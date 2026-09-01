# -*- coding: utf-8 -*-
"""
core/actions.py — 시스템을 실제로 "변경"하는 저수준 동작

의존: config.py, core/scanner.py (단방향)

담당 범위
  - 워킹셋 트림(EmptyWorkingSet), 프로세스 우선순위 조절(nice)
  - 휴지통 이동(Send2Trash), DNS 캐시 플러시, Nagle 알고리즘
  - 시스템 복구 지점 생성
  - 최적화 실행 스레드 OptimizationWorker, 게임 종료 후 즉시 정리
  - features/* 가 공통으로 쓰는 저수준 헬퍼: _run_cli / _reg_set / _reg_delete_value

⚠️ 이 모듈은 UI를 전혀 알지 못한다. 결과는 (성공여부, 메시지) 튜플이나
   시그널로만 돌려주고, 팝업을 띄우는 것은 ui/ 계층의 책임이다.
"""

import os
import time
import subprocess
from datetime import datetime

import psutil

from PyQt6.QtCore import QThread, pyqtSignal

from config import (
    IS_WINDOWS, WINREG_AVAILABLE, winreg,
    SEND2TRASH_AVAILABLE, send2trash,
    write_log,
)
from core.scanner import is_admin, scan_ram_candidates, scan_gpu_info
from core.win32 import empty_working_set


# =====================================================================
# 2. 실제 조치(액션) 함수들
# =====================================================================
def trim_process_working_set(pid: int) -> bool:
    """프로세스를 종료하지 않고 워킹셋(물리 메모리 점유분)만 비운다.

    [v2.1.0] ctypes 호출부를 core/win32.py 로 옮기고 여기서는 위임만 한다.
    예전 구현은 OpenProcess 실패 시 핸들을 닫지 않는 경로가 있었는데,
    win32.ProcessHandle(with 블록)을 쓰면 예외가 나도 반드시 닫힌다.

    ⚠️ 게임 실행 중에는 이 함수를 주기적으로 호출하지 말 것.
       (자세한 이유는 features/game_booster.py 상단 주석 참고)
    """
    return empty_working_set(pid)


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
    """게임 프로세스의 우선순위를 한 단계(Above Normal) 높인다.

    ⚠️ [v2.1.0] 게임 부스터의 기본 경로에서는 더 이상 이 함수를 쓰지 않는다.
       우선순위를 올리면 렌더 스레드가 오디오/입력 스레드를 굶겨 "프레임은
       나오는데 소리가 끊기는" 증상이 생기기 때문이다. 기본 동작은
       features/game_booster.stabilize_game_priority() 의 Normal 안정화다.
       이 함수는 사용자가 설정에서 명시적으로 허용했을 때만 호출되며,
       어떤 경우에도 High/Realtime 으로는 올라가지 않는다.
    """
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
        # [v2.1.0] CREATE_NO_WINDOW 를 줘서 PowerShell 콘솔 창이 번쩍이지 않게 한다.
        #   복구 지점 생성은 WMI(SystemRestore) 호출이라 순수 ctypes 로는 대체가
        #   번거로워, 이 항목만 예외적으로 PowerShell 을 유지한다.
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "Checkpoint-Computer -Description 'OptiCore' -RestorePointType 'MODIFY_SETTINGS'"
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            creationflags=0x08000000 if IS_WINDOWS else 0,
        )
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
