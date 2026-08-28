# -*- coding: utf-8 -*-
"""
config.py — OptiCore 전역 설정 계층 (최하위 모듈)

이 모듈은 OptiCore 안에서 "가장 아래"에 있습니다.
즉, 이 파일은 프로젝트 내부의 다른 어떤 모듈도 import 하지 않습니다.
(단방향 import 구조 유지 → 순환 참조 방지)

담당 범위
  - 프로그램 이름/버전 상수, GitHub 저장소 상수
  - 선택적 의존성(send2trash / pynvml / winreg) 로드 및 가용 플래그
  - 설정 파일(optimizer_settings.json) 로드/저장
  - 로그 파일(optimizer_log.txt) 기록
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
import platform
from datetime import datetime

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
APP_VERSION = "2.0.1"

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


def save_settings(settings: dict):
    """설정을 json 파일로 저장한다 (다음 실행 시에도 유지됨)."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def write_log(message: str):
    """모든 실제 조치 내역을 로그 파일에 남긴다."""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def get_changelog_text() -> str:
    """OptiCore.py 최상단 주석의 [변경 이력] 섹션을 그대로 추출해 설정 탭에 표시한다.
    (변경 이력을 이중으로 관리하지 않도록 헤더 주석을 유일한 원본으로 사용)

    [v2.0.0] 모듈 분리 후에는 config.py의 __doc__가 아니라, OptiCore.py가
    register_entry_point()로 등록해준 헤더 주석을 사용한다. 등록 전에 호출되는
    상황(단위 테스트 등)에 대비해 파일에서 직접 읽는 예비 경로도 둔다."""
    doc = _ENTRY_DOC
    if not doc:
        doc = _read_entry_docstring_from_file()

    section_header = " [변경 이력]\n " + ("=" * 69) + "\n"
    try:
        after_divider = doc.split(section_header, 1)[1]
        changelog = after_divider.split("\n [주의]", 1)[0]
        return changelog.strip("\n")
    except IndexError:
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
