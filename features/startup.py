# -*- coding: utf-8 -*-
"""
features/startup.py — 시작 프로그램 관리

의존: config.py, core/actions.py (단방향)

  - 레지스트리 Run 키 + 시작 폴더를 함께 스캔 (StartupScanThread)
  - 비활성화한 항목은 삭제하지 않고 Run_OptiCoreDisabled 키로 옮겨 보관 →
    언제든 되돌릴 수 있다.
  - 삭제는 "자동 실행 등록"만 지우며 프로그램 파일 자체는 건드리지 않는다.
"""

import os
import subprocess

from PyQt6.QtCore import QThread, pyqtSignal

from config import (
    IS_WINDOWS, WINREG_AVAILABLE, winreg,
    SEND2TRASH_AVAILABLE, send2trash, write_log,
)
from core.actions import _reg_set, _reg_delete_value


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
