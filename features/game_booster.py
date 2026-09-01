# -*- coding: utf-8 -*-
"""
features/game_booster.py — 부작용 없는 게임 부스터  [v2.1.0 신규]

의존: config.py, models.py, core/win32.py, core/scanner.py, core/actions.py (단방향)
      → UI를 전혀 알지 못한다. 결과는 DTO/딕셔너리로만 돌려준다.

=====================================================================
[왜 이 모듈을 새로 만들었나 — v2.0.x 게임 부스터의 실제 부작용]
=====================================================================
v2.0.x의 게임 부스터는 겉보기에 공격적이었지만, 실제로는 게임 경험을
나쁘게 만드는 동작이 세 가지 섞여 있었다.

  1) 게임 실행 중 주기적인 EmptyWorkingSet 호출
     → 게임이 방금 OS에 반납한 페이지를 곧바로 다시 읽어오게 되어
       하드 페이지 폴트가 폭증한다. 사용자 눈에는 "몇 초마다 한 번씩
       화면이 튀는" 스터터로 나타난다. 확보된 RAM 수치는 좋아 보이지만
       그 RAM은 게임이 다시 필요로 하던 것이었다.

  2) 프로세스 우선순위 격상 (High / Realtime)
     → 게임의 렌더 스레드가 오디오 스레드와 입력 스레드를 굶긴다.
       "프레임은 잘 나오는데 소리가 끊기고 마우스가 튄다"의 전형적 원인이다.
       특히 Realtime은 커널 스레드보다도 위라 시스템 전체가 멈출 수 있다.

  3) 2초 폴링
     → 감시 자체가 CPU를 계속 깨워 절전 상태 진입을 방해했다.

그래서 v2.1.0의 기본 동작은 "최대한 건드리지 않는 것"이다.

  ✔ 정리는 게임 시작 직전 딱 1회 (실행 중에는 절대 트림하지 않음)
  ✔ 게임 우선순위는 Normal 유지 (최대 Above Normal, 그 이상 불가)
  ✔ 폴링 주기 5초 이상
  ✔ 백그라운드 앱은 강제 종료가 아니라 NtSuspendProcess 로 일시 동결
  ✔ 하이브리드 CPU에서만 P-Core 바인딩 (동종 코어면 아무것도 하지 않음)

=====================================================================
[동결(freeze)에 대한 안전 장치]
=====================================================================
프로세스를 멈춘 채로 OptiCore가 죽어버리면 사용자는 "브라우저가 먹통"이
된 상태로 남는다. 이건 실제로 일어날 수 있는 최악의 시나리오라서 세 겹으로 막는다.
  1) 게임 종료 감지 시 자동 해동
  2) 세션 stop() 시 해동
  3) atexit 훅 — 인터프리터가 어떤 경로로 끝나든 남은 동결을 전부 해동
"""

import atexit
import os
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

import psutil

from config import IS_WINDOWS, PROTECTED_PROCESSES, write_log
from models import (
    DEFAULT_BACKGROUND_APPS, FrozenProcess, GameBoostOptions, GameBoostState,
)
from core.win32 import (
    MmcssTask, TimerResolution, describe_cpu_topology, empty_working_set,
    get_performance_core_ids, is_hybrid_cpu, resume_process, suspend_process,
)
from core.scanner import scan_ram_candidates

# =====================================================================
# 절대 동결하면 안 되는 프로세스
# =====================================================================
# 안티치트를 멈추면 게임이 즉시 강제 종료되거나 최악의 경우 밴 사유가 된다.
# 오디오/그래픽 드라이버 서비스를 멈추면 소리와 화면이 그대로 멈춘다.
# 이 목록은 config.PROTECTED_PROCESSES 에 "추가로" 적용되는 안전 장치다.
NEVER_SUSPEND = {
    # ---- 안티치트 ----
    "easyanticheat.exe", "easyanticheat_eos.exe", "eac_launcher.exe",
    "beservice.exe", "bedaisy.sys", "battleye.exe",
    "vgc.exe", "vgtray.exe", "vanguard.exe",          # Riot Vanguard
    "gamemon.des", "gamemon64.des", "npggnt.des",     # nProtect GameGuard
    "xhunter1.sys", "xigncode.exe",
    "faceitservice.exe", "faceitclient.exe",
    # ---- 오디오 ----
    "audiodg.exe", "rtkngui64.exe", "ravcpl64.exe", "nahimicservice.exe",
    "voicemeeter.exe", "equalizerapo.exe",
    # ---- 그래픽 드라이버 / 오버레이 ----
    "nvcontainer.exe", "nvdisplay.container.exe", "nvidia share.exe",
    "nvsphelper64.exe", "radeonsoftware.exe", "amddvr.exe", "atieclxx.exe",
    "igfxem.exe", "igfxext.exe", "igfxhk.exe",
    # ---- 입력 / 주변기기 ----
    "gamebarpresencewriter.exe", "logioverlay.exe", "lghub.exe",
    "icue.exe", "synapse3.exe", "razer synapse service.exe",
    # ---- 보안 ----
    "msmpeng.exe", "nissrv.exe", "securityhealthservice.exe",
    # ---- 개발/실행 환경 (자기 자신 보호) ----
    "opticore.exe", "opticore.py", "python.exe", "pythonw.exe",
}

# 프로그램이 죽어도 반드시 해동해야 하는 전역 목록 (atexit 안전망용)
_GLOBAL_FROZEN: List[FrozenProcess] = []


def _emergency_thaw_all():
    """[최후의 안전망] 인터프리터 종료 시 남아 있는 동결을 전부 해동한다."""
    if not _GLOBAL_FROZEN:
        return
    for item in list(_GLOBAL_FROZEN):
        try:
            resume_process(item.pid)
        except Exception:
            pass
    _GLOBAL_FROZEN.clear()


atexit.register(_emergency_thaw_all)


# =====================================================================
# 1. 우선순위 안정화
# =====================================================================
def stabilize_game_priority(pid: int, allow_above_normal: bool = False) -> Tuple[bool, str]:
    """
    게임 프로세스의 우선순위를 "안전한 범위"로 맞춘다.

    v2.0.x는 여기서 우선순위를 올리는 것을 부스트라고 불렀지만, 실제로는
    오디오/입력 스레드를 굶겨 체감을 나쁘게 만들었다. v2.1.0에서는
    기본적으로 Normal 로 "안정화"만 한다. 게임이 스스로 낮은 우선순위로
    떨어져 있는 경우(런처를 통해 실행되면 종종 발생)를 바로잡는 것이 목적이다.

    allow_above_normal=True 여도 ABOVE_NORMAL 을 넘지 않는다. HIGH/REALTIME 은
    코드 경로 자체가 없다.
    """
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    try:
        proc = psutil.Process(pid)
        target = (
            psutil.ABOVE_NORMAL_PRIORITY_CLASS if allow_above_normal
            else psutil.NORMAL_PRIORITY_CLASS
        )
        current = proc.nice()
        if current == target:
            return True, "이미 안정적인 우선순위입니다."
        proc.nice(target)
        label = "Above Normal" if allow_above_normal else "Normal"
        write_log(f"[게임부스터] 우선순위 안정화: PID {pid} → {label}")
        return True, f"우선순위를 {label} 로 안정화했습니다."
    except psutil.NoSuchProcess:
        return False, "프로세스를 찾을 수 없습니다."
    except psutil.AccessDenied:
        return False, "권한이 부족합니다 (관리자 권한으로 실행해보세요)."
    except Exception as e:
        return False, str(e)


# =====================================================================
# 2. 하이브리드 CPU P-Core 바인딩
# =====================================================================
def bind_to_performance_cores(pid: int) -> Tuple[bool, str, List[int]]:
    """
    게임 프로세스를 P-Core(성능 코어)에만 바인딩한다.

    12세대 인텔 이후 CPU는 P-Core와 E-Core가 섞여 있는데, 일부 게임과
    구형 안티치트는 이를 구분하지 못해 렌더 스레드가 E-Core로 밀린다.
    그러면 CPU 사용률은 낮은데 프레임이 안 나오는 상황이 생긴다.

    반환값의 세 번째 요소는 "원래 affinity"다. 게임 종료 시 이 값으로
    정확히 되돌리기 위해 반드시 보관해야 한다.

    ⚠️ 동종 코어 CPU에서는 아무것도 하지 않는다. 괜히 코어를 제한하면
       오히려 성능이 떨어지기 때문이다.
    """
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다.", []
    if not is_hybrid_cpu():
        return False, "하이브리드 CPU가 아니므로 P-Core 바인딩을 건너뜁니다.", []

    p_cores = get_performance_core_ids()
    if not p_cores:
        return False, "P-Core 목록을 확인할 수 없습니다.", []

    try:
        proc = psutil.Process(pid)
        original = list(proc.cpu_affinity())
        # 이미 P-Core 에만 묶여 있으면 건드리지 않는다.
        if set(original) == set(p_cores):
            return True, "이미 P-Core 에만 바인딩되어 있습니다.", original
        proc.cpu_affinity(p_cores)
        write_log(f"[게임부스터] P-Core 바인딩: PID {pid} → {p_cores} (원래 {original})")
        return True, f"P-Core {len(p_cores)}개에 바인딩했습니다: {p_cores}", original
    except psutil.NoSuchProcess:
        return False, "프로세스를 찾을 수 없습니다.", []
    except psutil.AccessDenied:
        return False, "권한이 부족합니다 (관리자 권한으로 실행해보세요).", []
    except Exception as e:
        return False, f"P-Core 바인딩 실패: {e}", []


def restore_affinity(pid: int, original: Sequence[int]) -> Tuple[bool, str]:
    """bind_to_performance_cores 로 바꾼 CPU affinity 를 원래대로 되돌린다."""
    if not original:
        return True, "되돌릴 affinity 기록이 없습니다."
    try:
        psutil.Process(pid).cpu_affinity(list(original))
        write_log(f"[게임부스터] CPU affinity 원복: PID {pid} → {list(original)}")
        return True, "CPU affinity 를 원래대로 복구했습니다."
    except psutil.NoSuchProcess:
        return True, "프로세스가 이미 종료되어 복구가 필요 없습니다."
    except Exception as e:
        return False, str(e)


# =====================================================================
# 3. 백그라운드 앱 일시 동결 / 해동
# =====================================================================
def _is_freezable(name: str, pid: int, protect_pids: set) -> bool:
    """이 프로세스를 동결해도 안전한지 판정한다 (보수적으로 판단)."""
    lower = (name or "").lower()
    if not lower:
        return False
    if pid in protect_pids or pid == os.getpid():
        return False
    if lower in PROTECTED_PROCESSES or lower in NEVER_SUSPEND:
        return False
    return True


def freeze_background_apps(target_names: Sequence[str],
                           protect_pids: Optional[set] = None) -> Tuple[List[FrozenProcess], List[str]]:
    """
    지정한 이름의 백그라운드 앱을 강제 종료하지 않고 일시 동결한다.

    브라우저처럼 프로세스가 여러 개로 쪼개진 앱(chrome.exe 가 탭마다 하나씩)도
    이름이 같으면 전부 동결된다. 이게 의도한 동작이다 — 일부만 멈추면
    부모/자식 프로세스가 서로를 기다리다 응답 없음 상태가 될 수 있다.

    반환: (동결된 목록, 건너뛴 사유 메시지 목록)
    """
    if not IS_WINDOWS:
        return [], ["Windows 전용 기능입니다."]

    wanted = {n.lower() for n in target_names if n}
    if not wanted:
        return [], ["동결 대상으로 지정된 앱이 없습니다."]

    protect_pids = protect_pids or set()
    frozen: List[FrozenProcess] = []
    notes: List[str] = []

    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            name = proc.info["name"] or ""
            pid = proc.info["pid"]
            if name.lower() not in wanted:
                continue
            if not _is_freezable(name, pid, protect_pids):
                notes.append(f"{name}: 보호 대상이라 건너뜀")
                continue
            ok, msg = suspend_process(pid)
            if ok:
                item = FrozenProcess(pid=pid, name=name)
                frozen.append(item)
                _GLOBAL_FROZEN.append(item)
            else:
                notes.append(f"{name}(PID {pid}): {msg}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            notes.append(f"동결 중 오류: {e}")

    if frozen:
        write_log(f"[게임부스터] 백그라운드 {len(frozen)}개 동결: "
                  + ", ".join(sorted({f.name for f in frozen})))
    return frozen, notes


def thaw_processes(frozen: Sequence[FrozenProcess]) -> Tuple[int, List[str]]:
    """동결해둔 프로세스를 모두 해동한다. 이미 종료된 것은 조용히 넘어간다."""
    resumed = 0
    notes: List[str] = []
    for item in list(frozen):
        try:
            if not psutil.pid_exists(item.pid):
                notes.append(f"{item.name}(PID {item.pid}): 이미 종료됨")
            else:
                ok, msg = resume_process(item.pid)
                if ok:
                    resumed += 1
                else:
                    notes.append(f"{item.name}(PID {item.pid}): {msg}")
        except Exception as e:
            notes.append(f"{item.name}: {e}")
        finally:
            # 성공/실패와 무관하게 전역 안전망 목록에서는 제거한다.
            if item in _GLOBAL_FROZEN:
                _GLOBAL_FROZEN.remove(item)
    if resumed:
        write_log(f"[게임부스터] 백그라운드 {resumed}개 해동 완료")
    return resumed, notes


# =====================================================================
# 4. 게임 시작 전 1회 정리
# =====================================================================
def pre_game_cleanup(excluded_set: Optional[set] = None, intensity: int = 2) -> int:
    """
    게임 시작 "직전"에 딱 한 번만 실행하는 메모리 정리.

    ⚠️ 이 함수는 감시 루프에서 절대 호출하면 안 된다. 게임이 이미 메모리를
       잡은 뒤에 트림하면 페이지 폴트로 스터터가 생긴다. 아직 게임이 메모리를
       요구하기 전인 "시작 직전"이기 때문에 안전한 것이다.
    """
    if not IS_WINDOWS:
        return 0
    trimmed = 0
    for pid, name, mem_mb in scan_ram_candidates(intensity, excluded_set):
        if empty_working_set(pid):
            trimmed += 1
    if trimmed:
        write_log(f"[게임부스터] 게임 시작 전 1회 정리: {trimmed}개 프로세스 트림")
    return trimmed


# =====================================================================
# 5. 부스트 세션
# =====================================================================
class GameBoostSession:
    """
    게임 한 판(감시 시작 ~ 종료)의 수명을 관리하는 객체.

    UI(main_window)는 QTimer 로 poll() 만 주기적으로 불러주면 되고,
    무엇을 적용하고 무엇을 되돌릴지는 전부 이 클래스가 기억한다.
    UI가 상태를 들고 있지 않으므로, 나중에 C#으로 옮길 때도 이 클래스만
    그대로 이식하면 된다.

    사용 흐름:
        session = GameBoostSession(options)
        state = session.start(pid, name, excluded_set)
        ...  # QTimer 로 5초마다
        result = session.poll()      # 게임이 끝났으면 dict, 아직이면 None
        ...
        session.stop()               # 사용자가 수동 중지한 경우
    """

    def __init__(self, options: Optional[GameBoostOptions] = None):
        self.options = options or GameBoostOptions()
        self.state = GameBoostState()
        self._timer = None   # TimerResolution
        self._mmcss = None   # MmcssTask

    # ---------------- 시작 ----------------
    def start(self, pid: int, name: str, excluded_set: Optional[set] = None) -> GameBoostState:
        self.state = GameBoostState(
            active=True, pid=pid, name=name,
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        notes = self.state.notes
        opt = self.options

        # ---- 1) 게임 시작 전 1회 정리 (실행 중에는 절대 반복하지 않음) ----
        if opt.pre_trim_once:
            self.state.pre_trim_count = pre_game_cleanup(excluded_set)
            notes.append(f"시작 전 1회 정리: {self.state.pre_trim_count}개 프로세스")

        # ---- 2) 우선순위 안정화 (Above Normal 이하) ----
        if opt.stabilize_priority:
            ok, msg = stabilize_game_priority(pid, opt.allow_above_normal)
            notes.append(f"우선순위: {msg}")

        # ---- 3) P-Core 바인딩 (하이브리드 CPU 한정) ----
        if opt.pcore_affinity:
            ok, msg, original = bind_to_performance_cores(pid)
            self.state.pcore_applied = ok and bool(original)
            self.state.original_affinity = original
            notes.append(f"P-Core: {msg}")

        # ---- 4) 백그라운드 앱 동결 ----
        if opt.suspend_background:
            targets = opt.background_apps or DEFAULT_BACKGROUND_APPS
            frozen, freeze_notes = freeze_background_apps(targets, protect_pids={pid})
            self.state.frozen = frozen
            if frozen:
                notes.append(f"동결: {len(frozen)}개 프로세스")
            notes.extend(freeze_notes[:5])

        # ---- 5) 고해상도 타이머 (with 대신 세션 수명에 맞춘 begin/end) ----
        if opt.timer_resolution:
            self._timer = TimerResolution(1)
            if self._timer.begin():
                self.state.timer_applied = True
                notes.append("1ms 고해상도 타이머 적용")

        # ---- 6) MMCSS 등록 ----
        # ⚠️ AvSetMmThreadCharacteristicsW 는 "호출한 스레드"에만 적용된다.
        #    즉 이걸로 게임이 빨라지지는 않는다. 여기서 등록하는 이유는,
        #    게임이 CPU를 꽉 채운 상황에서도 OptiCore의 감시 스레드가 밀리지 않아
        #    종료 감지와 백그라운드 해동이 제때 이뤄지도록 하기 위해서다.
        #    게임 자체에 적용되는 MMCSS 설정은 [성능 & 게이밍] 탭의
        #    'Tasks\\Games 프로필 주입'(set_games_task_profile) 쪽이다.
        if opt.mmcss_games:
            self._mmcss = MmcssTask("Games")
            if self._mmcss.begin():
                self.state.mmcss_applied = True
                notes.append("MMCSS 'Games' 등록 (감시 스레드)")

        write_log(f"[게임부스터] 세션 시작: {name} (PID {pid}) / " + " | ".join(notes))
        return self.state

    # ---------------- 감시 ----------------
    def is_game_running(self) -> bool:
        """감시 중인 게임이 아직 살아 있는지 확인한다.

        pid_exists 만 쓰면 PID가 재사용되었을 때 오판할 수 있어, 프로세스
        이름까지 함께 확인한다.
        """
        if not self.state.active or not self.state.pid:
            return False
        try:
            if not psutil.pid_exists(self.state.pid):
                return False
            proc = psutil.Process(self.state.pid)
            if self.state.name and proc.name() != self.state.name:
                return False  # PID 재사용 — 다른 프로그램이다
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            return True  # 접근이 막힌 것뿐이지 살아 있다
        except Exception:
            return False

    def poll(self) -> Optional[dict]:
        """
        감시 주기마다 호출한다. 게임이 끝났으면 정리 결과 dict 를, 아직
        실행 중이면 None 을 돌려준다.

        [v2.1.0] 이 함수 안에는 메모리 트림도, 우선순위 조작도 없다.
        게임이 도는 동안 OptiCore가 하는 일은 "살아 있는지 확인" 뿐이다.
        """
        if not self.state.active:
            return None
        if self.is_game_running():
            return None
        return self.stop(game_exited=True)

    # ---------------- 종료 / 원복 ----------------
    def stop(self, game_exited: bool = False) -> dict:
        """적용했던 모든 변경을 되돌린다 (부분 실패해도 나머지는 계속 진행)."""
        if not self.state.active:
            return {"active": False, "resumed": 0, "notes": []}

        notes: List[str] = []
        pid = self.state.pid
        name = self.state.name

        # ---- 1) 동결한 백그라운드 앱 해동 (가장 먼저 — 사용자 체감이 가장 큼) ----
        resumed, thaw_notes = thaw_processes(self.state.frozen)
        self.state.frozen = []
        notes.extend(thaw_notes[:5])

        # ---- 2) CPU affinity 원복 (게임이 아직 살아 있는 수동 중지 상황) ----
        if self.state.pcore_applied and pid and not game_exited:
            ok, msg = restore_affinity(pid, self.state.original_affinity)
            notes.append(f"affinity: {msg}")
        self.state.pcore_applied = False
        self.state.original_affinity = []

        # ---- 3) 우선순위 원복 ----
        if pid and not game_exited and self.options.stabilize_priority:
            try:
                psutil.Process(pid).nice(psutil.NORMAL_PRIORITY_CLASS)
            except Exception:
                pass

        # ---- 4) 타이머 / MMCSS 해제 ----
        if self._timer:
            self._timer.end()
            self._timer = None
        self.state.timer_applied = False
        if self._mmcss:
            self._mmcss.end()
            self._mmcss = None
        self.state.mmcss_applied = False

        self.state.active = False
        self.state.pid = None

        reason = "게임 종료 감지" if game_exited else "사용자 중지"
        write_log(f"[게임부스터] 세션 종료({reason}): {name} / 해동 {resumed}개")

        return {
            "active": False,
            "game_name": name,
            "game_exited": game_exited,
            "resumed": resumed,
            "notes": notes,
        }

    # ---------------- 정보 ----------------
    def describe(self) -> str:
        """현재 세션 상태를 사람이 읽는 한 줄 요약으로."""
        if not self.state.active:
            return "감시 중이 아닙니다."
        parts = [f"🟢 감시 중: {self.state.name} (PID {self.state.pid})"]
        if self.state.frozen:
            parts.append(f"동결 {len(self.state.frozen)}개")
        if self.state.pcore_applied:
            parts.append("P-Core 바인딩")
        if self.state.timer_applied:
            parts.append("1ms 타이머")
        return " · ".join(parts)


def get_cpu_topology_text() -> str:
    """설정 화면에서 P-Core 옵션 옆에 보여줄 CPU 구성 설명."""
    if not IS_WINDOWS:
        return "Windows 전용 기능입니다."
    return describe_cpu_topology()
