# -*- coding: utf-8 -*-
"""
features/tweaks.py — 성능 & 게이밍 튜닝 (대부분 관리자 권한 필요)

의존: config.py, core/actions.py (단방향)

  - 네트워크/CPU 게임 우선 배정 (SystemResponsiveness, GPU Priority 등)
  - 고해상도 타이머 (bcdedit useplatformtick)
  - 포그라운드 앱 우선 CPU 스케줄링 (Win32PrioritySeparation)
  - '최고의 성능(Ultimate Performance)' 전원 옵션 생성/적용
  - 시각 효과 최소화, Game DVR 비활성화
  - 위 작업들을 순차 실행하는 PerfTweakThread
"""

from PyQt6.QtCore import QThread, pyqtSignal

from config import IS_WINDOWS, WINREG_AVAILABLE, winreg, write_log
from core.scanner import is_admin
from core.actions import _run_cli, _reg_set


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
