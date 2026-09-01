# -*- coding: utf-8 -*-
"""
core/win32.py — Win32 Native API 전담 래퍼  [v2.1.0 신규]

의존: config.py, models.py (단방향)
      → core/scanner.py, core/actions.py, features/* 가 이 모듈을 가져다 쓴다.

[이 모듈이 생긴 이유]
  v2.0.x까지는 시스템을 건드릴 때마다 subprocess로 powershell/cmd를 띄웠다.
  그 방식에는 세 가지 실질적인 문제가 있었다.
    1) 콘솔 창이 순간적으로 번쩍인다 (게임 중이면 포커스를 뺏기기도 한다)
    2) 프로세스 생성 비용 때문에 버튼을 눌러도 수백 ms씩 반응이 늦다
    3) 한글 Windows(CP949)에서 출력 인코딩이 깨져 결과 파싱이 불안정하다
  ctypes.windll 로 C API를 직접 부르면 위 셋이 모두 사라진다.

[안전 원칙]
  - Windows가 아니거나 DLL 로드에 실패하면 예외를 던지지 않고 조용히
    "사용 불가" 상태가 된다. 호출부는 (성공여부, 메시지) 튜플만 확인하면 된다.
  - 핸들은 반드시 닫는다. 컨텍스트 매니저(RAII)를 제공하는 기능은
    with 블록을 벗어나는 순간 — 예외가 나더라도 — 자원을 반납한다.
  - 그래픽 드라이버 / 오디오 / 안티치트 스레드는 절대 건드리지 않는다.
    여기 있는 것은 전부 Microsoft가 공식 문서화한 API뿐이다.
"""

import atexit
import ctypes
import os
import threading
from ctypes import wintypes
from typing import List, Optional, Tuple

from config import IS_WINDOWS, write_log


# =====================================================================
# 0. DLL 로드 (실패해도 프로그램은 계속 동작한다)
# =====================================================================
kernel32 = None
user32 = None
ntdll = None
psapi = None
winmm = None
avrt = None

WIN32_AVAILABLE = False
MMCSS_AVAILABLE = False

if IS_WINDOWS:
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        winmm = ctypes.WinDLL("winmm", use_last_error=True)
        WIN32_AVAILABLE = True
    except Exception as e:  # pragma: no cover - 환경 의존
        write_log(f"[win32] 기본 DLL 로드 실패: {e}")
        WIN32_AVAILABLE = False

    # avrt.dll(MMCSS)은 일부 Windows 에디션(Server Core 등)에 없을 수 있다.
    try:
        avrt = ctypes.WinDLL("avrt", use_last_error=True)
        MMCSS_AVAILABLE = True
    except Exception:
        avrt = None
        MMCSS_AVAILABLE = False


# =====================================================================
# 1. 상수
# =====================================================================
# OpenProcess 접근 권한
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_SET_QUOTA = 0x0100
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_SET_INFORMATION = 0x0200

# ShowWindow
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9

# SetWindowPos
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

# GetLastError
ERROR_ALREADY_EXISTS = 183

# 단일 인스턴스 식별용 뮤텍스 이름 (요청서 지정 값)
SINGLE_INSTANCE_MUTEX_NAME = "OptiCore_SingleInstance_Mutex"


# =====================================================================
# 2. 함수 시그니처 선언
# =====================================================================
def _declare_signatures():
    """ctypes 기본값(int 반환)에 맡기면 64비트에서 핸들이 잘리므로 명시한다."""
    if not WIN32_AVAILABLE:
        return
    try:
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel32.ReleaseMutex.restype = wintypes.BOOL

        psapi.EmptyWorkingSet.argtypes = [wintypes.HANDLE]
        psapi.EmptyWorkingSet.restype = wintypes.BOOL

        ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtSuspendProcess.restype = ctypes.c_long  # NTSTATUS
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = ctypes.c_long

        winmm.timeBeginPeriod.argtypes = [wintypes.UINT]
        winmm.timeBeginPeriod.restype = wintypes.UINT
        winmm.timeEndPeriod.argtypes = [wintypes.UINT]
        winmm.timeEndPeriod.restype = wintypes.UINT

        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.BringWindowToTop.argtypes = [wintypes.HWND]
        user32.BringWindowToTop.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
        user32.AttachThreadInput.restype = wintypes.BOOL
        user32.SetWindowPos.argtypes = [
            wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL

        if MMCSS_AVAILABLE:
            avrt.AvSetMmThreadCharacteristicsW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
            avrt.AvSetMmThreadCharacteristicsW.restype = wintypes.HANDLE
            avrt.AvRevertMmThreadCharacteristics.argtypes = [wintypes.HANDLE]
            avrt.AvRevertMmThreadCharacteristics.restype = wintypes.BOOL
    except Exception as e:  # pragma: no cover
        write_log(f"[win32] 함수 시그니처 선언 실패: {e}")


_declare_signatures()


# =====================================================================
# 3. 고해상도 시스템 타이머 (RAII 컨텍스트 매니저)
# =====================================================================
class TimerResolution:
    """
    timeBeginPeriod / timeEndPeriod 를 짝이 맞게 보장하는 RAII 래퍼.

    Windows의 기본 타이머 주기는 약 15.6ms다. 이를 1ms로 낮추면 Sleep()이나
    이벤트 대기의 정밀도가 올라가 입력~렌더 사이의 지터가 줄어든다.
    문제는 timeBeginPeriod를 부른 뒤 timeEndPeriod를 빠뜨리면 그 설정이
    "프로세스가 죽을 때까지" 시스템 전역에 남아 전력 소모가 늘어난다는 점이다.

    그래서 세 겹으로 해제를 보장한다.
        1) with 블록 — 예외가 나도 __exit__ 가 반드시 호출된다
        2) 참조 카운트 — 여러 곳에서 중첩해 켜도 마지막 하나가 꺼질 때만 해제
        3) atexit 훅 — 인터프리터가 어떤 경로로 끝나든 남은 카운트를 정리

    사용법 (둘 다 지원):
        with TimerResolution(1):
            ...                      # 블록을 벗어나면 자동 해제

        tr = TimerResolution(1); tr.begin()
        ...
        tr.end()                     # 게임 세션처럼 수명이 긴 경우
    """

    _lock = threading.RLock()
    _refcount = 0
    _active_period = None

    def __init__(self, period_ms: int = 1, enabled: bool = True):
        self.period_ms = max(1, int(period_ms))
        self.enabled = bool(enabled)
        self._entered = False

    # ---- 명시적 제어 ----
    def begin(self) -> bool:
        if not self.enabled or not WIN32_AVAILABLE or self._entered:
            return False
        with TimerResolution._lock:
            try:
                # TIMERR_NOERROR == 0
                if winmm.timeBeginPeriod(self.period_ms) != 0:
                    write_log(f"[win32] timeBeginPeriod({self.period_ms}) 거부됨")
                    return False
            except Exception as e:
                write_log(f"[win32] timeBeginPeriod 실패: {e}")
                return False
            TimerResolution._refcount += 1
            TimerResolution._active_period = self.period_ms
            self._entered = True
            return True

    def end(self) -> bool:
        if not self._entered:
            return False
        with TimerResolution._lock:
            self._entered = False
            try:
                winmm.timeEndPeriod(self.period_ms)
            except Exception:
                pass
            TimerResolution._refcount = max(0, TimerResolution._refcount - 1)
            if TimerResolution._refcount == 0:
                TimerResolution._active_period = None
            return True

    # ---- with 문 지원 ----
    def __enter__(self) -> "TimerResolution":
        self.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.end()
        return False  # 예외는 그대로 위로 전달한다

    @classmethod
    def is_active(cls) -> bool:
        return cls._refcount > 0

    @classmethod
    def _release_all_on_exit(cls):
        """최후의 안전망: 남아 있는 참조를 전부 되돌린다."""
        with cls._lock:
            period = cls._active_period or 1
            while cls._refcount > 0:
                try:
                    winmm.timeEndPeriod(period)
                except Exception:
                    break
                cls._refcount -= 1
            cls._active_period = None


if WIN32_AVAILABLE:
    atexit.register(TimerResolution._release_all_on_exit)


# =====================================================================
# 4. MMCSS (Multimedia Class Scheduler Service) 등록
# =====================================================================
class MmcssTask:
    """
    현재 스레드를 MMCSS 의 특정 작업 범주("Games")로 등록하는 RAII 래퍼.

    MMCSS는 Windows가 멀티미디어/게임 스레드에 CPU 시간을 우선 배분하도록
    설계한 공식 서비스다. 프로세스 우선순위를 Realtime으로 올리는 것과 달리
    오디오·입력 스레드를 굶기지 않으면서 지연만 줄여주기 때문에,
    v2.1.0의 "부작용 없는 튜닝" 원칙에 정확히 부합한다.

    ⚠️ MMCSS 등록은 "스레드 단위"다. 등록한 그 스레드에서만 효과가 있으므로,
       실제 작업을 수행하는 워커 스레드 안에서 with 블록을 열어야 한다.
    """

    def __init__(self, task_name: str = "Games", enabled: bool = True):
        self.task_name = task_name
        self.enabled = bool(enabled)
        self.handle = None
        self.task_index = 0

    def begin(self) -> bool:
        if not self.enabled or not MMCSS_AVAILABLE:
            return False
        try:
            task_index = wintypes.DWORD(0)
            handle = avrt.AvSetMmThreadCharacteristicsW(self.task_name, ctypes.byref(task_index))
            # 실패 시 NULL 반환
            if not handle:
                return False
            self.handle = handle
            self.task_index = task_index.value
            return True
        except Exception as e:
            write_log(f"[win32] MMCSS 등록 실패: {e}")
            return False

    def end(self) -> bool:
        if not self.handle:
            return False
        try:
            avrt.AvRevertMmThreadCharacteristics(self.handle)
        except Exception:
            pass
        self.handle = None
        return True

    def __enter__(self) -> "MmcssTask":
        self.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.end()
        return False


def register_mmcss_games(enabled: bool = True) -> Tuple[bool, str]:
    """현재 스레드를 MMCSS "Games" 범주로 등록만 하고 핸들을 돌려준다(진단용)."""
    if not MMCSS_AVAILABLE:
        return False, "이 시스템에서는 MMCSS(avrt.dll)를 사용할 수 없습니다."
    task = MmcssTask("Games", enabled=enabled)
    if task.begin():
        return True, f"MMCSS 'Games' 등록 완료 (task index {task.task_index})"
    return False, "MMCSS 등록에 실패했습니다."


# =====================================================================
# 5. 프로세스 핸들 헬퍼
# =====================================================================
class ProcessHandle:
    """OpenProcess 핸들을 with 블록으로 안전하게 다루는 래퍼.

    핸들 누수는 눈에 잘 안 띄는 대신 오래 켜둘수록 확실히 쌓이는 종류의
    버그라서, 직접 OpenProcess/CloseHandle 을 부르지 말고 항상 이걸 쓴다.
    """

    def __init__(self, pid: int, access: int):
        self.pid = int(pid)
        self.access = access
        self.handle = None

    def __enter__(self):
        if WIN32_AVAILABLE:
            try:
                handle = kernel32.OpenProcess(self.access, False, self.pid)
                self.handle = handle if handle else None
            except Exception:
                self.handle = None
        return self.handle

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self.handle:
            try:
                kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None
        return False


def empty_working_set(pid: int) -> bool:
    """프로세스의 워킹셋을 비운다 (종료하지 않음).

    ⚠️ [v2.1.0 중요] 이 함수 자체는 안전하지만, 게임이 실행 중일 때
       주기적으로 호출하면 게임이 방금 반납한 페이지를 다시 읽어오느라
       하드 페이지 폴트가 폭증해 스터터(프레임 끊김)가 생긴다.
       그래서 v2.1.0부터 게임 감시 루프에서는 절대 호출하지 않고,
       게임 시작 직전 수동 1회만 허용한다.
    """
    if not WIN32_AVAILABLE:
        return False
    with ProcessHandle(pid, PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA) as handle:
        if not handle:
            return False
        try:
            return bool(psapi.EmptyWorkingSet(handle))
        except Exception:
            return False


# =====================================================================
# 6. 프로세스 동결 / 재개 (NtSuspendProcess / NtResumeProcess)
# =====================================================================
def suspend_process(pid: int) -> Tuple[bool, str]:
    """
    프로세스를 "종료하지 않고" 완전히 멈춘다.

    게임을 켤 때 브라우저나 런처를 강제 종료해버리면 사용자가 보던 탭과
    로그인 세션이 날아간다. NtSuspendProcess는 모든 스레드를 정지시킬 뿐이라
    CPU 점유율이 0이 되면서도 메모리 상태는 그대로 보존된다.
    게임이 끝나면 NtResumeProcess로 아무 일도 없었다는 듯 되돌아온다.

    ⚠️ 안전 규칙 (호출부에서 반드시 지킬 것)
       - 시스템/드라이버/안티치트/오디오 프로세스는 절대 대상에 넣지 않는다.
       - 동결한 목록은 반드시 어딘가에 보관하고 종료 시 해동해야 한다.
         (features/game_booster.py 가 atexit 안전망을 건다)
    """
    if not WIN32_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if pid == os.getpid():
        return False, "자기 자신은 동결할 수 없습니다."
    with ProcessHandle(pid, PROCESS_SUSPEND_RESUME) as handle:
        if not handle:
            return False, "프로세스 핸들을 열 수 없습니다 (권한 부족 또는 이미 종료됨)."
        try:
            status = ntdll.NtSuspendProcess(handle)
        except Exception as e:
            return False, f"NtSuspendProcess 호출 실패: {e}"
        if status == 0:
            return True, "동결 완료"
        return False, f"동결 실패 (NTSTATUS 0x{status & 0xFFFFFFFF:08X})"


def resume_process(pid: int) -> Tuple[bool, str]:
    """suspend_process 로 멈춘 프로세스를 다시 실행 상태로 되돌린다."""
    if not WIN32_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    with ProcessHandle(pid, PROCESS_SUSPEND_RESUME) as handle:
        if not handle:
            return False, "프로세스 핸들을 열 수 없습니다 (이미 종료되었을 수 있습니다)."
        try:
            status = ntdll.NtResumeProcess(handle)
        except Exception as e:
            return False, f"NtResumeProcess 호출 실패: {e}"
        if status == 0:
            return True, "재개 완료"
        return False, f"재개 실패 (NTSTATUS 0x{status & 0xFFFFFFFF:08X})"


# =====================================================================
# 7. 단일 인스턴스 뮤텍스 + 기존 창 복원
# =====================================================================
class SingleInstanceMutex:
    """
    Named Mutex 로 "이미 실행 중인지"를 판정한다.

    파일 잠금이나 포트 바인딩과 달리, 커널 오브젝트인 뮤텍스는 프로세스가
    비정상 종료(강제 종료/블루스크린)해도 OS가 알아서 정리해준다.
    잠금 파일 방식에서 흔한 "죽은 뒤에도 실행 중이라고 우기는" 문제가 없다.
    """

    def __init__(self, name: str = SINGLE_INSTANCE_MUTEX_NAME):
        self.name = name
        self.handle = None
        self.already_running = False

    def acquire(self) -> bool:
        """소유권 획득을 시도한다. 이미 다른 인스턴스가 있으면 False."""
        if not WIN32_AVAILABLE:
            return True  # 비 Windows 환경에서는 중복 실행 방지를 적용하지 않는다
        try:
            handle = kernel32.CreateMutexW(None, True, self.name)
            last_error = ctypes.get_last_error()
        except Exception as e:
            write_log(f"[win32] CreateMutexW 실패: {e}")
            return True  # 판정 불가 시에는 실행을 막지 않는다 (사용성 우선)

        if not handle:
            return True

        self.handle = handle
        self.already_running = (last_error == ERROR_ALREADY_EXISTS)
        if not self.already_running:
            atexit.register(self.release)
        return not self.already_running

    def release(self):
        if not self.handle:
            return
        try:
            if not self.already_running:
                kernel32.ReleaseMutex(self.handle)
            kernel32.CloseHandle(self.handle)
        except Exception:
            pass
        self.handle = None


def find_window_by_title(exact_title: str = None, title_prefix: str = None) -> Optional[int]:
    """
    창 핸들(HWND)을 찾는다.

    - exact_title: FindWindowW 로 정확히 일치하는 제목을 찾는다(가장 빠름)
    - title_prefix: 제목이 접두사로 시작하는 최상위 창을 EnumWindows로 찾는다
      (OptiCore 창 제목에는 버전이 들어 있어 정확 일치가 어려우므로 이쪽을 쓴다)
    """
    if not WIN32_AVAILABLE:
        return None

    if exact_title:
        try:
            hwnd = user32.FindWindowW(None, exact_title)
            if hwnd:
                return hwnd
        except Exception:
            pass

    if not title_prefix:
        return None

    found = []
    my_pid = os.getpid()

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _callback(hwnd, _lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == my_pid:
                return True  # 자기 자신의 창은 제외
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value.startswith(title_prefix):
                found.append(hwnd)
                return False  # 첫 번째를 찾으면 열거 중단
        except Exception:
            pass
        return True

    try:
        user32.EnumWindows(WNDENUMPROC(_callback), 0)
    except Exception:
        pass
    return found[0] if found else None


def force_foreground_window(hwnd: int) -> bool:
    """
    창을 복원(Restore)하고 화면 최상단으로 끌어올린다.

    Windows는 "포그라운드 가로채기"를 막기 위해 다른 프로세스가
    SetForegroundWindow 를 부르는 것을 대부분 무시한다. 그래서 문서화된
    우회 절차를 순서대로 시도한다.
        1) 최소화 상태면 SW_RESTORE 로 복원
        2) 현재 포그라운드 창의 스레드에 입력을 붙여(AttachThreadInput)
           같은 입력 큐 안에서 SetForegroundWindow 호출 → 차단 회피
        3) 그래도 안 되면 TOPMOST 로 한 번 올렸다가 즉시 되돌려 시선을 끈다
    """
    if not WIN32_AVAILABLE or not hwnd:
        return False
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)

        fg_hwnd = user32.GetForegroundWindow()
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0

        attached = False
        if fg_thread and target_thread and fg_thread != target_thread:
            attached = bool(user32.AttachThreadInput(fg_thread, target_thread, True))

        ok = bool(user32.SetForegroundWindow(hwnd))
        user32.BringWindowToTop(hwnd)

        if attached:
            user32.AttachThreadInput(fg_thread, target_thread, False)

        if not ok:
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            ok = True
        return ok
    except Exception as e:
        write_log(f"[win32] 창 포그라운드 복원 실패: {e}")
        return False


def restore_existing_instance(title_prefix: str) -> bool:
    """이미 떠 있는 OptiCore 창을 찾아 화면 앞으로 복원한다."""
    hwnd = find_window_by_title(title_prefix=title_prefix)
    if not hwnd:
        return False
    return force_foreground_window(hwnd)


# =====================================================================
# 8. 하이브리드 CPU P-Core 탐지 (GetSystemCpuSetInformation)
# =====================================================================
# 12세대 인텔(Alder Lake) 이후 CPU는 성능 코어(P-Core)와 효율 코어(E-Core)가
# 섞여 있다. 일부 구형 게임/안티치트는 두 코어를 구분하지 못해 게임 스레드가
# E-Core로 밀려 프레임이 떨어지는 일이 있다.
#
# 어느 코어가 P-Core인지는 추측하지 않는다. Windows가 알려주는
# GetSystemCpuSetInformation 의 EfficiencyClass 값을 그대로 읽어서,
# 가장 높은 등급을 가진 논리 프로세서만 P-Core로 판정한다.
# (값이 클수록 고성능. 동종 코어만 있는 CPU는 전부 같은 값이 나온다.)
_CPU_SET_RECORD_MIN_SIZE = 20
_CPU_SET_INFORMATION_TYPE = 0  # CpuSetInformation


def get_cpu_set_info() -> List[dict]:
    """논리 프로세서별 (index, core_index, efficiency_class) 목록을 돌려준다."""
    if not WIN32_AVAILABLE:
        return []
    fn = getattr(kernel32, "GetSystemCpuSetInformation", None)
    if fn is None:
        return []  # Windows 10 미만
    try:
        fn.argtypes = [
            ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG),
            wintypes.HANDLE, wintypes.ULONG,
        ]
        fn.restype = wintypes.BOOL

        needed = wintypes.ULONG(0)
        fn(None, 0, ctypes.byref(needed), None, 0)
        size = needed.value
        if size == 0:
            return []

        buf = ctypes.create_string_buffer(size)
        if not fn(buf, size, ctypes.byref(needed), None, 0):
            return []

        raw = buf.raw[:needed.value]
        results = []
        offset = 0
        while offset + _CPU_SET_RECORD_MIN_SIZE <= len(raw):
            rec_size = int.from_bytes(raw[offset:offset + 4], "little")
            rec_type = int.from_bytes(raw[offset + 4:offset + 8], "little")
            if rec_size <= 0 or offset + rec_size > len(raw):
                break
            if rec_type == _CPU_SET_INFORMATION_TYPE:
                # 구조체 오프셋: Id(8) Group(12) LogicalProcessorIndex(14)
                #                CoreIndex(15) LastLevelCacheIndex(16)
                #                NumaNodeIndex(17) EfficiencyClass(18)
                results.append({
                    "logical_index": raw[offset + 14],
                    "core_index": raw[offset + 15],
                    "efficiency_class": raw[offset + 18],
                    "group": int.from_bytes(raw[offset + 12:offset + 14], "little"),
                })
            offset += rec_size
        return results
    except Exception as e:
        write_log(f"[win32] CPU Set 정보 조회 실패: {e}")
        return []


def is_hybrid_cpu() -> bool:
    """P-Core / E-Core 가 섞인 하이브리드 CPU인지 판정한다."""
    info = get_cpu_set_info()
    if not info:
        return False
    return len({item["efficiency_class"] for item in info}) > 1


def get_performance_core_ids() -> List[int]:
    """
    P-Core(성능 코어)에 해당하는 논리 프로세서 번호 목록.

    - 하이브리드가 아니면 빈 리스트를 돌려준다 (바인딩할 이유가 없으므로).
    - psutil.Process().cpu_affinity(list) 에 그대로 넘길 수 있는 형식이다.
    """
    info = get_cpu_set_info()
    if not info:
        return []
    classes = {item["efficiency_class"] for item in info}
    if len(classes) <= 1:
        return []
    best = max(classes)
    ids = sorted({item["logical_index"] for item in info if item["efficiency_class"] == best})
    return ids


def describe_cpu_topology() -> str:
    """설정 화면에 보여줄 CPU 구성 요약 문자열."""
    info = get_cpu_set_info()
    if not info:
        return "CPU 코어 구성을 조회할 수 없습니다 (Windows 10 미만이거나 조회 실패)."
    classes = sorted({item["efficiency_class"] for item in info}, reverse=True)
    if len(classes) <= 1:
        return f"동종 코어 CPU (논리 프로세서 {len(info)}개) — P-Core 바인딩이 필요하지 않습니다."
    p_cores = get_performance_core_ids()
    e_count = len(info) - len(p_cores)
    return (
        f"하이브리드 CPU 감지 — 논리 프로세서 {len(info)}개 "
        f"(P-Core {len(p_cores)}개 / E-Core {e_count}개)\n"
        f"P-Core 번호: {p_cores}"
    )
