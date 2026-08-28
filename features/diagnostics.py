# -*- coding: utf-8 -*-
"""
features/diagnostics.py — 진단 & 복원 + 디스크 정리+

의존: config.py, core/*, features/tweaks.py (단방향)

  - sfc /scannow, DISM 을 별도 관리자 권한 터미널로 실행
  - 원클릭 순정 복원(RestoreDefaultsThread): 이 프로그램이 바꾼 레지스트리/
    서비스/전원 설정을 Windows 기본값으로 되돌린다.
  - 디스크 정리+ : Windows Update 캐시 / Prefetch / Brave 캐시 스캔 및 정리
    (ExtraCleanScanThread, ExtraCleanRunThread)

※ features/tweaks.py 를 import 하는 이유: 순정 복원이 tweaks에서 적용한
  설정들을 그대로 되돌려야 하기 때문. 반대 방향(tweaks → diagnostics)의
  import는 존재하지 않으므로 순환 참조가 아니다.
"""

import os
import subprocess

from PyQt6.QtCore import QThread, pyqtSignal

from config import (
    IS_WINDOWS, SEND2TRASH_AVAILABLE, send2trash,
    save_settings, write_log,
)
from core.scanner import is_admin
from core.actions import _run_cli
from features.debloat import set_telemetry_disabled
from features.tweaks import (
    set_network_gaming_priority, set_high_res_timer, set_priority_separation,
    set_visual_effects_performance, set_game_dvr_disabled,
)


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
