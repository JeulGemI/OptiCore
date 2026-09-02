# -*- coding: utf-8 -*-
"""
config.py — OptiCore 전역 설정 계층 (최하위 모듈)

이 모듈은 OptiCore 안에서 "가장 아래"에 있습니다.
즉, 이 파일은 프로젝트 내부의 다른 어떤 모듈도 import 하지 않습니다.
(단방향 import 구조 유지 → 순환 참조 방지)

담당 범위
  - 프로그램 이름/버전 상수, GitHub 저장소 상수
  - 선택적 의존성(send2trash / pynvml / winreg) 로드 및 가용 플래그
  - 설정 파일(optimizer_settings.json) 원자적(Atomic) 로드/저장
  - 로그 파일(optimizer_log.txt) 기록 + 자동 로테이션(5MB x 백업 2개)
  - 리소스 경로 헬퍼 resource_path() — PyInstaller(sys._MEIPASS) 대응
  - 진입점(OptiCore.py) 정보 등록 — 헤더 주석/자기 자신 경로를 다른 모듈이 쓸 수 있게 함

[Git 보안 안내 — .gitignore 설정 가이드]
  아래 두 파일은 **절대 GitHub에 커밋하지 마세요.**
    optimizer_settings.json   ← Gemini API 키가 평문으로 저장됩니다
    optimizer_log.txt         ← PC의 프로세스/경로 등 개인 정보가 남습니다
  저장소 루트에 .gitignore 파일을 만들고 아래 내용을 넣어두세요:

      # OptiCore 로컬 전용 파일 (커밋 금지)
      optimizer_settings.json
      optimizer_log.txt
      *.bak
      *.new
      __pycache__/
      build/
      dist/
      *.spec

  이미 실수로 커밋한 적이 있다면 파일을 지우는 것만으로는 부족합니다.
  (git 히스토리에 남아 있으므로) 반드시 해당 API 키를 Google AI Studio에서
  폐기(revoke)하고 새 키를 발급받으세요.
"""

import os
import sys
import json
import logging
import platform
import tempfile
import threading
from logging.handlers import RotatingFileHandler

import psutil

# =====================================================================
# 프로그램 식별 상수
# =====================================================================
# [v1.0.2] 파일명에 버전을 박아두면(OptiCore_V1.0.py 등) 버전이 오를 때마다
# 파일명을 바꿔야 하고, import/문서 참조가 깨지기 쉽습니다.
# 그래서 실제 진입점 파일명은 "OptiCore.py"로 고정하고, 버전은 아래 상수 +
# 창 제목 + OptiCore.py 최상단 주석의 [변경 이력]에서만 관리합니다.
# (다른 Claude 계정/세션에서 이어받아 작업할 때도 이 상수를 갱신 기준으로 삼으세요.)
APP_NAME = "OptiCore"
APP_VERSION = "2.1.1"

# =====================================================================
# 자동 업데이트용 GitHub 저장소 정보 (공개 저장소 / 토큰 불필요)
# =====================================================================
# releases에 "OptiCore.py"(소스 실행용) 또는 "OptiCore.exe"(빌드본) 에셋을
# 올려두면 updater.py가 해당 파일을 찾아 내려받습니다.
GITHUB_OWNER = "JeulGemI"
GITHUB_REPO = "OptiCore"
GITHUB_API_LATEST_RELEASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# 창/트레이 아이콘 파일명 (없으면 시스템 기본 아이콘으로 대체됨)
ICON_FILENAME = "icon.ico"

# [v2.1.0] 중복 실행 감지 시 "이미 떠 있는 창"을 찾기 위한 제목 접두사.
#   창 제목에는 버전(v2.1.0)이 들어가므로 정확히 일치시키기 어렵다. 그래서
#   버전이 바뀌어도 깨지지 않도록 접두사만 맞춰 EnumWindows 로 찾는다.
#   ui/main_window.py 의 setWindowTitle() 도 반드시 이 접두사로 시작해야 한다.
WINDOW_TITLE_PREFIX = f"{APP_NAME} v"


# =====================================================================
# 선택적 의존성 (없어도 프로그램은 동작하되 해당 기능만 비활성화)
# =====================================================================
# ※ 아래 send2trash / pynvml / winreg 는 이 파일 안에서는 직접 쓰이지 않지만
#   일부러 여기에 모아둔 "재수출(re-export)"이다. core/features 계층이
#   try/except ImportError 를 각자 반복하지 않고
#   `from config import send2trash, SEND2TRASH_AVAILABLE` 처럼 한 곳에서
#   가져다 쓰게 하기 위함이다. 사용하지 않는 import처럼 보여도 지우지 말 것.
try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    send2trash = None
    SEND2TRASH_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    pynvml = None
    NVML_AVAILABLE = False

IS_WINDOWS = platform.system() == "Windows"

# winreg는 Windows 전용 표준 모듈. 다른 OS에서는 None으로 두고,
# 사용하는 쪽에서 항상 WINREG_AVAILABLE를 먼저 확인한다.
winreg = None
WINREG_AVAILABLE = False
if IS_WINDOWS:
    try:
        import winreg as _winreg_module
        winreg = _winreg_module
        WINREG_AVAILABLE = True
    except ImportError:
        winreg = None
        WINREG_AVAILABLE = False

# 확장 기능(블로트웨어/시작프로그램/성능튜닝/진단복원/디스크정리+)은 기본 내장이다.
EXTENDED_FEATURES_AVAILABLE = True


# =====================================================================
# 진입점(OptiCore.py) 정보 등록
# =====================================================================
# 모듈을 분리하면서 생긴 주의점:
#   분리 전에는 __doc__(헤더 주석)과 __file__(자기 경로)을 한 파일 안에서
#   바로 쓸 수 있었지만, 이제 config.py의 __doc__/__file__은 "config.py의 것"이다.
#   그래서 OptiCore.py가 시작할 때 자신의 헤더 주석과 경로를 여기에 등록해두고,
#   get_changelog_text() / get_entry_point_path()가 그 값을 사용한다.
_ENTRY_DOC = ""
_ENTRY_PATH = ""

# 이 파일(config.py)이 놓인 폴더 = 프로젝트 루트 (OptiCore.py와 같은 위치)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def register_entry_point(doc: str, file_path: str):
    """OptiCore.py가 시작할 때 자신의 헤더 주석(__doc__)과 경로(__file__)를 등록한다."""
    global _ENTRY_DOC, _ENTRY_PATH
    _ENTRY_DOC = doc or ""
    _ENTRY_PATH = file_path or ""


def get_entry_point_path() -> str:
    """진입점 OptiCore.py의 절대 경로 (등록되지 않았다면 프로젝트 루트 기준으로 추정)."""
    if _ENTRY_PATH:
        return os.path.abspath(_ENTRY_PATH)
    return os.path.join(PROJECT_ROOT, "OptiCore.py")


def resource_path(relative_path: str) -> str:
    """
    icon.ico 같은 동봉 리소스의 실제 경로를 돌려준다.

    - PyInstaller 단일 실행 파일(--onefile)로 빌드된 경우:
      실행 시 리소스가 임시 폴더(sys._MEIPASS)에 풀리므로 그쪽을 봐야 한다.
    - 소스(.py)로 그냥 실행한 경우:
      OptiCore.py가 있는 폴더(PROJECT_ROOT)를 기준으로 찾는다.

    빌드 예시:
      pyinstaller --onefile --windowed --icon=icon.ico ^
                  --add-data "icon.ico;." OptiCore.py
    """
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return os.path.join(base_path, relative_path)
    return os.path.join(PROJECT_ROOT, relative_path)


# =====================================================================
# 전역 상수 / 설정 파일 / 로그
# =====================================================================
LOG_FILE_PATH = os.path.join(os.getcwd(), "optimizer_log.txt")
SETTINGS_PATH = os.path.join(os.getcwd(), "optimizer_settings.json")

# [버그 수정] 코어 개수로 나눠 CPU%를 정규화하기 위한 상수
CPU_CORE_COUNT = psutil.cpu_count(logical=True) or 1

# 절대로 건드리면 안 되는 윈도우 필수 시스템 프로세스 (소문자 비교)
PROTECTED_PROCESSES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe", "svchost.exe",
    "dwm.exe", "fontdrvhost.exe", "memory compression", "audiodg.exe",
    "spoolsv.exe", "explorer.exe", "sihost.exe", "taskhostw.exe",
    "ctfmon.exe", "python.exe", "pythonw.exe", "opticore.py", "opticore.exe",
}

DEFAULT_SETTINGS = {
    "excluded_processes": [],  # 사용자가 직접 추가한 예외(화이트리스트) 프로세스 이름 목록
    "auto_schedule": {
        "enabled": False,
        "idle_minutes": 10,
        "ram_threshold_pct": 85,
    },
    "nagle_disabled": False,  # 마지막으로 적용한 Nagle 설정 상태 (참고용 기록)
    "theme": "purple",  # 현재 적용 중인 테마 키 (themes.py의 THEMES 참고)
    "auto_check_update": True,  # 프로그램 시작 시 자동으로 새 버전 확인 여부
    # [v2.0.0] Google Gemini 연동 설정
    #   gemini_api_key: 사용자가 설정 탭에서 직접 입력한 키 (소스에 하드코딩 금지)
    #   gemini_precheck_enabled: 원클릭 최적화 사전 점검 시 AI 조언을 쓸지 여부
    "gemini_api_key": "",
    "gemini_precheck_enabled": True,

    # ---- [v2.1.0] 창 닫기(X) 버튼 동작 ----
    #   "minimize_taskbar" (기본값) : 작업 표시줄로 최소화 — 창은 사라지지만
    #                                 작업 표시줄 아이콘이 남아 바로 되돌아올 수 있다
    #   "minimize_tray"             : 시스템 트레이(우측 하단)로 숨김
    #   "exit"                      : 프로그램 완전 종료
    #   ※ 유효하지 않은 값이 들어와도 models.CloseAction.normalize() 가
    #     기본값으로 되돌리므로 프로그램이 죽지 않는다.
    "close_button_action": "minimize_taskbar",

    # ---- [v2.1.0] 비침습적 게임 부스터 설정 ----
    #   v2.0.x의 게임 부스터는 감시 중 주기적으로 메모리를 강제 회수하고
    #   우선순위를 크게 올렸는데, 이 두 가지가 오히려 스터터와 오디오 끊김의
    #   원인이었다. v2.1.0에서는 아래 기본값처럼 "건드리지 않는 쪽"이 기본이다.
    "game_booster": {
        "poll_interval_sec": 5,        # 감시 폴링 주기 (5초 미만으로 내려가지 않음)
        "pre_trim_once": True,         # 게임 시작 직전 1회만 RAM 정리
        "stabilize_priority": True,    # 게임 우선순위를 Normal 로 안정화
        "allow_above_normal": False,   # 켜도 Above Normal 을 넘지 않음
        "pcore_affinity": False,       # 하이브리드 CPU에서만 의미 있음
        "suspend_background": False,   # 강제 종료 대신 일시 동결(NtSuspendProcess)
        "mmcss_games": True,           # MMCSS "Games" 등록
        "timer_resolution": True,      # 게임 중 1ms 타이머 유지
        "background_apps": [],         # 비우면 models.DEFAULT_BACKGROUND_APPS 사용
    },

    # ---- [v2.1.0] 전역 저지연 타이머 ----
    #   게임 중이 아닐 때도 1ms 타이머를 유지할지 여부. 켜면 반응성이 아주
    #   미세하게 좋아지지만 노트북 배터리 소모가 늘어 기본값은 False 다.
    "low_latency_timer_always": False,
}


def load_settings() -> dict:
    """설정 파일(json)을 읽어온다. 없거나 손상되었으면 기본값 사용."""
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_SETTINGS))  # deep copy
            merged.update(data)
            return merged
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_SETTINGS))


def save_settings(settings: dict) -> bool:
    """
    설정을 json 파일로 저장한다 (다음 실행 시에도 유지됨).

    [v2.1.0 원자적(Atomic) 저장]
      기존 방식은 open(..., "w") 로 원본을 먼저 비운 뒤 새 내용을 썼다.
      그 사이(보통 수 ms)에 강제 종료·정전·블루스크린이 나면
      optimizer_settings.json 이 0바이트로 남아 다음 실행 때 설정이 전부
      초기화된다. 실제로 게임 중 강제 종료가 잦은 환경에서 충분히 일어난다.

      그래서 아래 순서로 바꿨다.
        1) 같은 폴더에 임시 파일(.tmp)을 만들고 거기에 전부 쓴다
        2) flush + os.fsync 로 디스크에 실제로 내려썼음을 보장한다
        3) os.replace 로 원본 위에 "원자적으로" 바꿔치기한다

      os.replace 는 같은 볼륨 안에서 원자적 연산이 보장되므로, 어느 시점에
      전원이 나가도 파일은 "옛 내용" 아니면 "새 내용"이지 절대 반쯤 쓰인
      상태가 되지 않는다. 임시 파일을 같은 폴더에 만드는 이유도 이것이다
      (다른 볼륨이면 원자성이 깨진다).
    """
    directory = os.path.dirname(SETTINGS_PATH) or "."
    tmp_path = None
    try:
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix="optimizer_settings.", suffix=".tmp", dir=directory
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, SETTINGS_PATH)  # ← 원자적 교체
        tmp_path = None
        return True
    except Exception as e:
        write_log(f"설정 저장 실패: {e}")
        return False
    finally:
        # 교체 전에 실패했다면 임시 파일이 남지 않도록 정리한다.
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# =====================================================================
# 로그 (RotatingFileHandler — 무한정 커지지 않도록 제한)
# =====================================================================
# [v2.1.0] 기존에는 optimizer_log.txt 에 계속 append 하기만 해서, 자동 정리를
# 켜두고 몇 달 쓰면 수십 MB까지 자라 설정 탭의 [로그 보기]가 버벅였다.
# 이제 5MB를 넘으면 optimizer_log.txt.1 / .2 로 넘기고 가장 오래된 것을 버린다.
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5MB
LOG_BACKUP_COUNT = 2              # 백업 2개 (총 최대 약 15MB)

_LOGGER_NAME = "OptiCore"
_logger = None
_logger_lock = threading.Lock()


def _get_logger() -> logging.Logger:
    """로거를 지연 생성한다 (여러 스레드에서 동시에 불러도 핸들러가 중복되지 않음)."""
    global _logger
    if _logger is not None:
        return _logger
    with _logger_lock:
        if _logger is not None:
            return _logger
        logger = logging.getLogger(_LOGGER_NAME)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # 루트 로거로 새어나가 콘솔에 중복 출력되는 것 방지
        if not logger.handlers:
            try:
                handler = RotatingFileHandler(
                    LOG_FILE_PATH,
                    maxBytes=LOG_MAX_BYTES,
                    backupCount=LOG_BACKUP_COUNT,
                    encoding="utf-8",
                    delay=True,  # 첫 기록이 있을 때까지 파일을 열지 않는다
                )
                # 기존 로그 형식([YYYY-MM-DD HH:MM:SS] 메시지)을 그대로 유지한다.
                # 설정 탭의 로그 뷰어와 사용자가 익숙한 형태를 깨지 않기 위함.
                handler.setFormatter(
                    logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
                )
                logger.addHandler(handler)
            except Exception:
                # 파일을 못 여는 환경(권한/경로 문제)에서도 프로그램은 계속 동작해야 한다.
                logger.addHandler(logging.NullHandler())
        _logger = logger
        return _logger


def write_log(message: str):
    """모든 실제 조치 내역을 로그 파일에 남긴다 (5MB 초과 시 자동 로테이션)."""
    try:
        _get_logger().info(message)
    except Exception:
        pass


def read_log_tail(max_chars: int = 200000) -> str:
    """설정/대시보드 탭의 [로그 보기]용. 파일이 커도 뒷부분만 읽어온다."""
    if not os.path.exists(LOG_FILE_PATH):
        return "아직 기록된 로그가 없습니다."
    try:
        size = os.path.getsize(LOG_FILE_PATH)
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            if size > max_chars:
                f.seek(size - max_chars)
                f.readline()  # 잘린 첫 줄은 버린다
            return f.read()
    except Exception as e:
        return f"로그를 읽을 수 없습니다: {e}"


def get_changelog_text() -> str:
    """OptiCore.py 최상단 주석의 [변경 이력] 섹션을 그대로 추출해 설정 탭에 표시한다.
    (변경 이력을 이중으로 관리하지 않도록 헤더 주석을 유일한 원본으로 사용)

    [v2.0.0] 모듈 분리 후에는 config.py의 __doc__가 아니라, OptiCore.py가
    register_entry_point()로 등록해준 헤더 주석을 사용한다. 등록 전에 호출되는
    상황(단위 테스트 등)에 대비해 파일에서 직접 읽는 예비 경로도 둔다.

    [v2.1.0] 헤더 표준화로 섹션 제목이 [변경 이력] → [주요 변경 이력]으로
    바뀌었다. 다른 계정에서 옛 헤더가 담긴 파일을 붙여넣는 경우에도 깨지지
    않도록 두 이름을 모두 인식한다."""
    doc = _ENTRY_DOC
    if not doc:
        doc = _read_entry_docstring_from_file()
    if not doc:
        return "변경 이력을 불러올 수 없습니다."

    divider = " " + ("=" * 69) + "\n"
    # 변경 이력이 끝나는 지점. 헤더에 어떤 섹션이 이어지든 거기서 잘라낸다.
    # (이 목록에 없는 섹션을 새로 추가했다면 여기에도 함께 넣어줄 것)
    stop_markers = (
        "\n ⚠️ 이 파일을 처음 여는",
        "\n [모듈 구조",
        "\n [AI 연동",
        "\n [필요 라이브러리",
        "\n [주의]",
    )
    for title in (" [주요 변경 이력]\n", " [변경 이력]\n"):
        for section_header in (title + divider, title):
            if section_header not in doc:
                continue
            body = doc.split(section_header, 1)[1]
            # 여러 종료 표식 중 가장 먼저 나오는 곳에서 자른다.
            cut = len(body)
            for marker in stop_markers:
                idx = body.find(marker)
                if idx != -1:
                    cut = min(cut, idx)
            changelog = body[:cut].strip("\n")
            # 섹션 사이의 구분선(=====)이 끝에 남으면 지저분하므로 정리한다.
            changelog = changelog.rstrip().rstrip("=").rstrip()
            if changelog:
                return changelog
    return "변경 이력을 불러올 수 없습니다."


def _read_entry_docstring_from_file() -> str:
    """예비 경로: OptiCore.py 파일을 직접 파싱해 헤더 docstring만 꺼내온다."""
    try:
        import ast
        with open(get_entry_point_path(), "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return ast.get_docstring(tree) or ""
    except Exception:
        return ""
