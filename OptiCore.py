# -*- coding: utf-8 -*-
"""
=====================================================================
 ⚠️ 이 파일을 처음 여는 Claude(또는 다른 작업자)는 아래 내용을 먼저 읽으세요
=====================================================================
 제작자 및 관리자: JeulGemI
 공동 협업자: KRJohnWick

 이 파일은 GitHub에 소스로 공개되고, 사용자가 이를 .exe로 빌드해 배포합니다.
 즉 여기서 만든 코드가 그대로 최종 배포판의 기반이 됩니다. 아래 원칙을
 반드시 지켜서 작업하세요.

 1. [기준 코드 원칙] 사용자는 여러 Claude 계정을 돌려가며 이 프로그램을
    수정합니다. 즉 지금 이 파일이 "가장 최신"이 아닐 수 있습니다.
    → 수정/업데이트 요청을 받으면, 사용자가 대화 중 새로 전달한
      'OptiCore.py' 코드가 있다면 그것을 기준(base)으로 삼아 그 위에
      요청 사항을 구현하세요. 자신의 기억 속 이전 버전을 기준으로 삼지 마세요.
    → 예외는 MAJOR 버전이 오르는 "대격변" 패치뿐입니다. 이 경우에만
      구조를 전면 재설계해도 됩니다.
 2. [파일명 고정] 실제 파일명은 항상 "OptiCore.py"로 고정합니다.
    버전이 올라가도 파일명은 절대 바꾸지 않습니다.
    (예: OptiCore_V1.0.py, OptiCore_v2.py 같은 형식 금지)
    사용자가 다른 계정에서 받은 코드의 파일명이 이 규칙과 다르면
    (예: OptiCore_V1_0.py), 작업 결과물은 다시 "OptiCore.py"로 저장하세요.
 3. [버전 갱신] 아래 [버전 표기 규칙]에 따라 APP_VERSION 상수, 창 제목,
    그리고 이 헤더의 [변경 이력]을 매번 함께 갱신하세요. 주석만 바꾸는
    작업(문서 정책 변경 등)도 "업데이트"로 취급해 PATCH를 올리고
    변경 이력에 기록하세요.
 4. [변경 이력 유지] 새 항목은 항상 맨 위에 추가하고, 목록이 너무
    길어지면 오래된 항목을 요약해서 정리하세요. 절대 삭제로 역사를
    지우지 마세요.

=====================================================================
 OptiCore - 스마트 시스템 최적화 프로그램
 제작자 및 관리자: JeulGemI
 공동 협업자: KRJohnWick
 현재 버전: v1.1.0
=====================================================================
 [파일명 규칙]
   실제 파일명은 항상 "OptiCore.py"로 고정합니다. 버전이 올라가도
   파일명은 바꾸지 않습니다 (예: OptiCore_V1.0.py 같은 형식 금지).
   버전 표시는 아래 APP_VERSION 상수 + 창 제목 + 이 헤더의 [변경 이력]에서만
   관리합니다. 사용자가 다른 계정에서 받은 코드를 붙여줄 때 파일명이
   이 규칙과 다르면(OptiCore_V1_0.py 등) 응답 코드에서는 "OptiCore.py"로
   되돌려서 저장하세요.

 [버전 표기 규칙]
   형식: MAJOR.MINOR.PATCH (예: 1.0.0, 1.0.1, ..., 1.0.13, 1.1.0, 1.12.3, 2.0.0)
   - PATCH (세 번째 숫자): 자잘한 버그 수정/문서 갱신 등 소규모 변경 시 +1
     (예: 1.0.0 -> 1.0.1 -> ... -> 1.0.13)
   - MINOR (두 번째 숫자): 기능 추가 시 +1, PATCH는 0으로 리셋 (예: 1.0.13 -> 1.1.0)
   - MAJOR (첫 번째 숫자): 구조 전면 개편 등 대격변 시 +1, MINOR/PATCH 모두 0으로 리셋
     (예: 1.x.x -> 2.0.0). 대격변 패치일 때만 "기준 코드 원칙"의 예외로,
     기존 코드 구조를 전면 재설계해도 됩니다.
   업데이트할 때마다 이 헤더의 "버전"(및 APP_VERSION 상수)과 아래 "변경 이력"을
   함께 갱신합니다. 변경 이력은 최신 버전이 맨 위로 오도록 추가하고,
   너무 길어지면 오래된 항목은 요약합니다.

 [배포 안내]
   이 프로그램은 GitHub 저장소 "OptiCore"에서 .exe로 빌드되어 배포됩니다.
   Claude가 수정한 OptiCore.py는 사용자가 이후 GitHub에 반영합니다.

 [필요 라이브러리 설치]
   pip install PyQt6 psutil Send2Trash
   (선택) NVIDIA GPU 정보: pip install nvidia-ml-py

 =====================================================================
 [변경 이력]
 =====================================================================
 v1.1.0 (UI 경로 개편 + 설정 탭 신설)
   - 상단 탭 배치를 일관성 있게 재정렬: 최적화 관련 기능(원클릭 최적화 → 성능
     대시보드 → 성능&게이밍 → 블로트웨어 제거 → 시작 프로그램 → 디스크 정리+ →
     진단&복원 → 전문가 팁&네트워크)을 앞쪽에 모으고, 화이트리스트 관리 →
     설정(신규) 순으로 뒤에 배치.
   - "⚙️ 설정" 탭 신설: 기존에 화이트리스트 탭 안에 깊숙이 있던 "🎨 테마 선택"을
     이곳으로 이동. 그 외 프로그램 정보(제작자/협업자/버전)와 업데이트 내역을
     함께 확인할 수 있도록 구성.
   - 공동 협업자 "KRJohnWick" 합류. 파일 상단 주석 및 설정 탭 프로그램 정보에 반영.

 v1.0.4 (리네이밍 — 기능 변경 없음)
   - 이전에 별도 모듈로서 기능하던 일부 확장 기능(블로트웨어 제거/시작프로그램
     관리/성능&게이밍 튜닝/진단&복원/디스크 정리+ 등) 관련 식별자를 프로그램
     기본 기능에 맞게 정리. 동작/로직은 동일하며 이름만 변경:
     · 탭 UI를 담당하던 믹스인 클래스명을 ExtendedFeaturesMixin으로 통일
     · 관련 가용 여부 플래그를 EXTENDED_FEATURES_AVAILABLE으로 통일
     · 시작프로그램 비활성화 저장용 레지스트리 키를 Run_OptiCoreDisabled로 통일
     · 관련 주석/문서 표현을 "확장 기능(기본 내장)"으로 통일
   - 주의: 구버전에서 시작프로그램을 비활성화한 적이 있는 PC는 이전 레지스트리
     키 이름으로 저장된 항목이 남아있을 수 있어 새 키 이름으로는 안 잡힐 수
     있음. 필요 시 시작프로그램 탭에서 항목을 다시 한번 확인하는 것을 권장.

 v1.0.3 (문서/정책 갱신 — 기능 변경 없음)
   - 파일 최상단에 "다른 Claude가 반드시 먼저 읽어야 할 안내" 블록 추가:
     제작자/관리자 "JeulGemI" 명시, 기준 코드 원칙(대격변 아니면 항상
     사용자가 전달한 OptiCore.py 코드를 기준으로 수정할 것), 파일명 고정
     원칙, 버전/변경이력 갱신 의무를 명문화.
   - GitHub 배포 안내 추가 (OptiCore가 GitHub에서 .exe로 빌드/배포됨).

 v1.0.2 (버그 수정 + 파일명 정책 변경)
   - 파일명을 "OptiCore.py"로 고정. 버전 번호를 파일명(OptiCore_V1.0.py 등)에
     박아두지 않고, APP_NAME/APP_VERSION 상수 + 창 제목 + 이 변경 이력에서만
     관리하도록 변경 (버전 오를 때마다 파일명을 바꿔야 하는 문제 해결).
   - 창 제목에 "OptiCore vX.Y.Z"가 표시되도록 setWindowTitle() 수정.

 v1.0.1 (버그 수정)
   - on_flush_dns_perf_tab()이 파일명을 하드코딩해 자기 자신을 import하던 문제 수정
     (main_real__2_ 모듈을 찾는 방식이라 파일명이 바뀌면 항상 실패하던 구조였음).
     이미 모듈에 정의되어 있던 flush_dns()를 바로 호출하도록 변경.
   - PROTECTED_PROCESSES 목록의 파일명 항목을 새 프로그램 이름에 맞게 갱신.

 v1.0.0 (기준 버전 - OptiCore로 이름 확정)
   - 이전까지 이름 없이 개발되던 통합판을 "OptiCore"로 명명하고 버전 관리를 시작함.
   - 포함된 주요 기능:
     · 실제 RAM 워킹셋 트림 / CPU 우선순위 조정 / SSD·브라우저 캐시 정리 (휴지통 이동)
     · 게임 부스터 (감시 시작 시 우선순위 부스트, 종료 시 자동 원복)
     · DNS 캐시 초기화, Nagle 알고리즘 토글, 시스템 복구 지점 생성
     · 자동 스마트 정리(유휴시간/RAM 임계값 기반), 플로팅 OSD, 화이트리스트 관리, Undo 타임라인
     · 확장 기능 모듈(기본 내장): 블로트웨어 제거, 시작 프로그램 관리, 성능&게이밍 튜닝,
       진단&복원, 디스크 정리+ (5개 탭 추가)
   - CPU 사용량 코어 수 정규화, 첫 호출 0% 문제, UI 프리징(QThread 분리), RAM 측정 시차,
     트레이 고립 방지 등 이전 단계에서 발견된 버그들은 이 기준 버전에 이미 반영되어 있음.

 [주의]
   - RAM/CPU 실측 조작, 레지스트리 조작, 복구 지점 생성, 확장 기능 모듈 상당수는 Windows 전용입니다.
   - 레지스트리/서비스/전원/시작프로그램 조작 기능 대부분은 관리자 권한이 필요합니다.
=====================================================================
"""

import sys
import os
import time
import json
import ctypes
import platform
import tempfile
import subprocess
from datetime import datetime

import psutil

# [v1.0.2] 파일명에 버전을 박아두면(OptiCore_V1.0.py 등) 버전이 오를 때마다
# 파일명을 바꿔야 하고, import/문서 참조가 깨지기 쉽습니다.
# 그래서 실제 파일명은 "OptiCore.py"로 고정하고, 버전은 아래 상수 + 창 제목 +
# 파일 최상단 주석의 [변경 이력]에서만 관리합니다.
# (다른 Claude 계정/세션에서 이 파일을 이어받아 작업할 때도 이 상수를 갱신 기준으로 삼으세요.)
APP_NAME = "OptiCore"
APP_VERSION = "1.1.0"

try:
    from send2trash import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False

IS_WINDOWS = platform.system() == "Windows"

WINREG_AVAILABLE = False
if IS_WINDOWS:
    try:
        import winreg
        WINREG_AVAILABLE = True
    except ImportError:
        WINREG_AVAILABLE = False

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QSlider, QTabWidget, QGroupBox, QFrame,
    QListWidget, QListWidgetItem, QDialog, QProgressBar, QMessageBox,
    QScrollArea, QTextEdit, QComboBox, QSystemTrayIcon, QMenu, QStyle,
    QLineEdit, QSpinBox, QAbstractItemView
)

EXTENDED_FEATURES_AVAILABLE = True


# =====================================================================
# 0. 전역 상수 / 설정 파일 / 로그
# =====================================================================
LOG_FILE_PATH = os.path.join(os.getcwd(), "optimizer_log.txt")
SETTINGS_PATH = os.path.join(os.getcwd(), "optimizer_settings.json")

# [버그 수정] 코어 개수로 나눠 CPU%를 정규화하기 위한 상수
CPU_CORE_COUNT = psutil.cpu_count(logical=True) or 1

# [버그 수정] psutil Process 객체를 재사용하기 위한 전역 캐시
# (매번 새로 만들면 cpu_percent()가 항상 0.0을 반환하는 문제가 있었음)
_PROCESS_CPU_CACHE = {}

# 절대로 건드리면 안 되는 윈도우 필수 시스템 프로세스 (소문자 비교)
PROTECTED_PROCESSES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe", "svchost.exe",
    "dwm.exe", "fontdrvhost.exe", "memory compression", "audiodg.exe",
    "spoolsv.exe", "explorer.exe", "sihost.exe", "taskhostw.exe",
    "ctfmon.exe", "python.exe", "pythonw.exe", "opticore_v1.0.py",
}

DEFAULT_SETTINGS = {
    "excluded_processes": [],  # 사용자가 직접 추가한 예외(화이트리스트) 프로세스 이름 목록
    "auto_schedule": {
        "enabled": False,
        "idle_minutes": 10,
        "ram_threshold_pct": 85,
    },
    "nagle_disabled": False,  # 마지막으로 적용한 Nagle 설정 상태 (참고용 기록)
    "theme": "purple",  # 현재 적용 중인 테마 키 (THEMES 딕셔너리 참고)
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
    """파일 최상단 주석의 [변경 이력] 섹션을 그대로 추출해 설정 탭에 표시한다.
    (변경 이력을 이중으로 관리하지 않도록 헤더 주석을 유일한 원본으로 사용)"""
    doc = __doc__ or ""
    section_header = " [변경 이력]\n " + ("=" * 69) + "\n"
    try:
        after_divider = doc.split(section_header, 1)[1]
        changelog = after_divider.split("\n [주의]", 1)[0]
        return changelog.strip("\n")
    except IndexError:
        return "변경 이력을 불러올 수 없습니다."


def is_admin() -> bool:
    if not IS_WINDOWS:
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_foreground_pid():
    """현재 활성화된(포커스된) 창의 프로세스 ID -> 실수로 건드리지 않기 위한 보호용."""
    if not IS_WINDOWS:
        return None
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value
    except Exception:
        return None


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_minutes() -> float:
    """사용자가 마지막으로 키보드/마우스를 조작한 뒤 몇 분이 지났는지 반환 (자동 스케줄링용)."""
    if not IS_WINDOWS:
        return 0.0
    try:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            millis_idle = ctypes.windll.kernel32.GetTickCount() - info.dwTime
            return millis_idle / 60000.0
    except Exception:
        pass
    return 0.0


def is_protected(proc_name: str, pid: int, foreground_pid, excluded_set=None) -> bool:
    """이 프로세스를 건드려도 되는지 판단. 시스템 보호 목록 + 사용자 화이트리스트 모두 확인."""
    name_lower = (proc_name or "").lower()
    if name_lower in PROTECTED_PROCESSES:
        return True
    if excluded_set and name_lower in excluded_set:
        return True
    if pid == os.getpid():
        return True
    if foreground_pid and pid == foreground_pid:
        return True
    return False


# =====================================================================
# 1. 실제 스캔(조사) 함수들
# =====================================================================
def scan_ram_candidates(intensity: int, excluded_set=None):
    """RAM 트림 대상 프로세스를 찾는다. 강도가 높을수록 더 작은 메모리 사용 프로세스까지 포함."""
    threshold_mb = {1: 250, 2: 120, 3: 40}[intensity]
    foreground_pid = get_foreground_pid()
    candidates = []

    for proc in psutil.process_iter(attrs=["pid", "name", "memory_info"]):
        try:
            name = proc.info["name"] or "unknown"
            pid = proc.info["pid"]
            mem_mb = proc.info["memory_info"].rss / (1024 * 1024)

            if is_protected(name, pid, foreground_pid, excluded_set):
                continue
            if mem_mb < threshold_mb:
                continue
            candidates.append((pid, name, round(mem_mb, 1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[:15]


def scan_cpu_candidates(intensity: int, excluded_set=None):
    """
    CPU 우선순위를 낮출 수 있는 대상을 찾는다.
    [버그 수정] 2단계부터 동작하도록 완화했고(기존엔 3단계 전용),
    전역 Process 캐시를 사용해 '첫 호출 0% 문제'를 해결했다.
    반환값은 코어 개수로 정규화된 '시스템 전체 대비 %'.
    """
    if intensity < 2:
        return []  # 1단계(약함)에서는 안전을 위해 CPU 조작을 하지 않음

    foreground_pid = get_foreground_pid()
    global _PROCESS_CPU_CACHE

    current_pids = set()
    for p in psutil.process_iter(attrs=["pid"]):
        pid = p.info["pid"]
        current_pids.add(pid)
        if pid not in _PROCESS_CPU_CACHE:
            try:
                proc_obj = psutil.Process(pid)
                proc_obj.cpu_percent(interval=None)  # 기준점을 잡기 위한 첫 호출(버림)
                _PROCESS_CPU_CACHE[pid] = proc_obj
            except Exception:
                continue

    # 이미 종료된 프로세스는 캐시에서 정리
    for pid in list(_PROCESS_CPU_CACHE.keys()):
        if pid not in current_pids:
            del _PROCESS_CPU_CACHE[pid]

    time.sleep(0.6)  # 의미 있는 델타 값을 얻기 위한 측정 구간

    # [버그 수정] 필터링 기준 완화: 2단계 2.0%, 3단계 0.5% (정규화된 값 기준)
    threshold = {2: 2.0, 3: 0.5}[intensity]

    candidates = []
    for pid, proc_obj in list(_PROCESS_CPU_CACHE.items()):
        try:
            name = proc_obj.name()
            raw_cpu_pct = proc_obj.cpu_percent(interval=None)
            cpu_pct = raw_cpu_pct / CPU_CORE_COUNT  # 시스템 전체 대비로 정규화

            if is_protected(name, pid, foreground_pid, excluded_set):
                continue
            if cpu_pct < threshold:
                continue
            candidates.append((pid, name, round(cpu_pct, 1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[:10]


def scan_temp_files(intensity: int):
    """사용자 TEMP 폴더의 오래된 파일을 찾는다 (시스템 폴더는 절대 건드리지 않음)."""
    min_age_minutes = {1: 7 * 24 * 60, 2: 24 * 60, 3: 10}[intensity]
    cutoff_time = time.time() - (min_age_minutes * 60)

    safe_dirs = set()
    safe_dirs.add(tempfile.gettempdir())
    if os.environ.get("TEMP"):
        safe_dirs.add(os.environ["TEMP"])
    if os.environ.get("TMP"):
        safe_dirs.add(os.environ["TMP"])

    target_files = []
    total_size = 0

    for base_dir in safe_dirs:
        if not os.path.isdir(base_dir):
            continue
        try:
            for root, dirs, files in os.walk(base_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        if os.path.islink(fpath):
                            continue
                        stat = os.stat(fpath)
                        if stat.st_mtime > cutoff_time:
                            continue
                        target_files.append(fpath)
                        total_size += stat.st_size
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except Exception:
            continue

    return target_files, total_size


def get_browser_cache_dirs():
    """Chrome/Edge의 '캐시 폴더만' 찾는다. 쿠키/비밀번호/북마크가 있는 상위 폴더는 절대 건드리지 않음."""
    dirs = []
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if not local_appdata:
        return dirs
    candidates = {
        "Chrome": os.path.join(local_appdata, "Google", "Chrome", "User Data", "Default", "Cache"),
        "Edge": os.path.join(local_appdata, "Microsoft", "Edge", "User Data", "Default", "Cache"),
    }
    for browser, path in candidates.items():
        if os.path.isdir(path):
            dirs.append((browser, path))
    return dirs


def scan_browser_cache_files(intensity: int):
    """브라우저 캐시 폴더 내 오래된 파일을 찾는다 (SSD 정리와 동일한 나이 기준 사용)."""
    min_age_minutes = {1: 7 * 24 * 60, 2: 24 * 60, 3: 10}[intensity]
    cutoff_time = time.time() - (min_age_minutes * 60)

    target_files = []
    total_size = 0
    for browser, base_dir in get_browser_cache_dirs():
        try:
            for root, dirs, files in os.walk(base_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        if os.path.islink(fpath):
                            continue
                        stat = os.stat(fpath)
                        if stat.st_mtime > cutoff_time:
                            continue
                        target_files.append(fpath)
                        total_size += stat.st_size
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except Exception:
            continue
    return target_files, total_size


def scan_gpu_info():
    """(정보 제공 전용) NVIDIA GPU의 VRAM 사용량을 조회한다."""
    if not NVML_AVAILABLE:
        return None
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="ignore")

        top_processes = []
        try:
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            for p in procs:
                try:
                    proc_name = psutil.Process(p.pid).name()
                except Exception:
                    proc_name = f"PID {p.pid}"
                used_mb = (p.usedGpuMemory or 0) / (1024 * 1024)
                top_processes.append((proc_name, round(used_mb, 1)))
        except Exception:
            pass

        return {
            "gpu_name": name,
            "total_mb": round(mem_info.total / (1024 * 1024), 1),
            "used_mb": round(mem_info.used / (1024 * 1024), 1),
            "free_mb": round(mem_info.free / (1024 * 1024), 1),
            "top_processes": sorted(top_processes, key=lambda x: x[1], reverse=True)[:5],
        }
    except Exception:
        return None


def get_watchable_processes():
    """게임 감시/부스트 대상으로 선택할 수 있는 후보 프로세스 목록."""
    candidates = []
    for proc in psutil.process_iter(attrs=["pid", "name", "memory_info"]):
        try:
            name = proc.info["name"] or "unknown"
            pid = proc.info["pid"]
            if name.lower() in PROTECTED_PROCESSES or pid == os.getpid():
                continue
            mem_mb = proc.info["memory_info"].rss / (1024 * 1024)
            if mem_mb < 300:
                continue
            candidates.append((pid, name, round(mem_mb, 1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates


# =====================================================================
# 2. 실제 조치(액션) 함수들
# =====================================================================
def trim_process_working_set(pid: int) -> bool:
    """프로세스를 종료하지 않고 워킹셋(물리 메모리 점유분)만 비운다."""
    if not IS_WINDOWS:
        return False
    try:
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_SET_QUOTA = 0x0100
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, False, pid
        )
        if not handle:
            return False
        result = ctypes.windll.psapi.EmptyWorkingSet(handle)
        ctypes.windll.kernel32.CloseHandle(handle)
        return bool(result)
    except Exception:
        return False


def lower_process_priority(pid: int) -> bool:
    """프로세스를 종료하지 않고 우선순위만 낮춘다 (되돌리기 가능)."""
    try:
        p = psutil.Process(pid)
        if IS_WINDOWS:
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            p.nice(10)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return False


def restore_process_priority(pid: int) -> bool:
    """낮췄던 우선순위를 '보통'으로 원복한다."""
    try:
        p = psutil.Process(pid)
        if IS_WINDOWS:
            p.nice(psutil.NORMAL_PRIORITY_CLASS)
        else:
            p.nice(0)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return False


def raise_process_priority(pid: int) -> bool:
    """게임 부스트용: 감시 중인 게임 프로세스의 우선순위를 한 단계 높인다 (되돌리기 가능)."""
    try:
        p = psutil.Process(pid)
        if IS_WINDOWS:
            p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
        else:
            p.nice(-5)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return False


def move_file_to_trash(filepath: str) -> bool:
    """파일을 영구 삭제하지 않고 휴지통으로 이동한다."""
    if not SEND2TRASH_AVAILABLE:
        return False
    try:
        send2trash(filepath)
        return True
    except Exception:
        return False


def flush_dns():
    """Windows DNS 캐시를 초기화한다 (ipconfig /flushdns)."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=10
        )
        success = result.returncode == 0
        write_log(f"DNS 캐시 초기화 {'성공' if success else '실패'}")
        msg = (result.stdout or result.stderr or "").strip()
        return success, msg
    except Exception as e:
        return False, str(e)


def set_nagle(disable: bool):
    """
    Nagle 알고리즘을 끄거나(핑 최적화) 기본값으로 되돌린다.
    - HKLM\\...\\Tcpip\\Parameters\\Interfaces 하위 모든 인터페이스에
      TcpAckFrequency=1, TCPNoDelay=1 값을 설정/삭제한다 (문서화된 표준 기법).
    - 관리자 권한 필수. 적용 후 네트워크 어댑터 재시작 또는 재부팅이 필요할 수 있다.
    """
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다. 프로그램을 관리자 권한으로 다시 실행해주세요."

    base_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    changed, failed = 0, 0
    try:
        base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path, 0, winreg.KEY_ALL_ACCESS)
    except Exception as e:
        return False, f"레지스트리 접근 실패: {e}"

    try:
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(base_key, i)
            except OSError:
                break
            i += 1
            try:
                subkey = winreg.OpenKey(base_key, subkey_name, 0, winreg.KEY_ALL_ACCESS)
                if disable:
                    winreg.SetValueEx(subkey, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(subkey, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                else:
                    for value_name in ("TcpAckFrequency", "TCPNoDelay"):
                        try:
                            winreg.DeleteValue(subkey, value_name)
                        except FileNotFoundError:
                            pass
                winreg.CloseKey(subkey)
                changed += 1
            except Exception:
                failed += 1
    finally:
        winreg.CloseKey(base_key)

    write_log(f"Nagle 알고리즘 {'비활성화' if disable else '기본값 복원'} 적용: 성공 {changed}, 실패 {failed}")
    msg = (
        f"{changed}개 네트워크 인터페이스에 적용했습니다 (실패 {failed}개).\n"
        "완전히 적용되려면 네트워크 어댑터를 재시작하거나 재부팅하세요."
    )
    return changed > 0, msg


def create_restore_point():
    """PowerShell을 통해 시스템 복구 지점을 생성한다. 관리자 권한 필요."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."
    try:
        cmd = [
            "powershell", "-Command",
            "Checkpoint-Computer -Description 'SmartOptimizer' -RestorePointType 'MODIFY_SETTINGS'"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            write_log("시스템 복구 지점 생성 성공")
            return True, "복구 지점을 생성했습니다."
        else:
            err = (result.stderr or "알 수 없는 오류").strip()
            write_log(f"시스템 복구 지점 생성 실패: {err}")
            return False, (
                f"복구 지점 생성에 실패했습니다:\n{err}\n\n"
                "참고: Windows는 기본적으로 24시간에 1번만 복구 지점 생성을 허용합니다."
            )
    except Exception as e:
        return False, f"오류 발생: {e}"


# =====================================================================
# 3. 스캔 전용 스레드 (ScannerWorker) - UI 프리징 방지
# =====================================================================
class ScannerWorker(QThread):
    """RAM/CPU/임시파일/브라우저 캐시 스캔을 백그라운드에서 수행 (UI가 멈추지 않도록)."""
    scan_finished = pyqtSignal(dict)

    def __init__(self, options: dict, intensity: int, excluded_set: set, parent=None):
        super().__init__(parent)
        self.options = options
        self.intensity = intensity
        self.excluded_set = excluded_set

    def run(self):
        result = {}
        result["ram_candidates"] = (
            scan_ram_candidates(self.intensity, self.excluded_set)
            if self.options.get("ram") and IS_WINDOWS else []
        )
        result["cpu_candidates"] = (
            scan_cpu_candidates(self.intensity, self.excluded_set)
            if self.options.get("cpu") else []
        )
        if self.options.get("ssd"):
            result["temp_files"], result["temp_size"] = scan_temp_files(self.intensity)
        else:
            result["temp_files"], result["temp_size"] = [], 0

        if self.options.get("browser"):
            result["browser_files"], result["browser_size"] = scan_browser_cache_files(self.intensity)
        else:
            result["browser_files"], result["browser_size"] = [], 0

        result["dns_selected"] = self.options.get("dns", False)
        result["gpu_selected"] = self.options.get("gpu", False)
        self.scan_finished.emit(result)


# =====================================================================
# 4. 최적화 작업 스레드 (QThread)
# =====================================================================
class OptimizationWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_report = pyqtSignal(dict)

    def __init__(self, ram_pids, cpu_pids, temp_files, browser_files, do_dns, do_gpu_scan, parent=None):
        super().__init__(parent)
        self.ram_pids = ram_pids
        self.cpu_pids = cpu_pids
        self.temp_files = temp_files
        self.browser_files = browser_files
        self.do_dns = do_dns
        self.do_gpu_scan = do_gpu_scan

    def run(self):
        psutil.cpu_percent(interval=None)  # 워밍업 호출
        time.sleep(0.2)
        mem_before = psutil.virtual_memory()
        cpu_before = psutil.cpu_percent(interval=0.3)

        total_tasks = (
            len(self.ram_pids) + len(self.cpu_pids) + len(self.temp_files)
            + len(self.browser_files) + (1 if self.do_dns else 0) + 1
        )
        total_tasks = max(total_tasks, 1)
        done = 0

        ram_trimmed_count = 0
        cpu_deprioritized = []
        cpu_reclaimed_pct = 0.0
        files_deleted = 0
        bytes_deleted = 0
        browser_files_deleted = 0
        browser_bytes_deleted = 0
        dns_result = None

        # ---- 1) RAM 워킹셋 트림 ----
        for pid, name, mem_mb in self.ram_pids:
            self.progress_changed.emit(int(done / total_tasks * 100), f"RAM 정리 중: {name}")
            if trim_process_working_set(pid):
                ram_trimmed_count += 1
                write_log(f"RAM 워킹셋 트림 성공: {name} (PID {pid}, {mem_mb}MB)")
            else:
                write_log(f"RAM 워킹셋 트림 실패(건너뜀): {name} (PID {pid})")
            done += 1

        # ---- 2) CPU 우선순위 낮추기 ----
        for pid, name, cpu_pct in self.cpu_pids:
            self.progress_changed.emit(int(done / total_tasks * 100), f"CPU 우선순위 조정 중: {name}")
            if lower_process_priority(pid):
                cpu_deprioritized.append((pid, name))
                cpu_reclaimed_pct += cpu_pct
                write_log(f"CPU 우선순위 낮춤: {name} (PID {pid}, {cpu_pct}%)")
            else:
                write_log(f"CPU 우선순위 조정 실패(건너뜀): {name} (PID {pid})")
            done += 1

        # ---- 3) 임시 파일 휴지통 이동 ----
        for fpath in self.temp_files:
            self.progress_changed.emit(int(done / total_tasks * 100), "SSD 캐시 정리 중...")
            try:
                fsize = os.path.getsize(fpath)
            except Exception:
                fsize = 0
            if move_file_to_trash(fpath):
                files_deleted += 1
                bytes_deleted += fsize
                write_log(f"파일 휴지통 이동: {fpath} ({fsize} bytes)")
            done += 1

        # ---- 4) 브라우저 캐시 정리 ----
        for fpath in self.browser_files:
            self.progress_changed.emit(int(done / total_tasks * 100), "브라우저 캐시 정리 중...")
            try:
                fsize = os.path.getsize(fpath)
            except Exception:
                fsize = 0
            if move_file_to_trash(fpath):
                browser_files_deleted += 1
                browser_bytes_deleted += fsize
                write_log(f"브라우저 캐시 휴지통 이동: {fpath} ({fsize} bytes)")
            done += 1

        # ---- 5) DNS 캐시 초기화 ----
        if self.do_dns:
            self.progress_changed.emit(int(done / total_tasks * 100), "DNS 캐시 초기화 중...")
            success, msg = flush_dns()
            dns_result = success
            done += 1

        # ---- 6) GPU 정보 조회 (조치 없음, 정보만) ----
        self.progress_changed.emit(int(done / total_tasks * 100), "GPU 상태 확인 중...")
        gpu_info = scan_gpu_info() if self.do_gpu_scan else None
        done += 1
        self.progress_changed.emit(100, "완료")

        # [버그 수정] RAM 트림 후 OS가 메모리 통계를 갱신할 시간을 1.5초로 늘려서 부여
        time.sleep(1.5)
        mem_after = psutil.virtual_memory()
        cpu_after = psutil.cpu_percent(interval=0.3)

        report = {
            "ram_before_mb": round((mem_before.total - mem_before.available) / (1024 * 1024)),
            "ram_after_mb": round((mem_after.total - mem_after.available) / (1024 * 1024)),
            "ram_freed_mb": max(0, round((mem_after.available - mem_before.available) / (1024 * 1024))),
            "ram_trimmed_process_count": ram_trimmed_count,
            "cpu_before_pct": cpu_before,
            "cpu_after_pct": cpu_after,
            "cpu_reclaimed_pct": min(round(cpu_reclaimed_pct, 1), 100.0),
            "cpu_deprioritized": cpu_deprioritized,
            "disk_freed_bytes": bytes_deleted,
            "disk_freed_files": files_deleted,
            "browser_freed_bytes": browser_bytes_deleted,
            "browser_freed_files": browser_files_deleted,
            "dns_flushed": dns_result,
            "gpu_info": gpu_info,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.finished_report.emit(report)


def instant_cleanup_after_game_exit(previously_deprioritized, excluded_set=None):
    """게임 종료 감지 즉시 실행되는 자동 정리 (우선순위 원복 + RAM 즉시 트림)."""
    mem_before = psutil.virtual_memory()

    restored_count = 0
    for pid, name in previously_deprioritized:
        if restore_process_priority(pid):
            restored_count += 1
            write_log(f"[자동] 게임 종료 감지 - CPU 우선순위 원복: {name} (PID {pid})")

    ram_candidates = scan_ram_candidates(intensity=3, excluded_set=excluded_set) if IS_WINDOWS else []
    trimmed_count = 0
    for pid, name, mem_mb in ram_candidates:
        if trim_process_working_set(pid):
            trimmed_count += 1
            write_log(f"[자동] 게임 종료 감지 - RAM 즉시 트림: {name} (PID {pid}, {mem_mb}MB)")

    time.sleep(0.5)
    mem_after = psutil.virtual_memory()
    freed_mb = max(0, round((mem_after.available - mem_before.available) / (1024 * 1024)))

    return {"restored_count": restored_count, "trimmed_count": trimmed_count, "freed_mb": freed_mb}


# =====================================================================
# 5. 사전 점검 팝업
# =====================================================================
class PrecheckDialog(QDialog):
    def __init__(self, scan_result: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사전 점검 (실제 대상 목록)")
        self.setMinimumSize(580, 560)

        self.scan_result = scan_result
        self.ram_checkboxes = {}
        self.cpu_checkboxes = {}

        layout = QVBoxLayout(self)

        warn = QLabel(
            "⚠️ 아래는 실제로 조회된 대상입니다. 원치 않는 항목은 체크를 해제하세요.\n"
            "- RAM/CPU 항목: 프로세스를 종료하지 않고 메모리 트림 / 우선순위 조정만 합니다.\n"
            "- SSD·브라우저 캐시: 완전 삭제가 아니라 휴지통으로 이동합니다 (복구 가능)."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet("background:#332b00; color:#ffe58a; padding:10px; border-radius:6px;")
        layout.addWidget(warn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        ram_candidates = scan_result.get("ram_candidates", [])
        if ram_candidates:
            ram_box = QGroupBox(f"RAM 정리 대상 ({len(ram_candidates)}개 프로세스)")
            ram_layout = QVBoxLayout(ram_box)
            for pid, name, mem_mb in ram_candidates:
                cb = QCheckBox(f"{name}  (PID {pid}, {mem_mb} MB 사용 중)")
                cb.setChecked(True)
                self.ram_checkboxes[pid] = cb
                ram_layout.addWidget(cb)
            inner_layout.addWidget(ram_box)

        cpu_candidates = scan_result.get("cpu_candidates", [])
        if cpu_candidates:
            cpu_box = QGroupBox(f"CPU 우선순위 조정 대상 ({len(cpu_candidates)}개 프로세스)")
            cpu_layout = QVBoxLayout(cpu_box)
            for pid, name, cpu_pct in cpu_candidates:
                cb = QCheckBox(f"{name}  (PID {pid}, 시스템 전체 대비 CPU {cpu_pct}%)")
                cb.setChecked(True)
                self.cpu_checkboxes[pid] = cb
                cpu_layout.addWidget(cb)
            inner_layout.addWidget(cpu_box)

        temp_files = scan_result.get("temp_files", [])
        self.ssd_checkbox = None
        if temp_files:
            ssd_box = QGroupBox("SSD 캐시 정리 대상")
            ssd_layout = QVBoxLayout(ssd_box)
            size_mb = round(scan_result.get("temp_size", 0) / (1024 * 1024), 1)
            self.ssd_checkbox = QCheckBox(f"임시 파일 {len(temp_files)}개 (총 {size_mb} MB) - 휴지통으로 이동")
            self.ssd_checkbox.setChecked(True)
            ssd_layout.addWidget(self.ssd_checkbox)
            if not SEND2TRASH_AVAILABLE:
                note = QLabel("⚠️ send2trash 미설치로 실행할 수 없습니다. (pip install Send2Trash)")
                note.setStyleSheet("color:#ff8a8a;")
                ssd_layout.addWidget(note)
                self.ssd_checkbox.setChecked(False)
                self.ssd_checkbox.setEnabled(False)
            inner_layout.addWidget(ssd_box)

        browser_files = scan_result.get("browser_files", [])
        self.browser_checkbox = None
        if browser_files:
            b_box = QGroupBox("브라우저 캐시 정리 대상")
            b_layout = QVBoxLayout(b_box)
            b_size_mb = round(scan_result.get("browser_size", 0) / (1024 * 1024), 1)
            self.browser_checkbox = QCheckBox(
                f"Chrome/Edge 캐시 파일 {len(browser_files)}개 (총 {b_size_mb} MB) - 휴지통으로 이동"
            )
            self.browser_checkbox.setChecked(True)
            if not SEND2TRASH_AVAILABLE:
                self.browser_checkbox.setChecked(False)
                self.browser_checkbox.setEnabled(False)
            b_layout.addWidget(self.browser_checkbox)
            inner_layout.addWidget(b_box)

        self.dns_checkbox = None
        if scan_result.get("dns_selected"):
            dns_box = QGroupBox("네트워크")
            dns_layout = QVBoxLayout(dns_box)
            self.dns_checkbox = QCheckBox("DNS 캐시 초기화 (ipconfig /flushdns)")
            self.dns_checkbox.setChecked(True)
            dns_layout.addWidget(self.dns_checkbox)
            inner_layout.addWidget(dns_box)

        if scan_result.get("gpu_selected"):
            gpu_box = QGroupBox("GPU")
            gpu_layout = QVBoxLayout(gpu_box)
            if NVML_AVAILABLE:
                gpu_layout.addWidget(QLabel("GPU는 VRAM 사용량 '조회'만 수행합니다 (직접 조작하지 않음)."))
            else:
                gpu_layout.addWidget(QLabel("pynvml 미설치로 GPU 정보를 조회할 수 없습니다."))
            inner_layout.addWidget(gpu_box)

        if not (ram_candidates or cpu_candidates or temp_files or browser_files):
            inner_layout.addWidget(QLabel("정리할 대상이 발견되지 않았습니다. (이미 최적화된 상태일 수 있습니다)"))

        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("취소")
        cancel_btn.setObjectName("secondaryButton")
        confirm_btn = QPushButton("확인 및 최적화 진행")
        cancel_btn.clicked.connect(self.reject)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

    def get_selected(self):
        ram_candidates = self.scan_result.get("ram_candidates", [])
        cpu_candidates = self.scan_result.get("cpu_candidates", [])
        ram_selected = [c for c in ram_candidates if self.ram_checkboxes.get(c[0]) and self.ram_checkboxes[c[0]].isChecked()]
        cpu_selected = [c for c in cpu_candidates if self.cpu_checkboxes.get(c[0]) and self.cpu_checkboxes[c[0]].isChecked()]
        files_selected = self.scan_result.get("temp_files", []) if (self.ssd_checkbox and self.ssd_checkbox.isChecked()) else []
        browser_selected = self.scan_result.get("browser_files", []) if (self.browser_checkbox and self.browser_checkbox.isChecked()) else []
        dns_selected = bool(self.dns_checkbox and self.dns_checkbox.isChecked())
        return ram_selected, cpu_selected, files_selected, browser_selected, dns_selected


class ScanningDialog(QDialog):
    """스캔 중임을 보여주는 간단한 팝업 (진행률 대신 인디케이터만 표시, 취소 불가)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("스캔 중")
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("실제 시스템 상태를 스캔하고 있습니다..."))
        bar = QProgressBar()
        bar.setRange(0, 0)  # 인디케이터 모드 (불확정 진행률)
        layout.addWidget(bar)


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("최적화 진행 중")
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        layout = QVBoxLayout(self)
        self.status_label = QLabel("준비 중...")
        self.progress_bar = QProgressBar()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

    def update_progress(self, value, text):
        self.progress_bar.setValue(value)
        self.status_label.setText(text)


# =====================================================================
# 6. 플로팅 오버레이 위젯 (실시간 CPU/RAM 표시)
# =====================================================================
class OsdWidget(QWidget):
    """화면 구석에 떠 있는 작은 실시간 자원 표시 위젯. 드래그로 위치 이동 가능, 더블클릭으로 숨김."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(170, 54)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("CPU: --%   RAM: --%")
        self.label.setStyleSheet(
            "color:#63e6a3; background: rgba(20,20,28,210); border: 1px solid #34364a;"
            "border-radius:10px; padding:10px; font-weight:bold; font-size:10pt;"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self._drag_pos = None
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 200, 40)

    def update_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        self.label.setText(f"CPU: {cpu:.0f}%   RAM: {ram:.0f}%")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseDoubleClickEvent(self, event):
        self.hide()


# =====================================================================
# 7. 메인 윈도우
# =====================================================================

# =====================================================================
# [확장 기능] 블로트웨어 / 시작프로그램 / 성능튜닝 / 진단복구 / 디스크정리+
# (프로그램 기본 기능의 일부로 통합됨. 위쪽에서 이미 정의된 IS_WINDOWS,
#  WINREG_AVAILABLE, winreg, is_admin, write_log, load_settings,
#  save_settings, SEND2TRASH_AVAILABLE, send2trash 등을 그대로 재사용한다.)
# =====================================================================

def _run_cli(cmd, timeout=30, shell=False):
    """
    공용 CLI 실행 래퍼.
    [검증 3-5] 한글 Windows(CP949) 환경에서 UnicodeDecodeError가 나지 않도록
    encoding='utf-8', errors='ignore' 로 안전하게 디코딩한다.
    관리자 권한 부재/명령 없음 등은 모두 예외로 잡아 (False, 사유) 로 반환.
    """
    try:
        creationflags = 0x08000000 if IS_WINDOWS else 0  # CREATE_NO_WINDOW
        result = subprocess.run(
            cmd, capture_output=True, timeout=timeout, shell=shell,
            encoding="utf-8", errors="ignore",
            creationflags=creationflags if IS_WINDOWS else 0,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, out.strip()
    except FileNotFoundError:
        return False, "명령을 찾을 수 없습니다 (해당 기능이 이 시스템에 없을 수 있습니다)."
    except subprocess.TimeoutExpired:
        return False, "명령 실행 시간이 초과되었습니다."
    except Exception as e:
        return False, f"실행 오류: {e}"


def _reg_set(hive, path, name, value, vtype, create=True):
    """레지스트리 값 설정. 권한/경로 문제는 모두 예외로 잡아 안전하게 실패 반환."""
    if not WINREG_AVAILABLE:
        return False, "이 시스템에서는 레지스트리를 사용할 수 없습니다."
    try:
        access = winreg.KEY_ALL_ACCESS
        try:
            key = winreg.OpenKey(hive, path, 0, access)
        except FileNotFoundError:
            if not create:
                return False, "레지스트리 경로가 없습니다."
            key = winreg.CreateKey(hive, path)
        winreg.SetValueEx(key, name, 0, vtype, value)
        winreg.CloseKey(key)
        return True, "OK"
    except PermissionError:
        return False, "관리자 권한이 필요합니다."
    except Exception as e:
        return False, f"레지스트리 설정 실패: {e}"


def _reg_delete_value(hive, path, name):
    if not WINREG_AVAILABLE:
        return False, "이 시스템에서는 레지스트리를 사용할 수 없습니다."
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
        try:
            winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True, "OK"
    except PermissionError:
        return False, "관리자 권한이 필요합니다."
    except FileNotFoundError:
        return True, "OK"  # 이미 없으면 성공으로 간주
    except Exception as e:
        return False, f"레지스트리 삭제 실패: {e}"


# =====================================================================
# 1. 블로트웨어 & 앱 관리 (Debloat & Apps)
# =====================================================================

# 안전하게 제거해도 되는 것으로 알려진 대표 AppX(사용자 확인 후에만 삭제)
REMOVABLE_APPX_HINTS = [
    ("Cortana", "Microsoft.549981C3F5F10"),
    ("Xbox Game Bar / Overlay", "Microsoft.XboxGamingOverlay"),
    ("Xbox App", "Microsoft.GamingApp"),
    ("당신의 휴대폰(Your Phone/Link to Windows)", "Microsoft.YourPhone"),
    ("뉴스 및 관심사(News & Interests)", "Microsoft.BingNews"),
    ("날씨(Weather)", "Microsoft.BingWeather"),
    ("3D Viewer", "Microsoft.Microsoft3DViewer"),
    ("Mixed Reality Portal", "Microsoft.MixedReality.Portal"),
    ("Skype", "Microsoft.SkypeApp"),
    ("Solitaire Collection", "Microsoft.MicrosoftSolitaireCollection"),
    ("Get Help", "Microsoft.GetHelp"),
    ("Feedback Hub", "Microsoft.WindowsFeedbackHub"),
]

TELEMETRY_SERVICES = ["DiagTrack", "dmwappushservice"]


def list_installed_appx():
    """
    설치된 AppX 패키지 중 REMOVABLE_APPX_HINTS 에 해당하는 것만 골라 목록화.
    [검증 1] PowerShell 호출은 시간이 걸릴 수 있으므로 반드시 스레드에서 호출할 것.
    """
    if not IS_WINDOWS:
        return []
    ok, out = _run_cli(
        ["powershell", "-NoProfile", "-Command",
         "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
        timeout=30,
    )
    if not ok or not out:
        return []
    installed = [line.strip() for line in out.splitlines() if line.strip()]
    found = []
    for label, key in REMOVABLE_APPX_HINTS:
        match = next((p for p in installed if key.lower() in p.lower()), None)
        if match:
            found.append((label, match))
    return found


def remove_appx_package(full_name: str):
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    ok, out = _run_cli(
        ["powershell", "-NoProfile", "-Command",
         f"Remove-AppxPackage -Package \"{full_name}\" -ErrorAction Stop"],
        timeout=60,
    )
    write_log(f"AppX 제거 {'성공' if ok else '실패'}: {full_name} ({out[:200]})")
    return ok, (out or ("제거 완료" if ok else "제거 실패"))


def set_telemetry_disabled(disable: bool):
    """
    DiagTrack / dmwappushservice 서비스 비활성화 + AllowTelemetry 레지스트리 설정.
    관리자 권한 필요. 실패해도 프로그램이 죽지 않도록 각 단계 개별 try-except.
    """
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다. 프로그램을 관리자 권한으로 다시 실행해주세요."

    results = []
    for svc in TELEMETRY_SERVICES:
        start_mode = "disabled" if disable else "demand"
        ok, out = _run_cli(["sc", "config", svc, "start=", start_mode], timeout=15)
        results.append(f"{svc} 서비스 시작유형={start_mode}: {'성공' if ok else '실패(' + out[:80] + ')'}")
        if disable:
            _run_cli(["net", "stop", svc], timeout=15)

    if disable:
        ok, msg = _reg_set(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry", 0, winreg.REG_DWORD,
        ) if WINREG_AVAILABLE else (False, "레지스트리 미지원")
    else:
        ok, msg = _reg_delete_value(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry",
        ) if WINREG_AVAILABLE else (False, "레지스트리 미지원")
    results.append(f"AllowTelemetry 레지스트리: {msg}")

    write_log(f"텔레메트리 {'차단' if disable else '복원'} 적용: {' / '.join(results)}")
    return True, "\n".join(results)


class AppxDebloatThread(QThread):
    """AppX 스캔/제거를 백그라운드에서 수행 (UI 프리징 방지)."""
    scan_done = pyqtSignal(list)
    remove_progress = pyqtSignal(int, str)
    remove_done = pyqtSignal(list)  # [(label, ok, msg), ...]

    def __init__(self, mode: str, targets=None, parent=None):
        super().__init__(parent)
        self.mode = mode  # "scan" or "remove"
        self.targets = targets or []  # [(label, full_name), ...]

    def run(self):
        if self.mode == "scan":
            try:
                found = list_installed_appx()
            except Exception as e:
                write_log(f"AppX 스캔 오류: {e}")
                found = []
            self.scan_done.emit(found)
        else:
            results = []
            total = max(len(self.targets), 1)
            for i, (label, full_name) in enumerate(self.targets):
                self.remove_progress.emit(int(i / total * 100), f"제거 중: {label}")
                try:
                    ok, msg = remove_appx_package(full_name)
                except Exception as e:
                    ok, msg = False, str(e)
                results.append((label, ok, msg))
            self.remove_done.emit(results)


# =====================================================================
# 2. 시작 프로그램 관리 (Startup Manager)
# =====================================================================
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_DISABLED_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run_OptiCoreDisabled"


def _startup_folder_path():
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return None
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def list_startup_items():
    """
    HKCU\\...\\Run, HKLM\\...\\Run 및 사용자 시작프로그램 폴더를 스캔한다.
    반환: [{"source": "HKCU"/"HKLM"/"Folder", "name": str, "command": str, "enabled": bool}]
    """
    items = []
    if WINREG_AVAILABLE:
        for hive, hive_name in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
            for key_path, enabled in ((RUN_KEY_PATH, True), (RUN_DISABLED_KEY_PATH, False)):
                try:
                    key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
                except Exception:
                    continue
                try:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                        except OSError:
                            break
                        i += 1
                        items.append({
                            "source": hive_name, "name": name, "command": str(value),
                            "enabled": enabled, "key_path": key_path,
                        })
                except Exception:
                    pass
                finally:
                    try:
                        winreg.CloseKey(key)
                    except Exception:
                        pass

    folder = _startup_folder_path()
    if folder and os.path.isdir(folder):
        try:
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    items.append({
                        "source": "Folder", "name": fname, "command": fpath,
                        "enabled": True, "key_path": folder,
                    })
        except Exception:
            pass
    return items


def toggle_startup_item(item: dict, enable: bool):
    """
    레지스트리 항목은 Run <-> Run_OptiCoreDisabled 사이로 값을 이동해 되돌릴 수 있게 처리.
    폴더 항목은 파일명 앞에 'disabled_' 접두어를 붙였다 떼는 방식으로 토글.
    """
    try:
        if item["source"] in ("HKCU", "HKLM"):
            if not WINREG_AVAILABLE:
                return False, "레지스트리를 사용할 수 없습니다."
            hive = winreg.HKEY_CURRENT_USER if item["source"] == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            src_path = RUN_KEY_PATH if not enable else RUN_DISABLED_KEY_PATH
            dst_path = RUN_DISABLED_KEY_PATH if not enable else RUN_KEY_PATH
            try:
                src_key = winreg.OpenKey(hive, src_path, 0, winreg.KEY_ALL_ACCESS)
                value, vtype = winreg.QueryValueEx(src_key, item["name"])[0], winreg.REG_SZ
                winreg.CloseKey(src_key)
            except Exception as e:
                return False, f"원본 값을 읽지 못했습니다: {e}"

            ok, msg = _reg_set(hive, dst_path, item["name"], value, winreg.REG_SZ)
            if not ok:
                return False, msg
            _reg_delete_value(hive, src_path, item["name"])
            write_log(f"시작프로그램 {'활성화' if enable else '비활성화'}: {item['name']}")
            return True, "완료"

        elif item["source"] == "Folder":
            folder = os.path.dirname(item["command"]) if not item["command"].startswith(_startup_folder_path() or "") else _startup_folder_path()
            base = os.path.basename(item["command"])
            if enable and base.startswith("disabled_"):
                new_path = os.path.join(folder, base[len("disabled_"):])
                os.rename(item["command"], new_path)
            elif not enable and not base.startswith("disabled_"):
                new_path = os.path.join(folder, "disabled_" + base)
                os.rename(item["command"], new_path)
            write_log(f"시작프로그램(폴더) {'활성화' if enable else '비활성화'}: {base}")
            return True, "완료"
        return False, "알 수 없는 항목 유형입니다."
    except PermissionError:
        return False, "권한이 없습니다. 관리자 권한으로 다시 실행해주세요."
    except Exception as e:
        return False, f"처리 실패: {e}"


def delete_startup_item(item: dict):
    try:
        if item["source"] in ("HKCU", "HKLM"):
            if not WINREG_AVAILABLE:
                return False, "레지스트리를 사용할 수 없습니다."
            hive = winreg.HKEY_CURRENT_USER if item["source"] == "HKCU" else winreg.HKEY_LOCAL_MACHINE
            ok, msg = _reg_delete_value(hive, item["key_path"], item["name"])
            if ok:
                write_log(f"시작프로그램 삭제: {item['name']}")
            return ok, msg
        elif item["source"] == "Folder":
            if SEND2TRASH_AVAILABLE:
                send2trash(item["command"])
            else:
                os.remove(item["command"])
            write_log(f"시작프로그램(바로가기) 삭제: {item['name']}")
            return True, "완료"
        return False, "알 수 없는 항목 유형입니다."
    except PermissionError:
        return False, "권한이 없습니다."
    except FileNotFoundError:
        return True, "이미 삭제됨"
    except Exception as e:
        return False, f"삭제 실패: {e}"


def open_in_explorer(path: str):
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    try:
        target = path if os.path.isdir(path) else os.path.dirname(path)
        if os.path.isfile(path):
            subprocess.run(["explorer", "/select,", path], creationflags=0x08000000)
        elif os.path.isdir(target):
            subprocess.run(["explorer", target], creationflags=0x08000000)
        else:
            return False, "경로를 찾을 수 없습니다."
        return True, "탐색기를 열었습니다."
    except Exception as e:
        return False, f"탐색기 열기 실패: {e}"


class StartupScanThread(QThread):
    scan_done = pyqtSignal(list)

    def run(self):
        try:
            items = list_startup_items()
        except Exception as e:
            write_log(f"시작프로그램 스캔 오류: {e}")
            items = []
        self.scan_done.emit(items)


# =====================================================================
# 3. 성능 & 게이밍 최적화 (Performance & Network Tweaks)
# =====================================================================
def set_network_gaming_priority(enable: bool):
    """NetworkThrottlingIndex / SystemResponsiveness 게임 우선 배정. 관리자 권한 필요."""
    if not IS_WINDOWS or not WINREG_AVAILABLE:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    results = []
    if enable:
        ok1, m1 = _reg_set(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 0xFFFFFFFF, winreg.REG_DWORD)
        ok2, m2 = _reg_set(winreg.HKEY_LOCAL_MACHINE, path, "SystemResponsiveness", 0, winreg.REG_DWORD)
    else:
        ok1, m1 = _reg_set(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 10, winreg.REG_DWORD)
        ok2, m2 = _reg_set(winreg.HKEY_LOCAL_MACHINE, path, "SystemResponsiveness", 20, winreg.REG_DWORD)
    results = [m1, m2]
    ok = ok1 and ok2
    write_log(f"네트워크 게임 우선순위 {'적용' if enable else '복원'}: {ok}")
    return ok, ("적용 완료" if ok else " / ".join(results))


def set_high_res_timer(enable: bool):
    """고해상도 타이머(bcdedit). 관리자 권한 + 재부팅 필요."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    if not is_admin():
        return False, "관리자 권한이 필요합니다."
    ok1, out1 = _run_cli(["bcdedit", "/set", "useplatformclock", "false" if enable else "true"])
    ok2, out2 = _run_cli(["bcdedit", "/set", "disabledynamictick", "yes" if enable else "no"])
    ok = ok1 or ok2
    write_log(f"고해상도 타이머 {'적용' if enable else '복원'}: {out1[:100]} / {out2[:100]}")
    return ok, "설정을 반영했습니다. 재부팅 후 적용됩니다." if ok else f"{out1}\n{out2}"


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


class PerfTweakThread(QThread):
    """성능 튜닝 항목을 순차 적용(각 항목 실패해도 다음 항목 계속 진행)."""
    progress_changed = pyqtSignal(int, str)
    finished_report = pyqtSignal(list)  # [(label, ok, msg), ...]

    def __init__(self, tasks: list, parent=None):
        super().__init__(parent)
        # tasks: [(label, callable), ...]
        self.tasks = tasks

    def run(self):
        results = []
        total = max(len(self.tasks), 1)
        for i, (label, func) in enumerate(self.tasks):
            self.progress_changed.emit(int(i / total * 100), f"적용 중: {label}")
            try:
                ok, msg = func()
            except Exception as e:
                ok, msg = False, str(e)
            results.append((label, ok, msg))
        self.finished_report.emit(results)


# =====================================================================
# 4. 시스템 검사 & 백업 (Diagnostics & Restoration)
# =====================================================================
def open_admin_terminal(command: str, title: str):
    """sfc/DISM 등을 별도 관리자 권한 터미널 창으로 실행."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다."
    try:
        ps_cmd = (
            f"Start-Process cmd -ArgumentList '/k {command}' -Verb RunAs"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=15, encoding="utf-8", errors="ignore",
        )
        write_log(f"관리자 터미널 실행: {title} ({command})")
        return True, "관리자 권한 확인창(UAC)이 뜨면 [예]를 눌러 진행하세요."
    except Exception as e:
        return False, f"실행 실패: {e}"


def run_sfc_scan():
    return open_admin_terminal("sfc /scannow", "SFC 무결성 검사")


def run_dism_scan():
    return open_admin_terminal("DISM /Online /Cleanup-Image /RestoreHealth", "DISM 이미지 복구")


def restore_all_defaults(settings: dict):
    """
    본 모듈로 변경된 설정을 윈도우 기본값으로 일괄 복원한다.
    settings["applied_tweaks"] 에 기록된 항목만 되돌리고, 실패한 항목은
    건너뛰되 전체 목록을 결과로 반환한다 (부분 실패해도 나머지는 계속 진행).
    """
    if not IS_WINDOWS:
        return [("환경", False, "Windows 전용 기능입니다.")]
    if not is_admin():
        return [("권한", False, "관리자 권한이 필요합니다.")]

    results = []
    try:
        ok, msg = set_network_gaming_priority(False)
        results.append(("네트워크 게임 우선순위 복원", ok, msg))
    except Exception as e:
        results.append(("네트워크 게임 우선순위 복원", False, str(e)))

    try:
        ok, msg = set_priority_separation(False)
        results.append(("CPU 스케줄링 기본값 복원", ok, msg))
    except Exception as e:
        results.append(("CPU 스케줄링 기본값 복원", False, str(e)))

    try:
        ok, msg = set_high_res_timer(False)
        results.append(("고해상도 타이머 복원", ok, msg))
    except Exception as e:
        results.append(("고해상도 타이머 복원", False, str(e)))

    try:
        ok, msg = set_visual_effects_performance(False)
        results.append(("시각 효과 복원", ok, msg))
    except Exception as e:
        results.append(("시각 효과 복원", False, str(e)))

    try:
        ok, msg = set_game_dvr_disabled(False)
        results.append(("Game DVR 복원", ok, msg))
    except Exception as e:
        results.append(("Game DVR 복원", False, str(e)))

    try:
        ok, msg = set_telemetry_disabled(False)
        results.append(("텔레메트리 복원", ok, msg))
    except Exception as e:
        results.append(("텔레메트리 복원", False, str(e)))

    settings["applied_tweaks"] = []
    save_settings(settings)
    write_log("전체 설정 순정 복원 실행 완료")
    return results


class RestoreDefaultsThread(QThread):
    finished_report = pyqtSignal(list)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings

    def run(self):
        try:
            results = restore_all_defaults(self.settings)
        except Exception as e:
            results = [("복원", False, str(e))]
        self.finished_report.emit(results)


# =====================================================================
# 5. 디스크 정리 확장 (Windows Update 캐시 / Prefetch / Brave / 휴지통)
# =====================================================================
def get_extra_cleanup_targets():
    """추가 정리 대상 폴더 목록 (관리자 권한이 필요한 폴더는 표시만 하고, 실제 삭제 시 확인)."""
    targets = []
    windir = os.environ.get("WINDIR", r"C:\Windows")
    targets.append(("Windows Update 캐시", os.path.join(windir, "SoftwareDistribution", "Download"), True))
    targets.append(("Prefetch", os.path.join(windir, "Prefetch"), True))
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        targets.append(("Brave 브라우저 캐시", os.path.join(
            local_appdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache"), False))
    return [(label, path, need_admin) for label, path, need_admin in targets if os.path.isdir(path)]


def scan_folder_size(path: str):
    """폴더 내 파일 목록과 총 용량(바이트)을 스캔. 권한 오류는 건너뛰고 계속 진행."""
    files = []
    total = 0
    try:
        for root, dirs, fnames in os.walk(path):
            for fname in fnames:
                fpath = os.path.join(root, fname)
                try:
                    if os.path.islink(fpath):
                        continue
                    size = os.path.getsize(fpath)
                    files.append(fpath)
                    total += size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
    except Exception:
        pass
    return files, total


def clean_windows_update_cache():
    """SoftwareDistribution\\Download 비우기: wuauserv 정지 -> 삭제 -> 재시작. 관리자 권한 필요."""
    if not IS_WINDOWS:
        return False, "Windows 전용 기능입니다.", 0
    if not is_admin():
        return False, "관리자 권한이 필요합니다.", 0
    windir = os.environ.get("WINDIR", r"C:\Windows")
    target = os.path.join(windir, "SoftwareDistribution", "Download")

    _run_cli(["net", "stop", "wuauserv"], timeout=20)
    files, total = scan_folder_size(target)
    deleted = 0
    for fpath in files:
        try:
            os.remove(fpath)
            deleted += 1
        except Exception:
            continue
    _run_cli(["net", "start", "wuauserv"], timeout=20)
    write_log(f"Windows Update 캐시 정리: {deleted}/{len(files)}개 삭제, 약 {total // (1024*1024)}MB")
    return True, f"{deleted}개 파일 삭제 (약 {total // (1024*1024)}MB)", total


class ExtraCleanScanThread(QThread):
    scan_done = pyqtSignal(list)  # [(label, path, need_admin, files, size), ...]

    def run(self):
        results = []
        try:
            for label, path, need_admin in get_extra_cleanup_targets():
                files, size = scan_folder_size(path)
                results.append((label, path, need_admin, files, size))
        except Exception as e:
            write_log(f"추가 정리 스캔 오류: {e}")
        self.scan_done.emit(results)


class ExtraCleanRunThread(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_report = pyqtSignal(list)  # [(label, ok, msg), ...]

    def __init__(self, selected: list, parent=None):
        super().__init__(parent)
        # selected: [(label, path, need_admin, files), ...]
        self.selected = selected

    def run(self):
        results = []
        total = max(len(self.selected), 1)
        for i, (label, path, need_admin, files) in enumerate(self.selected):
            self.progress_changed.emit(int(i / total * 100), f"정리 중: {label}")
            try:
                if "Windows Update" in label:
                    ok, msg, _ = clean_windows_update_cache()
                else:
                    deleted = 0
                    for fpath in files:
                        try:
                            if SEND2TRASH_AVAILABLE:
                                send2trash(fpath)
                            else:
                                os.remove(fpath)
                            deleted += 1
                        except Exception:
                            continue
                    ok, msg = True, f"{deleted}/{len(files)}개 항목 정리 완료"
                    write_log(f"추가 정리[{label}]: {msg}")
            except Exception as e:
                ok, msg = False, str(e)
            results.append((label, ok, msg))
        self.finished_report.emit(results)


# =====================================================================
# 6. 탭 UI 빌더 (MainWindow에 믹스인으로 결합)
# =====================================================================
class ExtendedFeaturesMixin:
    """
    MainWindow(QMainWindow) 에 다중 상속으로 결합해서 쓰는 믹스인.
    self.settings / self.excluded_set / self.add_history_entry 등
    기존 MainWindow 의 속성/메서드를 그대로 활용한다.
    """

    # ---------------- 공통 유틸 ----------------
    def _lut_confirm(self, text: str) -> bool:
        return QMessageBox.question(
            self, "확인", text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes

    def _lut_track_tweak(self, name: str):
        applied = self.settings.setdefault("applied_tweaks", [])
        if name not in applied:
            applied.append(name)
        save_settings(self.settings)

    # ---------------- Tab: 블로트웨어 & 앱 관리 ----------------
    def build_tab_debloat(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        box = QGroupBox("🧹 Windows 기본 탑재 앱 제거")
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(QLabel("스캔 후 제거할 앱을 선택하세요. (삭제는 되돌릴 수 없습니다)"))
        self.debloat_list = QListWidget()
        self.debloat_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        box_layout.addWidget(self.debloat_list)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("스캔")
        scan_btn.clicked.connect(self.on_debloat_scan)
        remove_btn = QPushButton("선택 항목 제거")
        remove_btn.setObjectName("secondaryButton")
        remove_btn.clicked.connect(self.on_debloat_remove)
        btn_row.addWidget(scan_btn)
        btn_row.addWidget(remove_btn)
        box_layout.addLayout(btn_row)

        self.debloat_progress = QProgressBar()
        self.debloat_progress.setValue(0)
        box_layout.addWidget(self.debloat_progress)
        layout.addWidget(box)

        tel_box = QGroupBox("📡 텔레메트리(사용정보 수집) 차단")
        tel_layout = QVBoxLayout(tel_box)
        tel_layout.addWidget(QLabel(
            "DiagTrack / dmwappushservice 서비스를 비활성화하고,\n"
            "AllowTelemetry 레지스트리 값을 0으로 설정합니다. (관리자 권한 필요)"
        ))
        tel_status = "차단됨" if self.settings.get("telemetry_disabled") else "기본값"
        self.telemetry_status_label = QLabel(f"현재 상태: {tel_status}")
        tel_layout.addWidget(self.telemetry_status_label)
        tel_btn_row = QHBoxLayout()
        tel_off_btn = QPushButton("텔레메트리 차단")
        tel_off_btn.clicked.connect(lambda: self.on_telemetry_toggle(True))
        tel_on_btn = QPushButton("기본값 복원")
        tel_on_btn.setObjectName("secondaryButton")
        tel_on_btn.clicked.connect(lambda: self.on_telemetry_toggle(False))
        tel_btn_row.addWidget(tel_off_btn)
        tel_btn_row.addWidget(tel_on_btn)
        tel_layout.addLayout(tel_btn_row)
        layout.addWidget(tel_box)

        layout.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(tab)
        outer.addWidget(scroll)
        self._debloat_thread = None
        return tab

    def on_debloat_scan(self):
        if not IS_WINDOWS:
            QMessageBox.information(self, "안내", "Windows 전용 기능입니다.")
            return
        self.debloat_list.clear()
        self._debloat_thread = AppxDebloatThread(mode="scan")
        self._debloat_thread.scan_done.connect(self._on_debloat_scan_done)
        self._debloat_thread.start()

    def _on_debloat_scan_done(self, found):
        self.debloat_list.clear()
        if not found:
            QMessageBox.information(self, "스캔 완료", "제거 가능한 앱을 찾지 못했습니다(이미 없거나 지원 목록 밖).")
            return
        for label, full_name in found:
            item = QListWidgetItem(f"{label}  —  {full_name}")
            item.setData(Qt.ItemDataRole.UserRole, (label, full_name))
            self.debloat_list.addItem(item)

    def on_debloat_remove(self):
        selected = self.debloat_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "안내", "제거할 앱을 목록에서 선택하세요.")
            return
        if not self._lut_confirm(f"선택한 {len(selected)}개 앱을 제거하시겠습니까?"):
            return
        targets = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        self._debloat_thread = AppxDebloatThread(mode="remove", targets=targets)
        self._debloat_thread.remove_progress.connect(
            lambda pct, msg: (self.debloat_progress.setValue(pct))
        )
        self._debloat_thread.remove_done.connect(self._on_debloat_remove_done)
        self._debloat_thread.start()

    def _on_debloat_remove_done(self, results):
        self.debloat_progress.setValue(100)
        ok_count = sum(1 for _, ok, _ in results if ok)
        for label, ok, msg in results:
            if hasattr(self, "add_history_entry") and ok:
                self.add_history_entry(f"앱 제거: {label}", None)
        QMessageBox.information(self, "완료", f"{ok_count}/{len(results)}개 앱을 제거했습니다.")
        self.on_debloat_scan()

    def on_telemetry_toggle(self, disable: bool):
        if not is_admin():
            QMessageBox.warning(self, "관리자 권한 필요", "관리자 권한으로 프로그램을 다시 실행해주세요.")
            return
        if not self._lut_confirm(("텔레메트리를 차단" if disable else "기본값으로 복원") + "하시겠습니까?"):
            return
        ok, msg = set_telemetry_disabled(disable)
        if ok:
            self.settings["telemetry_disabled"] = disable
            save_settings(self.settings)
            self.telemetry_status_label.setText(f"현재 상태: {'차단됨' if disable else '기본값'}")
            if disable:
                self._lut_track_tweak("telemetry")
            if hasattr(self, "add_history_entry"):
                self.add_history_entry(f"텔레메트리 {'차단' if disable else '복원'}", None)
        QMessageBox.information(self, "결과", msg)

    # ---------------- Tab: 시작 프로그램 관리 ----------------
    def build_tab_startup(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("자동 실행 항목(레지스트리 Run 키 + 시작프로그램 폴더)을 관리합니다."))

        self.startup_list = QListWidget()
        self.startup_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.startup_list)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("스캔")
        scan_btn.clicked.connect(self.on_startup_scan)
        toggle_btn = QPushButton("활성/비활성 전환")
        toggle_btn.clicked.connect(self.on_startup_toggle)
        delete_btn = QPushButton("삭제")
        delete_btn.setObjectName("secondaryButton")
        delete_btn.clicked.connect(self.on_startup_delete)
        open_btn = QPushButton("파일 위치 열기")
        open_btn.setObjectName("secondaryButton")
        open_btn.clicked.connect(self.on_startup_open_location)
        for b in (scan_btn, toggle_btn, delete_btn, open_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self._startup_items = []
        self._startup_thread = None
        return tab

    def on_startup_scan(self):
        if not IS_WINDOWS:
            QMessageBox.information(self, "안내", "Windows 전용 기능입니다.")
            return
        self.startup_list.clear()
        self._startup_thread = StartupScanThread()
        self._startup_thread.scan_done.connect(self._on_startup_scan_done)
        self._startup_thread.start()

    def _on_startup_scan_done(self, items):
        self._startup_items = items
        self.startup_list.clear()
        for it in items:
            status = "🟢 사용" if it["enabled"] else "⚪ 사용안함"
            display = f"[{it['source']}] {it['name']}  ({status})  — {it['command'][:70]}"
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.ItemDataRole.UserRole, it)
            self.startup_list.addItem(list_item)
        if not items:
            QMessageBox.information(self, "스캔 완료", "자동 실행 항목을 찾지 못했습니다.")

    def _selected_startup_item(self):
        sel = self.startup_list.selectedItems()
        if not sel:
            QMessageBox.information(self, "안내", "항목을 하나 선택하세요.")
            return None
        return sel[0].data(Qt.ItemDataRole.UserRole)

    def on_startup_toggle(self):
        item = self._selected_startup_item()
        if not item:
            return
        ok, msg = toggle_startup_item(item, enable=not item["enabled"])
        QMessageBox.information(self, "결과", msg)
        if ok and hasattr(self, "add_history_entry"):
            self.add_history_entry(f"시작프로그램 {'활성화' if not item['enabled'] else '비활성화'}: {item['name']}", None)
        self.on_startup_scan()

    def on_startup_delete(self):
        item = self._selected_startup_item()
        if not item:
            return
        if not self._lut_confirm(f"'{item['name']}' 항목을 삭제하시겠습니까?"):
            return
        ok, msg = delete_startup_item(item)
        QMessageBox.information(self, "결과", msg)
        if ok and hasattr(self, "add_history_entry"):
            self.add_history_entry(f"시작프로그램 삭제: {item['name']}", None)
        self.on_startup_scan()

    def on_startup_open_location(self):
        item = self._selected_startup_item()
        if not item:
            return
        ok, msg = open_in_explorer(item["command"])
        if not ok:
            QMessageBox.information(self, "안내", msg)

    # ---------------- Tab: 성능 & 게이밍 최적화 ----------------
    def build_tab_perf_tweaks(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        box = QGroupBox("🎮 게이밍 성능 튜닝 (관리자 권한 필요, 일부는 재부팅 후 적용)")
        box_layout = QVBoxLayout(box)

        self.cb_net_priority = QCheckBox("네트워크/CPU 게임 우선 배정 (NetworkThrottlingIndex, SystemResponsiveness)")
        self.cb_high_res_timer = QCheckBox("고해상도 타이머 사용 (bcdedit, 재부팅 필요)")
        self.cb_priority_sep = QCheckBox("포그라운드 앱 우선 CPU 스케줄링 (Win32PrioritySeparation)")
        self.cb_visual_fx = QCheckBox("시각 효과 최소화 (성능 우선)")
        self.cb_game_dvr = QCheckBox("Game DVR 비활성화")
        for cb in (self.cb_net_priority, self.cb_high_res_timer, self.cb_priority_sep,
                   self.cb_visual_fx, self.cb_game_dvr):
            box_layout.addWidget(cb)

        apply_btn = QPushButton("선택 항목 일괄 적용")
        apply_btn.clicked.connect(self.on_apply_perf_tweaks)
        box_layout.addWidget(apply_btn)

        self.perf_progress = QProgressBar()
        self.perf_progress.setValue(0)
        box_layout.addWidget(self.perf_progress)
        layout.addWidget(box)

        power_box = QGroupBox("⚡ 전원 옵션")
        power_layout = QVBoxLayout(power_box)
        power_btn = QPushButton("'최고의 성능' 전원 옵션 생성 및 적용")
        power_btn.clicked.connect(self.on_create_ultimate_power_plan)
        power_layout.addWidget(power_btn)
        layout.addWidget(power_box)

        dns_box = QGroupBox("🌐 DNS 캐시")
        dns_layout = QVBoxLayout(dns_box)
        dns_btn = QPushButton("DNS 캐시 플러시 (ipconfig /flushdns)")
        dns_btn.clicked.connect(self.on_flush_dns_perf_tab)
        dns_layout.addWidget(dns_btn)
        layout.addWidget(dns_box)

        layout.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(tab)
        outer.addWidget(scroll)
        self._perf_thread = None
        return tab

    def on_apply_perf_tweaks(self):
        if not is_admin():
            QMessageBox.warning(self, "관리자 권한 필요", "관리자 권한으로 프로그램을 다시 실행해주세요.")
            return
        tasks = []
        if self.cb_net_priority.isChecked():
            tasks.append(("네트워크/CPU 게임 우선 배정", lambda: set_network_gaming_priority(True)))
        if self.cb_high_res_timer.isChecked():
            tasks.append(("고해상도 타이머", lambda: set_high_res_timer(True)))
        if self.cb_priority_sep.isChecked():
            tasks.append(("CPU 스케줄링(포그라운드 우선)", lambda: set_priority_separation(True)))
        if self.cb_visual_fx.isChecked():
            tasks.append(("시각 효과 최소화", lambda: set_visual_effects_performance(True)))
        if self.cb_game_dvr.isChecked():
            tasks.append(("Game DVR 비활성화", lambda: set_game_dvr_disabled(True)))

        if not tasks:
            QMessageBox.information(self, "안내", "적용할 항목을 선택하세요.")
            return
        if not self._lut_confirm(f"선택한 {len(tasks)}개 항목을 적용하시겠습니까? 시스템 설정이 변경됩니다."):
            return

        self._perf_thread = PerfTweakThread(tasks)
        self._perf_thread.progress_changed.connect(
            lambda pct, msg: self.perf_progress.setValue(pct)
        )
        self._perf_thread.finished_report.connect(self._on_perf_tweaks_done)
        self._perf_thread.start()

    def _on_perf_tweaks_done(self, results):
        self.perf_progress.setValue(100)
        lines = []
        for label, ok, msg in results:
            lines.append(f"{'✅' if ok else '❌'} {label}: {msg[:80]}")
            if ok:
                self._lut_track_tweak(label)
                if hasattr(self, "add_history_entry"):
                    self.add_history_entry(f"성능 튜닝 적용: {label}", None)
        QMessageBox.information(self, "적용 결과", "\n".join(lines))

    def on_create_ultimate_power_plan(self):
        if not self._lut_confirm("'최고의 성능' 전원 옵션을 생성하고 적용하시겠습니까?"):
            return
        ok, msg = create_ultimate_performance_plan()
        QMessageBox.information(self, "결과", msg)
        if ok and hasattr(self, "add_history_entry"):
            self.add_history_entry("최고의 성능 전원 옵션 적용", None)

    def on_flush_dns_perf_tab(self):
        # [버그 수정 v1.0.1] 파일명을 하드코딩해 자기 자신을 import하던 방식은
        # 파일명이 바뀌면(main_real__2_.py -> OptiCore_V1.0.py) 항상 실패하는 구조였습니다.
        # 이 파일 안에 이미 정의되어 있는 flush_dns()를 바로 호출하도록 수정했습니다.
        ok, msg = flush_dns()
        QMessageBox.information(self, "결과", msg or ("완료" if ok else "실패"))

    # ---------------- Tab: 진단 & 복원 ----------------
    def build_tab_diagnostics(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("🩺 시스템 무결성 검사")
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(QLabel("별도의 관리자 권한 터미널 창에서 안전하게 실행됩니다."))
        sfc_btn = QPushButton("sfc /scannow 실행")
        sfc_btn.clicked.connect(self.on_run_sfc)
        dism_btn = QPushButton("DISM 이미지 복구 실행")
        dism_btn.clicked.connect(self.on_run_dism)
        box_layout.addWidget(sfc_btn)
        box_layout.addWidget(dism_btn)
        layout.addWidget(box)

        restore_box = QGroupBox("🔁 원클릭 순정 복원")
        restore_layout = QVBoxLayout(restore_box)
        restore_layout.addWidget(QLabel(
            "본 프로그램으로 변경한 레지스트리/네트워크/서비스 설정을 기본값으로 되돌립니다.\n"
            "(관리자 권한 필요)"
        ))
        restore_btn = QPushButton("모든 설정 순정 복원")
        restore_btn.setObjectName("secondaryButton")
        restore_btn.clicked.connect(self.on_restore_defaults)
        restore_layout.addWidget(restore_btn)
        self.restore_progress = QProgressBar()
        self.restore_progress.setRange(0, 0)
        self.restore_progress.setVisible(False)
        restore_layout.addWidget(self.restore_progress)
        layout.addWidget(restore_box)

        layout.addStretch()
        self._restore_thread = None
        return tab

    def on_run_sfc(self):
        if not self._lut_confirm("sfc /scannow 를 관리자 권한 터미널에서 실행하시겠습니까?"):
            return
        ok, msg = run_sfc_scan()
        QMessageBox.information(self, "결과", msg)

    def on_run_dism(self):
        if not self._lut_confirm("DISM 이미지 복구를 관리자 권한 터미널에서 실행하시겠습니까? (시간이 오래 걸릴 수 있습니다)"):
            return
        ok, msg = run_dism_scan()
        QMessageBox.information(self, "결과", msg)

    def on_restore_defaults(self):
        if not self._lut_confirm("본 프로그램으로 변경한 모든 설정을 기본값으로 되돌리시겠습니까?"):
            return
        self.restore_progress.setVisible(True)
        self._restore_thread = RestoreDefaultsThread(self.settings)
        self._restore_thread.finished_report.connect(self._on_restore_defaults_done)
        self._restore_thread.start()

    def _on_restore_defaults_done(self, results):
        self.restore_progress.setVisible(False)
        lines = [f"{'✅' if ok else '❌'} {label}: {msg[:80]}" for label, ok, msg in results]
        QMessageBox.information(self, "복원 결과", "\n".join(lines))
        if hasattr(self, "add_history_entry"):
            self.add_history_entry("전체 설정 순정 복원", None)

    # ---------------- Tab: 디스크 정리 확장 ----------------
    def build_tab_cleaner_plus(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(
            "Windows Update 캐시 / Prefetch / Brave 캐시 등 추가 정리 대상을 스캔합니다.\n"
            "Windows Update 캐시와 Prefetch는 관리자 권한이 필요합니다."
        ))

        self.extra_clean_list = QListWidget()
        self.extra_clean_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        layout.addWidget(self.extra_clean_list)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("스캔")
        scan_btn.clicked.connect(self.on_extra_clean_scan)
        clean_btn = QPushButton("선택 항목 정리")
        clean_btn.setObjectName("secondaryButton")
        clean_btn.clicked.connect(self.on_extra_clean_run)
        btn_row.addWidget(scan_btn)
        btn_row.addWidget(clean_btn)
        layout.addLayout(btn_row)

        self.extra_clean_progress = QProgressBar()
        self.extra_clean_progress.setValue(0)
        layout.addWidget(self.extra_clean_progress)

        self._extra_clean_data = []
        self._extra_clean_thread = None
        return tab

    def on_extra_clean_scan(self):
        if not IS_WINDOWS:
            QMessageBox.information(self, "안내", "Windows 전용 기능입니다.")
            return
        self.extra_clean_list.clear()
        self._extra_clean_thread = ExtraCleanScanThread()
        self._extra_clean_thread.scan_done.connect(self._on_extra_clean_scan_done)
        self._extra_clean_thread.start()

    def _on_extra_clean_scan_done(self, results):
        self._extra_clean_data = results
        self.extra_clean_list.clear()
        if not results:
            QMessageBox.information(self, "스캔 완료", "정리할 대상을 찾지 못했습니다.")
            return
        for label, path, need_admin, files, size in results:
            mb = size / (1024 * 1024)
            admin_tag = " [관리자 권한 필요]" if need_admin else ""
            item = QListWidgetItem(f"{label}{admin_tag}  —  {len(files)}개 파일, {mb:.1f}MB")
            item.setData(Qt.ItemDataRole.UserRole, (label, path, need_admin, files))
            self.extra_clean_list.addItem(item)

    def on_extra_clean_run(self):
        selected = self.extra_clean_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "안내", "정리할 항목을 선택하세요.")
            return
        targets = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        if any(need_admin for _, _, need_admin, _ in targets) and not is_admin():
            QMessageBox.warning(self, "관리자 권한 필요",
                                 "선택 항목 중 관리자 권한이 필요한 항목이 있습니다.\n"
                                 "프로그램을 관리자 권한으로 다시 실행해주세요.")
            return
        if not self._lut_confirm(f"선택한 {len(targets)}개 항목을 정리하시겠습니까?"):
            return
        self._extra_clean_thread = ExtraCleanRunThread(targets)
        self._extra_clean_thread.progress_changed.connect(
            lambda pct, msg: self.extra_clean_progress.setValue(pct)
        )
        self._extra_clean_thread.finished_report.connect(self._on_extra_clean_run_done)
        self._extra_clean_thread.start()

    def _on_extra_clean_run_done(self, results):
        self.extra_clean_progress.setValue(100)
        lines = [f"{'✅' if ok else '❌'} {label}: {msg}" for label, ok, msg in results]
        QMessageBox.information(self, "정리 결과", "\n".join(lines))
        for label, ok, msg in results:
            if ok and hasattr(self, "add_history_entry"):
                self.add_history_entry(f"추가 정리: {label}", None)
        self.on_extra_clean_scan()


class MainWindow(ExtendedFeaturesMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — 스마트 시스템 최적화 프로그램")
        self.resize(960, 760)

        self.settings = load_settings()
        self.excluded_set = set(self.settings.get("excluded_processes", []))

        self.last_report = None
        self.worker = None
        self.scanner = None
        self.progress_dialog = None
        self.scanning_dialog = None
        self.osd_widget = None
        self.action_history = []  # 조치 내역(Undo 타임라인)

        # ---- 게임 감시/부스트 상태 ----
        self.watched_pid = None
        self.watched_name = None
        self.boosted_original_priority_applied = False
        self.deprioritized_during_watch = []
        self.watch_timer = QTimer(self)
        self.watch_timer.setInterval(2000)
        self.watch_timer.timeout.connect(self.check_watched_process)
        self._force_quit = False

        # ---- 자동 스마트 정리 타이머 ----
        self.auto_timer = QTimer(self)
        self.auto_timer.setInterval(60 * 1000)  # 1분마다 조건 확인
        self.auto_timer.timeout.connect(self.check_auto_schedule)
        self.last_auto_run_time = None
        if self.settings["auto_schedule"]["enabled"]:
            self.auto_timer.start()

        # [v1.1.0] 탭 배치를 일관성 있게 재정렬: "최적화 실행/분석" 계열 탭을
        # 앞쪽에 모으고, 뒤이어 "관리/설정" 계열 탭(화이트리스트 → 설정)을 배치.
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # ---- 최적화 실행 & 분석 ----
        tabs.addTab(self.build_tab1(), "🚀 원클릭 최적화")
        tabs.addTab(self.build_tab2(), "📊 성능 대시보드")
        tabs.addTab(self.build_tab_perf_tweaks(), "🎮 성능 & 게이밍")
        tabs.addTab(self.build_tab_debloat(), "🧹 블로트웨어 제거")
        tabs.addTab(self.build_tab_startup(), "🗂 시작 프로그램")
        tabs.addTab(self.build_tab_cleaner_plus(), "🧽 디스크 정리+")
        tabs.addTab(self.build_tab_diagnostics(), "🩺 진단 & 복원")
        tabs.addTab(self.build_tab3(), "💡 전문가 팁 & 네트워크")

        # ---- 관리 & 설정 ----
        tabs.addTab(self.build_tab4(), "🛡 화이트리스트 관리")
        tabs.addTab(self.build_tab_settings(), "⚙️ 설정")

        self._setup_tray_icon()

    # -----------------------------------------------------------------
    # 트레이 아이콘 (창을 닫아도 고립되지 않도록)
    # -----------------------------------------------------------------
    def _setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("스마트 시스템 최적화 - 대기 중")

        menu = QMenu()
        open_action = QAction("창 열기", self)
        open_action.triggered.connect(self._show_from_tray)
        instant_action = QAction("지금 즉시 RAM 정리", self)
        instant_action.triggered.connect(self.run_instant_ram_cleanup_manual)
        osd_action = QAction("실시간 오버레이 켜기/끄기", self)
        osd_action.triggered.connect(self.toggle_osd)
        quit_action = QAction("완전 종료", self)
        quit_action.triggered.connect(self._quit_from_tray)

        menu.addAction(open_action)
        menu.addAction(instant_action)
        menu.addAction(osd_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(
            lambda reason: self._show_from_tray() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        self.tray_icon.show()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _quit_from_tray(self):
        self._force_quit = True
        if self.watched_pid:
            self.stop_watching(silent=True)
        if self.osd_widget:
            self.osd_widget.close()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """
        [버그 수정] 이제는 게임 감시 여부와 무관하게 항상 트레이로 최소화한다.
        트레이가 아예 지원되지 않는 환경에서만 완전히 종료한다.
        완전 종료는 트레이 메뉴의 [완전 종료]로만 가능하다.
        """
        if self.tray_icon and not self._force_quit:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "백그라운드에서 계속 실행 중",
                "트레이 아이콘 우클릭 → [창 열기]로 언제든 복구하거나 [완전 종료]로 끌 수 있습니다.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        else:
            if self.tray_icon:
                self.tray_icon.hide()
            event.accept()

    def toggle_osd(self):
        if self.osd_widget is None:
            self.osd_widget = OsdWidget()
            self.osd_widget.show()
        elif self.osd_widget.isVisible():
            self.osd_widget.hide()
        else:
            self.osd_widget.show()

    def run_instant_ram_cleanup_manual(self):
        result = instant_cleanup_after_game_exit(self.deprioritized_during_watch, self.excluded_set)
        self.deprioritized_during_watch = []
        msg = f"RAM {result['freed_mb']}MB 확보 ({result['trimmed_count']}개 프로세스 트림)"
        if self.tray_icon:
            self.tray_icon.showMessage("즉시 정리 완료", msg, QSystemTrayIcon.MessageIcon.Information, 3000)
        else:
            QMessageBox.information(self, "즉시 정리 완료", msg)

    # -----------------------------------------------------------------
    # Tab 1: 원클릭 최적화
    # -----------------------------------------------------------------
    def build_tab1(self):
        tab = QWidget()
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        status_lines = []
        if IS_WINDOWS:
            status_lines.append("관리자 권한: " + ("✅ 있음" if is_admin() else "⚠️ 없음 (일부 기능 제한)"))
        else:
            status_lines.append("⚠️ RAM/CPU/레지스트리 관련 기능은 Windows 전용입니다.")
        status_lines.append("SSD/브라우저 캐시 정리: " + ("✅ 사용 가능" if SEND2TRASH_AVAILABLE else "⚠️ Send2Trash 미설치"))
        status_lines.append("GPU 정보 조회: " + ("✅ 사용 가능" if NVML_AVAILABLE else "⚠️ pynvml 미설치 또는 NVIDIA 아님"))
        status_label = QLabel("\n".join(status_lines))
        status_label.setStyleSheet("color:#9a9ab0; padding:6px;")
        layout.addWidget(status_label)

        # ---- 게임 감시 & 부스터 ----
        watch_group = QGroupBox("⚡ 게임 부스터 (감시 시작 시 즉시 부스트 + 종료 시 자동 정리)")
        watch_layout = QVBoxLayout(watch_group)
        watch_desc = QLabel(
            "감시를 시작하면: 선택한 게임의 우선순위를 높이고, 백그라운드 앱은 우선순위를 낮춥니다.\n"
            "게임 종료가 감지되면: 우선순위를 자동 원복하고 RAM을 즉시 정리합니다.\n"
            "창을 닫아도 트레이에서 계속 감시합니다."
        )
        watch_desc.setWordWrap(True)
        watch_desc.setStyleSheet("color:#9a9ab0;")
        watch_layout.addWidget(watch_desc)

        watch_row = QHBoxLayout()
        self.watch_combo = QComboBox()
        self.watch_refresh_btn = QPushButton("목록 새로고침")
        self.watch_refresh_btn.setObjectName("secondaryButton")
        self.watch_refresh_btn.clicked.connect(self.refresh_watch_combo)
        watch_row.addWidget(self.watch_combo, stretch=1)
        watch_row.addWidget(self.watch_refresh_btn)
        watch_layout.addLayout(watch_row)

        self.watch_toggle_btn = QPushButton("▶ 이 게임 부스트 + 종료 감시 시작")
        self.watch_toggle_btn.clicked.connect(self.on_watch_toggle_clicked)
        watch_layout.addWidget(self.watch_toggle_btn)

        self.watch_status_label = QLabel("감시 중이 아닙니다.")
        self.watch_status_label.setStyleSheet("color:#9a9ab0;")
        watch_layout.addWidget(self.watch_status_label)

        layout.addWidget(watch_group)
        self.refresh_watch_combo()

        # ---- 체크박스 그룹 ----
        check_group = QGroupBox("최적화 대상 선택")
        check_layout = QGridLayout(check_group)
        self.cb_cpu = QCheckBox("CPU (우선순위 조정)")
        self.cb_gpu = QCheckBox("GPU (정보 조회만)")
        self.cb_ram = QCheckBox("RAM (워킹셋 트림)")
        self.cb_ssd = QCheckBox("SSD (임시파일 → 휴지통)")
        self.cb_browser = QCheckBox("브라우저 캐시 (Chrome/Edge)")
        self.cb_dns = QCheckBox("DNS 캐시 초기화")
        for i, cb in enumerate((self.cb_cpu, self.cb_gpu, self.cb_ram, self.cb_ssd, self.cb_browser, self.cb_dns)):
            cb.setChecked(True)
            check_layout.addWidget(cb, i // 2, i % 2)
        layout.addWidget(check_group)

        # ---- 강도 슬라이더 ----
        slider_group = QGroupBox("최적화 강도 (1: 약함 ~ 3: 강함)")
        slider_layout = QVBoxLayout(slider_group)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(3)
        self.slider.setValue(2)
        self.slider.valueChanged.connect(self.update_intensity_label)
        self.intensity_label = QLabel()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.intensity_label)
        layout.addWidget(slider_group)

        note = QLabel(
            "ℹ️ CPU 우선순위 조정은 2단계부터 동작합니다.\n"
            "현재 화면에서 활성화된(포그라운드) 프로그램과 아래 화이트리스트에 등록된 프로그램은 자동 보호됩니다."
        )
        note.setWordWrap(True)
        note.setStyleSheet("background:#1f2e1f; color:#b6f2c0; padding:10px; border-radius:6px;")
        layout.addWidget(note)

        # ---- 자동 스마트 정리 ----
        auto_group = QGroupBox("🕒 자동 스마트 정리 (백그라운드 무소음 실행)")
        auto_layout = QVBoxLayout(auto_group)
        self.auto_enable_cb = QCheckBox("유휴 시간 또는 RAM 사용률 초과 시 자동으로 조용히 정리")
        self.auto_enable_cb.setChecked(self.settings["auto_schedule"]["enabled"])
        self.auto_enable_cb.stateChanged.connect(self.on_auto_settings_changed)
        auto_layout.addWidget(self.auto_enable_cb)

        auto_row = QHBoxLayout()
        auto_row.addWidget(QLabel("유휴 시간(분) 이상:"))
        self.auto_idle_spin = QSpinBox()
        self.auto_idle_spin.setRange(1, 120)
        self.auto_idle_spin.setValue(self.settings["auto_schedule"]["idle_minutes"])
        self.auto_idle_spin.valueChanged.connect(self.on_auto_settings_changed)
        auto_row.addWidget(self.auto_idle_spin)

        auto_row.addWidget(QLabel("  RAM 사용률(%) 초과:"))
        self.auto_ram_spin = QSpinBox()
        self.auto_ram_spin.setRange(50, 99)
        self.auto_ram_spin.setValue(self.settings["auto_schedule"]["ram_threshold_pct"])
        self.auto_ram_spin.valueChanged.connect(self.on_auto_settings_changed)
        auto_row.addWidget(self.auto_ram_spin)
        auto_row.addStretch()
        auto_layout.addLayout(auto_row)

        self.auto_status_label = QLabel("자동 정리: 비활성화됨")
        self.auto_status_label.setStyleSheet("color:#9a9ab0;")
        auto_layout.addWidget(self.auto_status_label)
        layout.addWidget(auto_group)
        self.update_auto_status_label()

        self.progress_bar = QProgressBar()
        self.status_label = QLabel("대기 중")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self.start_btn = QPushButton("🔍 사전 점검 및 최적화 시작")
        self.start_btn.setMinimumHeight(42)
        self.start_btn.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_btn)

        osd_btn = QPushButton("📌 실시간 오버레이 표시/숨기기")
        osd_btn.setObjectName("secondaryButton")
        osd_btn.clicked.connect(self.toggle_osd)
        layout.addWidget(osd_btn)

        layout.addStretch()
        self.update_intensity_label()

        outer_scroll.setWidget(content)
        outer_layout = QVBoxLayout(tab)
        outer_layout.addWidget(outer_scroll)
        return tab

    def update_intensity_label(self):
        labels = {
            1: "1단계 (약함 - 큰 메모리 프로세스 위주, 오래된 캐시만, CPU 조정 없음)",
            2: "2단계 (보통 - 일반 백그라운드 프로세스 포함, CPU 조정 시작)",
            3: "3단계 (강함 - 더 넓은 범위, 최근 캐시까지 포함)",
        }
        self.intensity_label.setText(f"현재 강도: {labels[self.slider.value()]}")

    # ---- 자동 스마트 정리 설정 ----
    def on_auto_settings_changed(self):
        self.settings["auto_schedule"]["enabled"] = self.auto_enable_cb.isChecked()
        self.settings["auto_schedule"]["idle_minutes"] = self.auto_idle_spin.value()
        self.settings["auto_schedule"]["ram_threshold_pct"] = self.auto_ram_spin.value()
        save_settings(self.settings)

        if self.settings["auto_schedule"]["enabled"]:
            if not self.auto_timer.isActive():
                self.auto_timer.start()
        else:
            self.auto_timer.stop()
        self.update_auto_status_label()

    def update_auto_status_label(self):
        s = self.settings["auto_schedule"]
        if not s["enabled"]:
            self.auto_status_label.setText("자동 정리: 비활성화됨")
        else:
            last = self.last_auto_run_time.strftime("%H:%M:%S") if self.last_auto_run_time else "없음"
            self.auto_status_label.setText(
                f"자동 정리: 활성화됨 (유휴 {s['idle_minutes']}분 또는 RAM {s['ram_threshold_pct']}% 초과 시) "
                f"| 마지막 실행: {last}"
            )

    def check_auto_schedule(self):
        """1분마다 호출되어 자동 정리 조건을 만족하는지 확인한다."""
        s = self.settings["auto_schedule"]
        if not s["enabled"]:
            return

        # 너무 자주 실행되지 않도록 최소 10분 간격(쿨다운) 적용
        if self.last_auto_run_time and (datetime.now() - self.last_auto_run_time).total_seconds() < 600:
            return

        idle_min = get_idle_minutes()
        ram_pct = psutil.virtual_memory().percent

        if idle_min >= s["idle_minutes"] or ram_pct >= s["ram_threshold_pct"]:
            reason = f"유휴 {idle_min:.1f}분" if idle_min >= s["idle_minutes"] else f"RAM {ram_pct:.0f}%"
            self.run_silent_auto_optimization(reason)

    def run_silent_auto_optimization(self, reason: str):
        """자동 스케줄링에 의해 팝업 없이 조용히 실행되는 최적화 (RAM 트림 + CPU 우선순위, 강도 2 고정)."""
        self.last_auto_run_time = datetime.now()
        self.update_auto_status_label()

        ram_candidates = scan_ram_candidates(2, self.excluded_set) if IS_WINDOWS else []
        cpu_candidates = scan_cpu_candidates(2, self.excluded_set)

        trimmed, deprioritized = 0, []
        for pid, name, mem_mb in ram_candidates:
            if trim_process_working_set(pid):
                trimmed += 1
        for pid, name, cpu_pct in cpu_candidates:
            if lower_process_priority(pid):
                deprioritized.append((pid, name))
                self.add_history_entry(f"[자동] {name} 우선순위 낮춤", "priority", pid=pid, name=name)

        self.deprioritized_during_watch.extend(deprioritized)
        write_log(f"[자동 스케줄] {reason} 감지 -> RAM {trimmed}개 트림, CPU {len(deprioritized)}개 우선순위 조정")

        if self.tray_icon:
            self.tray_icon.showMessage(
                "자동 스마트 정리 실행됨",
                f"({reason}) RAM {trimmed}개 프로세스 트림, CPU {len(deprioritized)}개 우선순위 조정",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    # ---- 게임 감시 & 부스트 ----
    def refresh_watch_combo(self):
        self.watch_combo.clear()
        if not IS_WINDOWS:
            self.watch_combo.addItem("Windows 전용 기능입니다", None)
            self.watch_combo.setEnabled(False)
            return
        candidates = get_watchable_processes()
        if not candidates:
            self.watch_combo.addItem("실행 중인 무거운 프로세스가 없습니다", None)
            return
        for pid, name, mem_mb in candidates:
            self.watch_combo.addItem(f"{name}  (PID {pid}, {mem_mb} MB)", (pid, name))

    def on_watch_toggle_clicked(self):
        if self.watched_pid is None:
            self.start_watching()
        else:
            self.stop_watching()

    def start_watching(self):
        item_data = self.watch_combo.currentData()
        if item_data is None:
            QMessageBox.warning(self, "선택 필요", "감시할 프로세스를 목록에서 선택하세요.")
            return

        self.watched_pid, self.watched_name = item_data

        # ---- 게임 부스트 즉시 적용 ----
        boosted = raise_process_priority(self.watched_pid)
        if boosted:
            write_log(f"게임 부스트: {self.watched_name} 우선순위 상승 (PID {self.watched_pid})")
            self.add_history_entry(f"[부스트] {self.watched_name} 우선순위 상승", "boost_priority",
                                    pid=self.watched_pid, name=self.watched_name)

        cpu_candidates = scan_cpu_candidates(3, self.excluded_set)
        boosted_bg = []
        for pid, name, cpu_pct in cpu_candidates:
            if pid == self.watched_pid:
                continue
            if lower_process_priority(pid):
                boosted_bg.append((pid, name))
                self.add_history_entry(f"[부스트] {name} 우선순위 낮춤", "priority", pid=pid, name=name)
        self.deprioritized_during_watch.extend(boosted_bg)

        self.watch_timer.start()
        self.watch_toggle_btn.setText("■ 감시 중지")
        self.watch_status_label.setText(
            f"🟢 감시+부스트 중: {self.watched_name} (PID {self.watched_pid}) - "
            f"백그라운드 {len(boosted_bg)}개 양보 처리됨"
        )
        if self.tray_icon:
            self.tray_icon.setToolTip(f"감시 중: {self.watched_name}")
        write_log(f"게임 종료 자동 감지 시작: {self.watched_name} (PID {self.watched_pid})")

    def stop_watching(self, silent=False):
        self.watch_timer.stop()
        if self.watched_pid and restore_process_priority(self.watched_pid):
            write_log(f"게임 부스트 원복: {self.watched_name} (PID {self.watched_pid})")
        if not silent:
            write_log(f"게임 종료 자동 감지 중지: {self.watched_name}")
        self.watched_pid = None
        self.watched_name = None
        self.watch_toggle_btn.setText("▶ 이 게임 부스트 + 종료 감시 시작")
        self.watch_status_label.setText("감시 중이 아닙니다.")
        if self.tray_icon:
            self.tray_icon.setToolTip("스마트 시스템 최적화 - 대기 중")

    def check_watched_process(self):
        if self.watched_pid is None:
            return
        if psutil.pid_exists(self.watched_pid):
            return

        finished_name = self.watched_name
        self.watch_timer.stop()

        result = instant_cleanup_after_game_exit(self.deprioritized_during_watch, self.excluded_set)
        for pid, name in self.deprioritized_during_watch:
            self.add_history_entry(f"[자동원복] {name} 우선순위 원복", "reverted", pid=pid, name=name)
        self.deprioritized_during_watch = []

        write_log(
            f"[자동] '{finished_name}' 종료 감지 -> RAM {result['freed_mb']}MB 확보, "
            f"{result['trimmed_count']}개 프로세스 트림, {result['restored_count']}개 우선순위 원복"
        )

        detect_msg = f"'{finished_name}' 종료를 감지해 RAM {result['freed_mb']}MB를 즉시 확보했습니다."
        if self.tray_icon:
            self.tray_icon.showMessage("게임 종료 감지 - 자동 정리 완료", detect_msg,
                                        QSystemTrayIcon.MessageIcon.Information, 5000)
        elif self.isVisible():
            QMessageBox.information(self, "게임 종료 감지", detect_msg)

        self.watched_pid = None
        self.watched_name = None
        if self.isVisible():
            self.watch_toggle_btn.setText("▶ 이 게임 부스트 + 종료 감시 시작")
            self.watch_status_label.setText(
                f"✅ '{finished_name}' 종료를 감지해 자동으로 정리했습니다. (RAM {result['freed_mb']}MB 확보)"
            )
            self.refresh_watch_combo()

    # ---- 최적화 시작 (스캔은 ScannerWorker로 비동기 처리) ----
    def on_start_clicked(self):
        options = {
            "cpu": self.cb_cpu.isChecked(),
            "gpu": self.cb_gpu.isChecked(),
            "ram": self.cb_ram.isChecked(),
            "ssd": self.cb_ssd.isChecked(),
            "browser": self.cb_browser.isChecked(),
            "dns": self.cb_dns.isChecked(),
        }
        if not any(options.values()):
            QMessageBox.warning(self, "선택 필요", "최소 하나 이상의 항목을 선택하세요.")
            return

        intensity = self.slider.value()
        self.start_btn.setEnabled(False)

        # [버그 수정] 스캔을 별도 스레드(ScannerWorker)에서 실행해 UI가 멈추지 않도록 함
        self.scanning_dialog = ScanningDialog(parent=self)
        self.scanner = ScannerWorker(options, intensity, self.excluded_set)
        self.scanner.scan_finished.connect(self.on_scan_finished)
        self.scanner.start()
        self.scanning_dialog.exec()

    def on_scan_finished(self, scan_result: dict):
        if self.scanning_dialog:
            self.scanning_dialog.accept()
            self.scanning_dialog = None
        self.start_btn.setEnabled(True)

        precheck = PrecheckDialog(scan_result, parent=self)
        if precheck.exec() != QDialog.DialogCode.Accepted:
            return

        ram_selected, cpu_selected, files_selected, browser_selected, dns_selected = precheck.get_selected()
        self.run_optimization(ram_selected, cpu_selected, files_selected, browser_selected,
                               dns_selected, scan_result.get("gpu_selected", False))

    def run_optimization(self, ram_selected, cpu_selected, files_selected, browser_selected, dns_selected, gpu_selected):
        self.start_btn.setEnabled(False)
        self.progress_dialog = ProgressDialog(parent=self)

        self.worker = OptimizationWorker(ram_selected, cpu_selected, files_selected,
                                          browser_selected, dns_selected, gpu_selected)
        self.worker.progress_changed.connect(self.progress_dialog.update_progress)
        self.worker.progress_changed.connect(lambda v, t: self.progress_bar.setValue(v))
        self.worker.finished_report.connect(self.on_finished)
        self.worker.start()
        self.progress_dialog.exec()

    def on_finished(self, report):
        self.last_report = report
        self.start_btn.setEnabled(True)

        self.deprioritized_during_watch.extend(report.get("cpu_deprioritized", []))
        for pid, name in report.get("cpu_deprioritized", []):
            self.add_history_entry(f"{name} 우선순위 낮춤", "priority", pid=pid, name=name)
        if report.get("disk_freed_files"):
            self.add_history_entry(f"임시 파일 {report['disk_freed_files']}개 휴지통 이동", "trash_info")
        if report.get("browser_freed_files"):
            self.add_history_entry(f"브라우저 캐시 {report['browser_freed_files']}개 휴지통 이동", "trash_info")
        if report.get("dns_flushed"):
            self.add_history_entry("DNS 캐시 초기화", None)

        if self.progress_dialog:
            self.progress_dialog.accept()
            self.progress_dialog = None

        write_log(
            f"최적화 완료 - RAM 확보 {report['ram_freed_mb']}MB, "
            f"디스크 확보 {round(report['disk_freed_bytes']/1024/1024,1)}MB, "
            f"CPU 우선순위 조정 {len(report['cpu_deprioritized'])}개"
        )

        self.refresh_dashboard()
        self.centralWidget().setCurrentIndex(1)
        QMessageBox.information(self, "완료", "최적화가 완료되었습니다. [성능 대시보드]에서 실제 결과를 확인하세요.")

    # -----------------------------------------------------------------
    # Tab 2: 성능 대시보드
    # -----------------------------------------------------------------
    def build_tab2(self):
        tab = QWidget()
        self.dash_layout = QVBoxLayout(tab)

        # [버그 수정] 기존에는 QLabel + 고정 레이아웃 조합이라, 결과 텍스트가 길어지면
        # QLabel에 할당되는 세로 공간이 부족해 글자가 위아래로 잘려 보이는 문제가 있었다.
        # 읽기전용 QTextEdit(자체 스크롤 지원)로 교체하고 레이아웃 stretch를 줘서
        # 내용이 많아도 잘리지 않고 스크롤되도록 수정.
        self.dash_content = QTextEdit()
        self.dash_content.setReadOnly(True)
        self.dash_content.setPlainText("아직 실행된 최적화가 없습니다.")
        self.dash_content.setMinimumHeight(180)
        self.dash_layout.addWidget(self.dash_content, stretch=1)

        btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton("↩ CPU 우선순위 전체 원복")
        self.restore_btn.setObjectName("secondaryButton")
        self.restore_btn.clicked.connect(self.on_restore_clicked)
        self.log_btn = QPushButton("📄 로그 보기")
        self.log_btn.setObjectName("secondaryButton")
        self.log_btn.clicked.connect(self.show_log)
        self.recycle_btn = QPushButton("🗑 휴지통 열기")
        self.recycle_btn.setObjectName("secondaryButton")
        self.recycle_btn.clicked.connect(self.open_recycle_bin)
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.log_btn)
        btn_layout.addWidget(self.recycle_btn)
        self.dash_layout.addLayout(btn_layout)

        history_label = QLabel("📜 최근 조치 내역 (원클릭 되돌리기)")
        history_label.setStyleSheet("font-weight:bold; margin-top:10px;")
        self.dash_layout.addWidget(history_label)

        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(220)
        self.dash_layout.addWidget(self.history_list)

        return tab

    def add_history_entry(self, desc: str, revert_type, pid=None, name=None):
        """조치 내역에 새 항목을 추가한다 (Undo 타임라인)."""
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "desc": desc,
            "revert_type": revert_type,  # "priority" | "trash_info" | "reverted" | "boost_priority" | None
            "pid": pid,
            "name": name,
        }
        self.action_history.insert(0, entry)
        self.action_history = self.action_history[:50]
        self.refresh_history_list()

    def refresh_history_list(self):
        if not hasattr(self, "history_list"):
            return
        self.history_list.clear()
        for entry in self.action_history:
            item = QListWidgetItem(self.history_list)
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 2, 4, 2)

            label = QLabel(f"[{entry['time']}] {entry['desc']}")
            row_layout.addWidget(label, stretch=1)

            if entry["revert_type"] in ("priority", "boost_priority"):
                btn = QPushButton("되돌리기")
                btn.setObjectName("secondaryButton")
                btn.clicked.connect(lambda _, e=entry, w=row_widget: self.revert_history_entry(e, w))
                row_layout.addWidget(btn)
            elif entry["revert_type"] == "trash_info":
                btn = QPushButton("휴지통 열기")
                btn.setObjectName("secondaryButton")
                btn.clicked.connect(self.open_recycle_bin)
                row_layout.addWidget(btn)
            elif entry["revert_type"] == "reverted":
                done_label = QLabel("✅ 자동 원복됨")
                done_label.setStyleSheet("color:#63e6a3;")
                row_layout.addWidget(done_label)
            else:
                na_label = QLabel("되돌릴 수 없음")
                na_label.setStyleSheet("color:#666;")
                row_layout.addWidget(na_label)

            item.setSizeHint(row_widget.sizeHint())
            self.history_list.setItemWidget(item, row_widget)

    def revert_history_entry(self, entry, row_widget):
        """개별 조치를 즉시 되돌린다 (우선순위 조정 항목만 해당)."""
        success = restore_process_priority(entry["pid"])
        if success:
            write_log(f"[수동 원복] {entry['name']} 우선순위 원복 (PID {entry['pid']})")
            entry["revert_type"] = "reverted"
            self.deprioritized_during_watch = [
                (p, n) for p, n in self.deprioritized_during_watch if p != entry["pid"]
            ]
            QMessageBox.information(self, "원복 완료", f"{entry['name']}의 우선순위를 원복했습니다.")
        else:
            QMessageBox.warning(self, "원복 실패", "이미 종료되었거나 권한이 없어 원복할 수 없습니다.")
        self.refresh_history_list()

    def refresh_dashboard(self):
        if not self.last_report:
            self.dash_content.setPlainText("아직 실행된 최적화가 없습니다.")
            return
        r = self.last_report
        lines = [
            f"✅ 최적화 완료 시각: {r['timestamp']}\n",
            f"[RAM] 정리 전 사용량: {r['ram_before_mb']} MB → 정리 후: {r['ram_after_mb']} MB",
            f"[RAM] 실제 확보된 여유 메모리: 약 {r['ram_freed_mb']} MB (트림된 프로세스 {r['ram_trimmed_process_count']}개)",
            f"[CPU] 확보량: 약 {r.get('cpu_reclaimed_pct', 0)}% (시스템 전체 대비, 우선순위를 낮춘 프로세스 기준)",
            f"[CPU] 참고 - 전체 시스템 순간 사용률: {r['cpu_before_pct']}% → {r['cpu_after_pct']}% (오차 있을 수 있음)",
            f"[SSD] 휴지통으로 이동한 파일: {r['disk_freed_files']}개 (총 {round(r['disk_freed_bytes']/1024/1024,1)} MB)",
            f"[브라우저] 캐시 정리: {r.get('browser_freed_files',0)}개 (총 {round(r.get('browser_freed_bytes',0)/1024/1024,1)} MB)",
        ]
        if r.get("dns_flushed") is not None:
            lines.append(f"[DNS] 캐시 초기화: {'성공' if r['dns_flushed'] else '실패'}")

        if r.get("gpu_info"):
            g = r["gpu_info"]
            lines.append(f"\n[GPU] {g['gpu_name']}: {g['used_mb']} / {g['total_mb']} MB 사용 중 (여유 {g['free_mb']} MB)")
            if g["top_processes"]:
                top = ", ".join(f"{n}({m}MB)" for n, m in g["top_processes"])
                lines.append(f"[GPU] VRAM 사용량 상위 프로세스: {top}")
        else:
            lines.append("\n[GPU] 정보 없음 (NVIDIA GPU가 아니거나 미설치, 또는 GPU 옵션 미선택)")

        self.dash_content.setPlainText("\n".join(lines))
        self.refresh_history_list()

    def on_restore_clicked(self):
        if not self.deprioritized_during_watch:
            QMessageBox.information(self, "안내", "원복할 대상이 없습니다.")
            return
        restored, failed = 0, 0
        for pid, name in list(self.deprioritized_during_watch):
            if restore_process_priority(pid):
                restored += 1
                write_log(f"CPU 우선순위 원복 성공: {name} (PID {pid})")
                for entry in self.action_history:
                    if entry.get("pid") == pid and entry["revert_type"] in ("priority", "boost_priority"):
                        entry["revert_type"] = "reverted"
            else:
                failed += 1
        QMessageBox.information(self, "원복 완료", f"{restored}개 프로세스 우선순위를 원복했습니다. (실패 {failed}개)")
        self.deprioritized_during_watch = []
        self.refresh_history_list()

    def show_log(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("최적화 로그")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                text_edit.setPlainText(f.read())
        except FileNotFoundError:
            text_edit.setPlainText("아직 기록된 로그가 없습니다.")
        layout.addWidget(text_edit)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def open_recycle_bin(self):
        if IS_WINDOWS:
            os.system("explorer shell:RecycleBinFolder")
        else:
            QMessageBox.information(self, "안내", "이 기능은 Windows 전용입니다.")

    # -----------------------------------------------------------------
    # Tab 3: 전문가 팁 & 네트워크 / 복구
    # -----------------------------------------------------------------
    def build_tab3(self):
        tab = QWidget()
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        box1 = QGroupBox("NVIDIA 제어판 설정")
        b1 = QVBoxLayout(box1)
        b1.addWidget(QLabel("전원 관리: 최고 성능 선호 / 저지연 모드: 울트라 권장"))
        btn1 = QPushButton("NVIDIA 제어판 열기")
        btn1.clicked.connect(lambda: os.system("start nvcplui.exe") if IS_WINDOWS else None)
        b1.addWidget(btn1)
        layout.addWidget(box1)

        box2 = QGroupBox("윈도우 서비스 정리")
        b2 = QVBoxLayout(box2)
        b2.addWidget(QLabel("SysMain, DiagTrack 등은 필요시 수동으로 변경하세요."))
        btn2 = QPushButton("서비스 관리자 열기")
        btn2.clicked.connect(lambda: os.system("start services.msc") if IS_WINDOWS else None)
        b2.addWidget(btn2)
        layout.addWidget(box2)

        box3 = QGroupBox("시작 프로그램 정리")
        b3 = QVBoxLayout(box3)
        b3.addWidget(QLabel("불필요한 시작 프로그램을 꺼서 부팅 시간을 줄이세요."))
        btn3 = QPushButton("시작 앱 설정 열기")
        btn3.clicked.connect(lambda: os.system("start ms-settings:startupapps") if IS_WINDOWS else None)
        b3.addWidget(btn3)
        layout.addWidget(box3)

        # ---- 네트워크 핑 최적화 (Nagle) ----
        net_box = QGroupBox("🌐 네트워크 핑 최적화 (Nagle 알고리즘)")
        net_layout = QVBoxLayout(net_box)
        net_desc = QLabel(
            "Nagle 알고리즘을 끄면 작은 네트워크 패킷을 모아 보내지 않고 즉시 전송해 핑(지연)이 줄어들 수 있습니다.\n"
            "레지스트리를 수정하며 관리자 권한이 필요합니다. 적용 후 재부팅을 권장합니다."
        )
        net_desc.setWordWrap(True)
        net_layout.addWidget(net_desc)

        self.nagle_status_label = QLabel(
            "마지막 적용 상태: " + ("비활성화(핑 최적화 적용됨)" if self.settings.get("nagle_disabled") else "기본값")
        )
        self.nagle_status_label.setStyleSheet("color:#9a9ab0;")
        net_layout.addWidget(self.nagle_status_label)

        net_btn_row = QHBoxLayout()
        nagle_off_btn = QPushButton("Nagle 비활성화 (핑 최적화)")
        nagle_off_btn.clicked.connect(lambda: self.on_nagle_toggle(True))
        nagle_on_btn = QPushButton("기본값으로 복원")
        nagle_on_btn.setObjectName("secondaryButton")
        nagle_on_btn.clicked.connect(lambda: self.on_nagle_toggle(False))
        net_btn_row.addWidget(nagle_off_btn)
        net_btn_row.addWidget(nagle_on_btn)
        net_layout.addLayout(net_btn_row)
        layout.addWidget(net_box)

        # ---- 시스템 복구 지점 ----
        restore_box = QGroupBox("🛡 시스템 복구 지점 생성")
        restore_layout = QVBoxLayout(restore_box)
        restore_layout.addWidget(QLabel(
            "레지스트리/우선순위 변경 등 시스템 조치를 하기 전에 복구 지점을 만들어두면 안전합니다.\n"
            "(Windows는 기본적으로 24시간에 1번만 생성을 허용합니다. 관리자 권한 필요)"
        ))
        restore_btn = QPushButton("지금 복구 지점 만들기")
        restore_btn.clicked.connect(self.on_create_restore_point)
        restore_layout.addWidget(restore_btn)
        layout.addWidget(restore_box)

        layout.addStretch()
        outer_scroll.setWidget(content)
        outer_layout = QVBoxLayout(tab)
        outer_layout.addWidget(outer_scroll)
        return tab

    def on_nagle_toggle(self, disable: bool):
        if not is_admin():
            QMessageBox.warning(self, "관리자 권한 필요",
                                 "이 기능은 관리자 권한으로 실행해야 합니다.\n"
                                 "프로그램을 관리자 권한으로 다시 실행해주세요.")
            return
        confirm = QMessageBox.question(
            self, "확인",
            ("Nagle 알고리즘을 비활성화하시겠습니까?" if disable else "기본값으로 복원하시겠습니까?") +
            "\n네트워크 레지스트리 값이 변경됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        success, msg = set_nagle(disable)
        if success:
            self.settings["nagle_disabled"] = disable
            save_settings(self.settings)
            self.nagle_status_label.setText(
                "마지막 적용 상태: " + ("비활성화(핑 최적화 적용됨)" if disable else "기본값")
            )
            self.add_history_entry(f"Nagle 알고리즘 {'비활성화' if disable else '복원'}", None)
        QMessageBox.information(self, "결과", msg)

    def on_create_restore_point(self):
        if not is_admin():
            QMessageBox.warning(self, "관리자 권한 필요", "이 기능은 관리자 권한이 필요합니다.")
            return
        confirm = QMessageBox.question(
            self, "확인", "시스템 복구 지점을 생성하시겠습니까? (몇 분 정도 걸릴 수 있습니다)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        success, msg = create_restore_point()
        if success:
            self.add_history_entry("시스템 복구 지점 생성", None)
        QMessageBox.information(self, "결과", msg)

    # -----------------------------------------------------------------
    # Tab 4: 화이트리스트(예외 목록) 관리
    # -----------------------------------------------------------------
    def build_tab4(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # [v1.1.0] 🎨 테마 선택은 "⚙️ 설정" 탭으로 이동했습니다 (build_tab_settings 참고).

        # ---- 화이트리스트(예외 목록) ----
        desc = QLabel(
            "여기에 등록한 프로세스는 RAM 트림 / CPU 우선순위 조정 / 게임 부스트 대상에서 항상 제외됩니다.\n"
            "예: discord.exe, spotify.exe 처럼 파일 이름 그대로 입력하세요 (대소문자 무관)."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.exclude_list_widget = QListWidget()
        for name in sorted(self.excluded_set):
            self.exclude_list_widget.addItem(name)
        layout.addWidget(self.exclude_list_widget)

        add_row = QHBoxLayout()
        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("예: discord.exe")
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.on_add_exclude)
        add_row.addWidget(self.exclude_input)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        remove_btn = QPushButton("선택 항목 삭제")
        remove_btn.setObjectName("secondaryButton")
        remove_btn.clicked.connect(self.on_remove_exclude)
        layout.addWidget(remove_btn)

        layout.addStretch()
        return tab

    def on_theme_changed(self, index: int):
        theme_key = self.theme_combo.itemData(index)
        if not theme_key:
            return
        apply_theme(theme_key)
        self.settings["theme"] = theme_key
        save_settings(self.settings)
        write_log(f"테마 변경: {theme_key}")

    def on_add_exclude(self):
        name = self.exclude_input.text().strip().lower()
        if not name:
            return
        if name in self.excluded_set:
            QMessageBox.information(self, "안내", "이미 등록된 항목입니다.")
            return
        self.excluded_set.add(name)
        self.exclude_list_widget.addItem(name)
        self.exclude_input.clear()
        self.settings["excluded_processes"] = sorted(self.excluded_set)
        save_settings(self.settings)
        write_log(f"화이트리스트 추가: {name}")

    def on_remove_exclude(self):
        selected_items = self.exclude_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "안내", "삭제할 항목을 목록에서 선택하세요.")
            return
        for item in selected_items:
            name = item.text()
            self.excluded_set.discard(name)
            self.exclude_list_widget.takeItem(self.exclude_list_widget.row(item))
            write_log(f"화이트리스트 제거: {name}")
        self.settings["excluded_processes"] = sorted(self.excluded_set)
        save_settings(self.settings)

    # -----------------------------------------------------------------
    # Tab: 설정 (테마 · 프로그램 정보 · 업데이트 내역)
    # -----------------------------------------------------------------
    def build_tab_settings(self):
        tab = QWidget()
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        # ---- 테마 선택 ----
        theme_box = QGroupBox("🎨 테마 선택")
        theme_layout = QVBoxLayout(theme_box)
        theme_layout.addWidget(QLabel("원하는 색상 테마를 선택하세요. 즉시 적용되고 다음 실행 시에도 유지됩니다."))
        self.theme_combo = QComboBox()
        current_theme_key = self.settings.get("theme", DEFAULT_THEME_KEY)
        selected_index = 0
        for i, (key, theme) in enumerate(THEMES.items()):
            self.theme_combo.addItem(theme["label"], userData=key)
            if key == current_theme_key:
                selected_index = i
        self.theme_combo.setCurrentIndex(selected_index)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_box)

        # ---- 프로그램 정보 ----
        info_box = QGroupBox("ℹ️ 프로그램 정보")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel(f"{APP_NAME} v{APP_VERSION}"))
        info_layout.addWidget(QLabel("제작자 및 관리자: JeulGemI"))
        info_layout.addWidget(QLabel("공동 협업자: KRJohnWick"))
        layout.addWidget(info_box)

        # ---- 업데이트 내역 ----
        changelog_box = QGroupBox("📜 업데이트 내역")
        changelog_layout = QVBoxLayout(changelog_box)
        changelog_view = QTextEdit()
        changelog_view.setReadOnly(True)
        changelog_view.setMinimumHeight(260)
        changelog_view.setPlainText(get_changelog_text())
        changelog_layout.addWidget(changelog_view)
        layout.addWidget(changelog_box)

        layout.addStretch()
        outer_scroll.setWidget(content)
        outer_layout = QVBoxLayout(tab)
        outer_layout.addWidget(outer_scroll)
        return tab


# =====================================================================
# 8. 다중 테마 시스템 (THEMES + QSS 생성기)
# =====================================================================
# [신규 기능] 블랙 / 그레이 / 화이트 + 다양한 색상 테마.
# 각 테마는 색상 토큰만 다르고 구조는 동일한 QSS 템플릿을 공유한다.
# QLabel/QCheckBox/QGroupBox 등에 여유 있는 padding을 줘서 텍스트가
# 위아래로 잘리는 현상을 테마 차원에서도 방지한다.
THEME_QSS_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 10pt;
}}
QMainWindow {{ background-color: {bg_main}; }}
QLabel {{ padding: 2px 0px; }}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 8px;
    background-color: {panel};
}}
QTabBar::tab {{
    background: {panel};
    color: {subtext};
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}}
QTabBar::tab:selected {{ background: {accent}; color: {tab_selected_text}; }}
QTabBar::tab:hover:!selected {{ background: {panel_hover}; }}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 10px 10px 10px;
    font-weight: bold;
    color: {accent_text};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
QCheckBox {{ spacing: 8px; padding: 5px 2px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid {border_strong}; background: {panel};
}}
QCheckBox::indicator:checked {{ background: {accent}; border: 1px solid {accent}; }}
QPushButton {{
    background-color: {accent}; color: {button_text}; border: none;
    border-radius: 8px; padding: 10px 16px; font-weight: bold;
}}
QPushButton:hover {{ background-color: {accent_hover}; }}
QPushButton:pressed {{ background-color: {accent_pressed}; }}
QPushButton:disabled {{ background-color: {disabled_bg}; color: {disabled_text}; }}
QPushButton#secondaryButton {{ background-color: {panel_hover}; color: {text}; }}
QPushButton#secondaryButton:hover {{ background-color: {border}; }}
QSlider::groove:horizontal {{ height: 6px; background: {border}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {progress}; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px;
}}
QSlider::sub-page:horizontal {{ background: {progress}; border-radius: 3px; }}
QListWidget {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 4px;
}}
QListWidget::item {{ padding: 7px 4px; border-radius: 4px; }}
QListWidget::item:hover {{ background-color: {panel_hover}; }}
QProgressBar {{
    border: 1px solid {border}; border-radius: 8px; background-color: {panel};
    text-align: center; height: 24px; padding: 1px; color: {text};
}}
QProgressBar::chunk {{ background-color: {progress}; border-radius: 8px; }}
QLineEdit, QSpinBox, QComboBox {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 7px;
    color: {text};
}}
QComboBox QAbstractItemView {{
    background-color: {panel}; color: {text}; border: 1px solid {border};
    selection-background-color: {accent}; selection-color: {button_text};
}}
QTextEdit {{
    background-color: {panel}; border: 1px solid {border}; border-radius: 6px;
    padding: 6px; color: {text};
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {bg}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {border_strong}; border-radius: 6px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {accent}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
"""


def make_theme_qss(colors: dict) -> str:
    """색상 토큰 dict를 받아 완성된 QSS 문자열을 생성한다."""
    return THEME_QSS_TEMPLATE.format(**colors)


# 필수 3종(블랙/그레이/화이트) + 다양한 색상 테마
THEMES = {
    "black": {
        "label": "⚫ 블랙",
        "colors": {
            "bg": "#0d0d0f", "bg_main": "#0a0a0b", "panel": "#19191c",
            "panel_hover": "#242427", "border": "#2c2c30", "border_strong": "#3f3f45",
            "text": "#eaeaea", "subtext": "#9a9a9f", "accent": "#3b82f6",
            "accent_hover": "#5b9bfa", "accent_pressed": "#2f68c9", "accent_text": "#93c5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#2a2a2e", "disabled_text": "#77777c", "progress": "#22d3ee",
        },
    },
    "gray": {
        "label": "⚪ 그레이",
        "colors": {
            "bg": "#28292d", "bg_main": "#222327", "panel": "#323338",
            "panel_hover": "#3c3d43", "border": "#46474e", "border_strong": "#5a5b63",
            "text": "#f2f2f3", "subtext": "#b7b8bf", "accent": "#14b8a6",
            "accent_hover": "#2dd4bf", "accent_pressed": "#0f9488", "accent_text": "#5eead4",
            "button_text": "#0a0a0a", "tab_selected_text": "#0a0a0a",
            "disabled_bg": "#3a3b41", "disabled_text": "#8a8b92", "progress": "#38bdf8",
        },
    },
    "white": {
        "label": "⚪ 화이트",
        "colors": {
            "bg": "#f4f5f7", "bg_main": "#eceef1", "panel": "#ffffff",
            "panel_hover": "#eef0f4", "border": "#d8dae0", "border_strong": "#b9bcc4",
            "text": "#20222a", "subtext": "#5b5e69", "accent": "#4f46e5",
            "accent_hover": "#6366f1", "accent_pressed": "#4338ca", "accent_text": "#4338ca",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#e4e5e9", "disabled_text": "#a0a2aa", "progress": "#06b6d4",
        },
    },
    "purple": {
        "label": "🟣 퍼플(게이밍)",
        "colors": {
            "bg": "#14151b", "bg_main": "#101116", "panel": "#1a1c26",
            "panel_hover": "#262838", "border": "#2a2c3d", "border_strong": "#45475a",
            "text": "#e6e6e6", "subtext": "#9a9ab0", "accent": "#7c3aed",
            "accent_hover": "#9061f9", "accent_pressed": "#6425d0", "accent_text": "#c4b5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#33354a", "disabled_text": "#888888", "progress": "#00e5ff",
        },
    },
    "blue": {
        "label": "🔵 블루",
        "colors": {
            "bg": "#0b1220", "bg_main": "#080e1a", "panel": "#101a2e",
            "panel_hover": "#182541", "border": "#1f2b45", "border_strong": "#33456b",
            "text": "#e4e9f2", "subtext": "#8b98b3", "accent": "#2563eb",
            "accent_hover": "#3b82f6", "accent_pressed": "#1d4ed8", "accent_text": "#93c5fd",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#25324d", "disabled_text": "#7c879e", "progress": "#38bdf8",
        },
    },
    "green": {
        "label": "🟢 그린",
        "colors": {
            "bg": "#0e1512", "bg_main": "#0a100d", "panel": "#16211b",
            "panel_hover": "#1e2e26", "border": "#26362c", "border_strong": "#3c5245",
            "text": "#e4efe7", "subtext": "#93a89b", "accent": "#16a34a",
            "accent_hover": "#22c55e", "accent_pressed": "#15803d", "accent_text": "#86efac",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#243830", "disabled_text": "#7e9186", "progress": "#4ade80",
        },
    },
    "red": {
        "label": "🔴 레드",
        "colors": {
            "bg": "#160d0f", "bg_main": "#100a0b", "panel": "#221317",
            "panel_hover": "#2e1a20", "border": "#3a1e23", "border_strong": "#57303a",
            "text": "#f1e4e6", "subtext": "#b08890", "accent": "#dc2626",
            "accent_hover": "#ef4444", "accent_pressed": "#b91c1c", "accent_text": "#fca5a5",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#3a2328", "disabled_text": "#93777c", "progress": "#fb7185",
        },
    },
    "orange": {
        "label": "🟠 오렌지",
        "colors": {
            "bg": "#181209", "bg_main": "#120d07", "panel": "#241a0d",
            "panel_hover": "#302512", "border": "#3a2a14", "border_strong": "#5a4020",
            "text": "#f3e9d8", "subtext": "#c2a173", "accent": "#ea580c",
            "accent_hover": "#f97316", "accent_pressed": "#c2410c", "accent_text": "#fdba74",
            "button_text": "#ffffff", "tab_selected_text": "#ffffff",
            "disabled_bg": "#3d2e18", "disabled_text": "#9c8560", "progress": "#fbbf24",
        },
    },
}

DEFAULT_THEME_KEY = "purple"


def apply_theme(theme_key: str):
    """QApplication 전체에 테마 QSS를 적용한다. 알 수 없는 키는 기본 테마로 대체."""
    theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME_KEY])
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(make_theme_qss(theme["colors"]))


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 창을 닫아도 트레이에서 계속 실행

    startup_settings = load_settings()
    apply_theme(startup_settings.get("theme", DEFAULT_THEME_KEY))

    if not IS_WINDOWS:
        QMessageBox.warning(
            None, "환경 안내",
            "RAM/CPU/레지스트리/복구 지점 기능은 Windows 전용입니다.\n"
            "다른 OS에서는 SSD/브라우저 캐시 정리와 GPU 정보 조회만 동작합니다."
        )


    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
