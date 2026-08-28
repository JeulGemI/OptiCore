# -*- coding: utf-8 -*-
"""
core/scanner.py — 시스템 상태 "조회" 전담 (아무것도 변경하지 않음)

의존: config.py 만 (단방향)

담당 범위
  - 권한/포그라운드/유휴시간 등 시스템 상태 질의 (is_admin, get_foreground_pid,
    get_idle_minutes) 및 보호 대상 판정(is_protected)
  - CPU / RAM / SSD(임시파일) / 브라우저 캐시 / GPU 스캔
  - CPU 코어 수 정규화 + psutil Process 객체 캐시
  - UI 프리징 방지용 ScannerWorker(QThread)

이 모듈의 함수는 전부 "읽기 전용"이다. 실제로 시스템을 바꾸는 동작은
core/actions.py 에 있다.
"""

import os
import time
import ctypes
import tempfile

import psutil

from PyQt6.QtCore import QThread, pyqtSignal

from config import (
    IS_WINDOWS, NVML_AVAILABLE, pynvml,
    CPU_CORE_COUNT, PROTECTED_PROCESSES,
)

# [버그 수정] psutil Process 객체를 재사용하기 위한 모듈 전역 캐시
# (매번 새로 만들면 cpu_percent()가 항상 0.0을 반환하는 문제가 있었음)
_PROCESS_CPU_CACHE = {}


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
