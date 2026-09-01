# -*- coding: utf-8 -*-
"""
models.py — OptiCore 공용 데이터 모델(DTO) 계층  [v2.1.0 신규]

이 모듈은 config.py보다도 아래에 있는 "최하위" 모듈입니다.
표준 라이브러리 외에는 아무것도 import 하지 않으며, 프로젝트 내부의 어떤
모듈도 import 하지 않습니다. (순환 참조 원천 차단)

    models  ←  config  ←  themes / updater / core / features / ai / ui

[왜 DTO를 따로 빼는가 — C# 마이그레이션 대비]
  지금까지 프로세스 정보는 (pid, name, mem_mb) 같은 "익명 튜플"로 계층 사이를
  오갔습니다. 파이썬에서는 편하지만, 나중에 C#(.NET/WPF)으로 옮길 때는
  튜플이 그대로 대응되지 않아 호출부를 전부 다시 읽어야 합니다.
  @dataclass로 이름 있는 필드를 정의해두면 C#의 record/class와 1:1로
  대응되므로 이식 비용이 크게 줄어듭니다.

    Python : @dataclass class ProcessInfo: pid: int; name: str ...
    C#     : public record ProcessInfo(int Pid, string Name, ...);

[하위 호환 원칙 — 중요]
  기존 코드(core/scanner.py 등)는 여전히 튜플을 주고받습니다. 한 번에 전부
  바꾸면 회귀 버그가 생기므로, 각 DTO에 튜플 <-> DTO 변환 헬퍼
  (from_tuple / as_tuple)를 두어 "점진적 전환"이 가능하게 했습니다.
  새로 작성하는 코드는 DTO를, 기존 코드는 튜플을 그대로 쓰면 됩니다.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# =====================================================================
# 공통 베이스 — JSON 직렬화 헬퍼
# =====================================================================
class DtoMixin:
    """모든 DTO가 공유하는 직렬화 도우미.

    optimizer_settings.json 저장이나 로그 기록에 그대로 쓸 수 있도록
    dict 변환을 제공한다. (C#에서는 System.Text.Json 대응)
    """

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """알 수 없는 키는 조용히 무시한다.

        설정 파일이 구버전에서 넘어와 필드가 남거나 빠져 있어도
        프로그램이 죽지 않도록 하기 위함이다.
        """
        if not isinstance(data, dict):
            return cls()
        known = getattr(cls, "__dataclass_fields__", {})
        return cls(**{k: v for k, v in data.items() if k in known})


# =====================================================================
# 1. 프로세스 정보
# =====================================================================
@dataclass
class ProcessInfo(DtoMixin):
    """스캔/부스트 대상 프로세스 한 건.

    memory_mb : 물리 메모리 점유량(RSS, MB)
    cpu_percent : 논리 코어 수로 정규화된 CPU 사용률(%)
    """
    pid: int = 0
    name: str = ""
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    exe_path: str = ""

    # ---- 기존 튜플 코드와의 호환 ----
    @classmethod
    def from_ram_tuple(cls, item: Tuple[int, str, float]) -> "ProcessInfo":
        """core.scanner.scan_ram_candidates() 의 (pid, name, mem_mb) 튜플 변환."""
        pid, name, mem_mb = item
        return cls(pid=pid, name=name, memory_mb=float(mem_mb))

    @classmethod
    def from_cpu_tuple(cls, item: Tuple[int, str, float]) -> "ProcessInfo":
        """core.scanner.scan_cpu_candidates() 의 (pid, name, cpu_pct) 튜플 변환."""
        pid, name, cpu_pct = item
        return cls(pid=pid, name=name, cpu_percent=float(cpu_pct))

    def as_ram_tuple(self) -> Tuple[int, str, float]:
        return (self.pid, self.name, self.memory_mb)

    def as_cpu_tuple(self) -> Tuple[int, str, float]:
        return (self.pid, self.name, self.cpu_percent)

    def __str__(self) -> str:
        return f"{self.name} (PID {self.pid})"


# =====================================================================
# 2. 시스템 상태 스냅샷
# =====================================================================
@dataclass
class SystemStats(DtoMixin):
    """대시보드/OSD가 표시하는 한 시점의 시스템 상태."""
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: int = 0
    ram_total_mb: int = 0
    ram_available_mb: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def ram_used_gb(self) -> float:
        return round(self.ram_used_mb / 1024, 2)

    @property
    def ram_total_gb(self) -> float:
        return round(self.ram_total_mb / 1024, 2)


# =====================================================================
# 3. 튜닝 항목 프로필
# =====================================================================
@dataclass
class TweakProfile(DtoMixin):
    """성능 & 게이밍 탭의 튜닝 항목 하나를 설명하는 메타데이터.

    key             optimizer_settings.json 의 applied_tweaks 에 기록되는 식별자
    requires_admin  관리자 권한 필요 여부
    requires_reboot 재부팅 후에야 실제 반영되는지 여부
    reversible      '원클릭 순정 복원'으로 되돌릴 수 있는지 여부
    """
    key: str = ""
    label: str = ""
    description: str = ""
    requires_admin: bool = True
    requires_reboot: bool = False
    reversible: bool = True
    applied: bool = False


@dataclass
class TweakResult(DtoMixin):
    """튜닝 적용 결과 한 건. (label, ok, msg) 튜플과 호환."""
    label: str = ""
    ok: bool = False
    message: str = ""

    @classmethod
    def from_tuple(cls, item: Tuple[str, bool, str]) -> "TweakResult":
        label, ok, msg = item
        return cls(label=label, ok=bool(ok), message=msg or "")

    def as_tuple(self) -> Tuple[str, bool, str]:
        return (self.label, self.ok, self.message)


# =====================================================================
# 4. 게임 부스터 상태
# =====================================================================
@dataclass
class FrozenProcess(DtoMixin):
    """NtSuspendProcess로 일시 동결(freeze)해둔 백그라운드 프로세스.

    ⚠️ 이 목록은 반드시 게임 종료/프로그램 종료 시 해동(resume)되어야 한다.
       features/game_booster.py 가 atexit 훅으로 마지막 안전망을 건다.
    """
    pid: int = 0
    name: str = ""


@dataclass
class GameBoostOptions(DtoMixin):
    """게임 부스터 동작 방식 설정 (optimizer_settings["game_booster"] 에 저장).

    [v2.1.0 비침습 원칙]
      periodic_trim 이 없다는 점에 주목할 것. 게임 실행 중 주기적인
      EmptyWorkingSet 호출은 페이지 폴트를 유발해 프레임 드랍(스터터)을
      일으키므로 v2.1.0에서 완전히 제거되었다. 정리는 게임 시작 전 1회뿐이다.
    """
    poll_interval_sec: int = 5           # 감시 폴링 주기 (최소 5초)
    pre_trim_once: bool = True           # 게임 시작 직전 딱 1회만 RAM 정리
    stabilize_priority: bool = True      # 게임 우선순위를 Normal 로 안정화
    allow_above_normal: bool = False     # True 여도 Above Normal 을 넘지 않음
    pcore_affinity: bool = False         # 하이브리드 CPU P-Core 바인딩
    suspend_background: bool = False     # 백그라운드 앱 강제종료 대신 일시 동결
    mmcss_games: bool = True             # MMCSS "Games" 스레드 등록
    timer_resolution: bool = True        # 게임 중 1ms 타이머 유지
    background_apps: List[str] = field(default_factory=lambda: list(DEFAULT_BACKGROUND_APPS))


@dataclass
class GameBoostState(DtoMixin):
    """현재 진행 중인 게임 부스트 세션의 실시간 상태."""
    active: bool = False
    pid: Optional[int] = None
    name: str = ""
    started_at: str = ""
    frozen: List[FrozenProcess] = field(default_factory=list)
    deprioritized: List[FrozenProcess] = field(default_factory=list)
    original_affinity: List[int] = field(default_factory=list)
    pcore_applied: bool = False
    timer_applied: bool = False
    mmcss_applied: bool = False
    pre_trim_count: int = 0
    notes: List[str] = field(default_factory=list)


# 동결/양보 대상 기본 후보 (사용자가 설정에서 편집 가능)
# ※ 게임과 무관하고, 잠깐 멈춰도 데이터가 손상되지 않는 앱만 넣는다.
#    안티치트/드라이버/오디오/시스템 프로세스는 절대 포함하지 않는다.
DEFAULT_BACKGROUND_APPS: List[str] = [
    "chrome.exe", "msedge.exe", "firefox.exe", "whale.exe", "opera.exe",
    "Discord.exe", "Slack.exe", "Telegram.exe", "KakaoTalk.exe",
    "EpicGamesLauncher.exe", "Battle.net.exe", "Origin.exe", "upc.exe",
    "OneDrive.exe", "Dropbox.exe", "GoogleDriveFS.exe",
    "Spotify.exe", "Notion.exe", "Code.exe", "Teams.exe",
]


# =====================================================================
# 5. 창 닫기(X) 동작
# =====================================================================
class CloseAction:
    """X 버튼을 눌렀을 때의 동작 상수.

    optimizer_settings.json 의 "close_button_action" 값으로 저장된다.
    (C# 이식 시 enum CloseAction 으로 그대로 대응)
    """
    MINIMIZE_TASKBAR = "minimize_taskbar"   # 기본값: 작업 표시줄로 최소화
    MINIMIZE_TRAY = "minimize_tray"         # 시스템 트레이로 숨김
    EXIT = "exit"                           # 프로그램 완전 종료

    ALL = (MINIMIZE_TASKBAR, MINIMIZE_TRAY, EXIT)

    LABELS = {
        MINIMIZE_TASKBAR: "작업 표시줄로 최소화 (기본값)",
        MINIMIZE_TRAY: "시스템 트레이로 숨김",
        EXIT: "프로그램 완전 종료",
    }

    @classmethod
    def normalize(cls, value: str) -> str:
        """설정 파일에 이상한 값이 들어 있어도 기본값으로 안전하게 되돌린다."""
        return value if value in cls.ALL else cls.MINIMIZE_TASKBAR
