# -*- coding: utf-8 -*-
"""
features/tweaks.py — 성능 & 게이밍 튜닝 (대부분 관리자 권한 필요)

의존: config.py, models.py, core/actions.py, core/win32.py (단방향)

  - Multimedia SystemProfile 저지연 튜닝 (NetworkThrottlingIndex, SystemResponsiveness)
  - SystemProfile\\Tasks\\Games 작업 프로필 주입 (GPU Priority / Priority / Scheduling Category)
  - Nagle 알고리즘 해제 (TcpAckFrequency / TCPNoDelay)
  - BCD 타이머 설정 (disabledynamictick / useplatformtick)
  - 포그라운드 앱 우선 CPU 스케줄링 (Win32PrioritySeparation)
  - '최고의 성능(Ultimate Performance)' 전원 옵션 생성/적용
  - 시각 효과 최소화, Game DVR 비활성화
  - 위 작업들을 순차 실행하는 PerfTweakTask (QThreadPool 기반)

[v2.1.0 설계 원칙 — 왜 이 값들만 건드리는가]
  여기 있는 항목은 전부 Microsoft가 문서화한 레지스트리 값과 bcdedit 옵션이다.
  드라이버를 후킹하거나 커널 메모리를 직접 쓰는 "부스터"들과 달리,
  안티치트가 오탐할 여지가 없고 원클릭 순정 복원으로 전부 되돌릴 수 있다.
  값 자체도 게임 실행 여부와 무관하게 유지되는 정적 설정이라,
  게임 중 프로그램이 개입해 프레임을 흔드는 일이 없다.
"""

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from config import IS_WINDOWS, WINREG_AVAILABLE, winreg, write_log
from core.scanner import is_admin
from core.actions import _run_cli, _reg_set, set_nagle

# 레지스트리 경로 상수 (오타로 엉뚱한 키를 만드는 사고를 막기 위해 한 곳에 모음)
MULTIMEDIA_PROFILE_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
GAMES_TASK_PATH = MULTIMEDIA_PROFILE_PATH + r"\Tasks\Games"


# =====================================================================
# 1. Multimedia SystemProfile — 시스템 응답성 / 네트워크 쓰로틀링
# =====================================================================
def set_multimedia_system_profile(enable: bool):
    """
    NetworkThrottlingIndex / SystemResponsiveness 를 저지연 값으로 설정한다.

    - NetworkThrottlingIndex: Windows는 멀티미디어 재생 중 네트워크 수신을
      초당 약 10,000 패킷으로 제한한다. 0xFFFFFFFF 를 넣으면 이 제한이 꺼진다.
    - SystemResponsiveness: 백그라운드 작업에 예약해두는 CPU 비율(%)이다.
      기본 20(%)을 0으로 낮추면 포그라운드 게임이 그만큼 더 쓸 수 있다.

    복원값은 Windows 기본값인 10 / 20 이다.
    """
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."

    throttling = 0xFFFFFFFF if enable else 10
    responsiveness = 0 if enable else 20

    ok1, m1 = _reg_set(winreg.HKEY_LOCAL_MACHINE, MULTIMEDIA_PROFILE_PATH,
                       "NetworkThrottlingIndex", throttling, winreg.REG_DWORD)
    ok2, m2 = _reg_set(winreg.HKEY_LOCAL_MACHINE, MULTIMEDIA_PROFILE_PATH,
                       "SystemResponsiveness", responsiveness, winreg.REG_DWORD)
    ok = ok1 and ok2
    write_log(f"Multimedia SystemProfile {'저지연 적용' if enable else '기본값 복원'}: {ok}")
    if ok:
        return True, (
            "적용 완료 (NetworkThrottlingIndex=0xFFFFFFFF, SystemResponsiveness=0)"
            if enable else "Windows 기본값(10 / 20)으로 복원했습니다."
        )
    return False, " / ".join([m1, m2])


def set_network_gaming_priority(enable: bool):
    """[하위 호환 별칭] v2.0.x 부터 쓰이던 이름. 내부적으로는 위 함수와 같다.

    features/diagnostics.py 의 순정 복원과 기존 UI 가 이 이름을 참조하므로
    지우지 않고 위임(delegate)만 한다.
    """
    return set_multimedia_system_profile(enable)


# =====================================================================
# 2. SystemProfile\Tasks\Games — 게임 작업 프로필 주입
# =====================================================================
def set_games_task_profile(enable: bool):
    """
    MMCSS 가 "Games" 범주 스레드에 적용할 스케줄링 규칙을 조정한다.

    이 값들은 MMCSS 서비스가 읽어가는 공식 설정이며, 게임이
    AvSetMmThreadCharacteristicsW("Games") 로 등록한 스레드에만 영향을 준다.
    다른 프로그램이나 드라이버에는 아무 영향이 없다는 점이 핵심이다.

      GPU Priority        8  : GPU 명령 대기열에서의 우선순위 (기본 8, 최대 8)
      Priority            6  : MMCSS 내부 우선순위 (기본 2 → 6)
      Scheduling Category High : 스케줄링 범주 (Medium → High)
      SFIO Priority       High : 예약된 파일 I/O 우선순위
      Background Only     False: 백그라운드 전용 취급하지 않음
      Clock Rate          10000: 1ms 단위(10000 * 100ns) 스케줄링 주기
    """
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."

    if enable:
        values = [
            ("GPU Priority", 8, winreg.REG_DWORD),
            ("Priority", 6, winreg.REG_DWORD),
            ("Scheduling Category", "High", winreg.REG_SZ),
            ("SFIO Priority", "High", winreg.REG_SZ),
            ("Background Only", "False", winreg.REG_SZ),
            ("Clock Rate", 10000, winreg.REG_DWORD),
        ]
    else:
        # Windows 기본값으로 복원
        values = [
            ("GPU Priority", 8, winreg.REG_DWORD),
            ("Priority", 2, winreg.REG_DWORD),
            ("Scheduling Category", "Medium", winreg.REG_SZ),
            ("SFIO Priority", "Normal", winreg.REG_SZ),
            ("Background Only", "False", winreg.REG_SZ),
            ("Clock Rate", 10000, winreg.REG_DWORD),
        ]

    failures = []
    for name, value, vtype in values:
        ok, msg = _reg_set(winreg.HKEY_LOCAL_MACHINE, GAMES_TASK_PATH, name, value, vtype)
        if not ok:
            failures.append(f"{name}: {msg}")

    ok = not failures
    write_log(f"Tasks\\Games 프로필 {'주입' if enable else '기본값 복원'}: {ok}")
    if ok:
        return True, (
            "게임 작업 프로필을 주입했습니다 (GPU Priority 8 / Priority 6 / Scheduling Category High)."
            if enable else "게임 작업 프로필을 Windows 기본값으로 복원했습니다."
        )
    return False, "\n".join(failures)


# =====================================================================
# 3. Nagle 알고리즘 (저지연 네트워크)
# =====================================================================
def set_nagle_low_latency(disable: bool):
    """
    Nagle 알고리즘을 끈다 (TcpAckFrequency=1, TCPNoDelay=1).

    Nagle은 작은 TCP 패킷을 모아서 한 번에 보내 대역폭을 아끼는 기법이다.
    파일 전송에는 이득이지만, 조작 입력처럼 아주 작은 패킷을 계속 보내는
    게임에서는 최대 200ms의 지연으로 나타난다. 그래서 게이밍 환경에서는
    끄는 것이 일반적이다. (실제 구현은 core/actions.py 의 set_nagle 이 담당)

    ⚠️ 되돌릴 때는 값을 0으로 덮어쓰는 게 아니라 값 자체를 삭제해야
       Windows 기본 동작으로 정확히 돌아간다. set_nagle 이 그렇게 한다.
    """
    return set_nagle(disable)


# =====================================================================
# 4. BCD 타이머 설정
# =====================================================================
def set_bcd_timer_tweaks(enable: bool):
    """
    부팅 구성(BCD)의 타이머 옵션을 조정한다. 재부팅 후 적용된다.

      disabledynamictick=yes : 동적 틱(tickless) 비활성화 → 타이머 주기가
                               일정해져 프레임 페이싱의 지터가 줄어든다
      useplatformtick=yes    : 플랫폼 타이머(HPET 등)를 틱 소스로 사용

    ⚠️ 아주 드물게 특정 메인보드/BIOS 조합에서 부팅이 느려지거나 타이머가
       오히려 불안정해질 수 있다. 그래서 기본값은 꺼짐이며, 복원 시에는
       두 값을 /deletevalue 로 완전히 지워 순정 상태로 되돌린다.
    """
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."

    if enable:
        ok1, out1 = _run_cli(["bcdedit", "/set", "disabledynamictick", "yes"])
        ok2, out2 = _run_cli(["bcdedit", "/set", "useplatformtick", "yes"])
    else:
        ok1, out1 = _run_cli(["bcdedit", "/deletevalue", "disabledynamictick"])
        ok2, out2 = _run_cli(["bcdedit", "/deletevalue", "useplatformtick"])
        # 값이 원래 없었다면 bcdedit가 실패를 반환하는데, 이는 "이미 순정"이라는
        # 뜻이므로 실패로 취급하지 않는다.
        ok1 = ok1 or "찾을 수 없" in out1 or "not found" in out1.lower()
        ok2 = ok2 or "찾을 수 없" in out2 or "not found" in out2.lower()

    ok = ok1 and ok2
    write_log(f"BCD 타이머 설정 {'적용' if enable else '복원'}: {ok1}/{ok2}")
    if ok:
        return True, "설정을 반영했습니다. 재부팅 후 적용됩니다."
    return False, f"{out1}\n{out2}".strip()


def set_high_res_timer(enable: bool):
    """
    고해상도 타이머(useplatformclock). 관리자 권한 + 재부팅 필요.

    [v2.1.0 변경] 예전에는 이 함수가 disabledynamictick 까지 같이 건드려서
    새로 추가된 set_bcd_timer_tweaks 와 담당이 겹쳤다. 같은 값을 두 곳에서
    쓰면 복원 순서에 따라 설정이 어긋나므로, 이 함수는 useplatformclock 만
    책임지도록 분리했다.
    """
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."
    ok, out = _run_cli(["bcdedit", "/set", "useplatformclock", "false" if enable else "true"])
    write_log(f"고해상도 타이머(useplatformclock) {'적용' if enable else '복원'}: {out[:100]}")
    return ok, ("설정을 반영했습니다. 재부팅 후 적용됩니다." if ok else out)


# =====================================================================
# 5. CPU 스케줄링 / 전원 / 시각 효과 / Game DVR (기존 기능 유지)
# =====================================================================
def set_priority_separation(gaming: bool):
    """CPU 프로세서 스케줄링(Win32PrioritySeparation). 26=포그라운드 우선(게임), 2=Windows 기본값."""
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."
    value = 26 if gaming else 2
    ok, msg = _reg_set(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\PriorityControl",
        "Win32PrioritySeparation", value, winreg.REG_DWORD,
    )
    write_log(f"Win32PrioritySeparation={value} 적용: {ok}")
    return ok, msg


def create_ultimate_performance_plan():
    """'최고의 성능' 전원 옵션을 생성하고 활성화한다."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    dup_ok, dup_out = _run_cli(
        ["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"], timeout=15
    )
    if not dup_ok:
        write_log(f"Ultimate Performance 생성 실패: {dup_out[:200]}")
        return False, dup_out or "전원 옵션 생성에 실패했습니다."
    guid = None
    for token in dup_out.replace(":", " ").split():
        if len(token) == 36 and token.count("-") == 4:
            guid = token
            break
    if not guid:
        return False, "생성된 전원 옵션 GUID를 찾지 못했습니다."
    act_ok, act_out = _run_cli(["powercfg", "-setactive", guid], timeout=15)
    write_log(f"Ultimate Performance 전원 옵션 적용: {act_ok}")
    return act_ok, "최고의 성능 전원 옵션을 적용했습니다." if act_ok else act_out


def set_visual_effects_performance(enable_performance: bool):
    """시각 효과 최소화(성능 우선). 2=성능 우선, 1=모양 우선(기본값에 가까움)."""
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    value = 2 if enable_performance else 1
    ok, msg = _reg_set(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
        "VisualFXSetting", value, winreg.REG_DWORD,
    )
    write_log(f"시각 효과 설정(VisualFXSetting={value}) 적용: {ok}")
    return ok, msg


def set_game_dvr_disabled(disable: bool):
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    ok1, m1 = _reg_set(
        winreg.HKEY_CURRENT_USER, r"System\GameConfigStore",
        "GameDVR_Enabled", 0 if disable else 1, winreg.REG_DWORD,
    )
    ok2, m2 = _reg_set(
        winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR",
        "AllowGameDVR", 0 if disable else 1, winreg.REG_DWORD,
    ) if is_admin() else (True, "관리자 권한 없이 정책 값은 건너뜀(사용자 값만 적용)")
    ok = ok1
    write_log(f"Game DVR {'비활성화' if disable else '복원'}: {m1} / {m2}")
    return ok, f"{m1}\n{m2}"


# =====================================================================
# 6. 순차 적용 작업 (QThreadPool 기반)
# =====================================================================
class _PerfTweakSignals(QObject):
    """QRunnable은 QObject가 아니라 시그널을 가질 수 없어, 신호 전달용 객체를 따로 둔다."""
    progress_changed = pyqtSignal(int, str)
    finished_report = pyqtSignal(list)  # [(label, ok, msg), ...]


class PerfTweakTask(QRunnable):
    """
    성능 튜닝 항목을 순차 적용한다 (한 항목이 실패해도 나머지는 계속 진행).

    [v2.1.0 QThread → QThreadPool 전환]
      기존에는 버튼을 누를 때마다 QThread 인스턴스를 새로 만들었다. QThread는
      OS 스레드를 직접 잡기 때문에, 사용자가 버튼을 여러 번 누르면 그만큼
      스레드가 생기고 참조가 끊긴 스레드는 정리되지 않은 채 남았다.
      QThreadPool은 미리 만들어둔 워커를 재사용하므로 이 누수가 사라진다.

    호출부 호환을 위해 QThread 처럼 .start() 로 시작할 수 있게 해두었다.
    """

    def __init__(self, tasks: list, parent=None):
        super().__init__()
        # tasks: [(label, callable), ...]
        self.tasks = tasks
        self.signals = _PerfTweakSignals()
        # 기존 코드가 task.progress_changed.connect(...) 로 쓰던 형태 유지
        self.progress_changed = self.signals.progress_changed
        self.finished_report = self.signals.finished_report
        # 풀이 실행 직후 C++ 객체를 지우면 파이썬 쪽 참조가 무효가 되므로 끈다.
        self.setAutoDelete(False)

    def start(self):
        """QThread 와 같은 사용감을 위해 제공. 전역 스레드 풀에 제출한다."""
        QThreadPool.globalInstance().start(self)

    def run(self):
        results = []
        total = max(len(self.tasks), 1)
        for i, (label, func) in enumerate(self.tasks):
            self.signals.progress_changed.emit(int(i / total * 100), f"적용 중: {label}")
            try:
                ok, msg = func()
            except Exception as e:
                ok, msg = False, str(e)
            results.append((label, ok, msg))
        self.signals.finished_report.emit(results)


# [하위 호환] v2.0.x 에서 쓰던 이름. 기존 import 를 깨지 않기 위해 별칭으로 남긴다.
PerfTweakThread = PerfTweakTask
