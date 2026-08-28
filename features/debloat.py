# -*- coding: utf-8 -*-
"""
features/debloat.py — 블로트웨어 제거 & 텔레메트리 차단

의존: config.py, core/actions.py (단방향)

  - 설치된 AppX 중 "안전 목록"에 있는 것만 스캔/제거 (AppxDebloatThread)
  - 텔레메트리 서비스(DiagTrack 등) 중지 + 레지스트리 차단
"""

from PyQt6.QtCore import QThread, pyqtSignal

from config import IS_WINDOWS, WINREG_AVAILABLE, winreg, write_log
from core.scanner import is_admin
from core.actions import _run_cli, _reg_set, _reg_delete_value


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
