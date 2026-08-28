# -*- coding: utf-8 -*-
"""
updater.py — 공개(Public) GitHub Releases 기반 자동 업데이트

의존: config.py 만 (단방향)

배포된 .exe(또는 이 소스 그대로)가 실행되는 동안, GitHub의 최신 릴리스와
버전을 비교해 새 버전이 있으면 물어보고 자동으로 내려받아 "같은 경로/같은
파일명"으로 교체한다. 브라우저로 직접 재다운로드할 때 생기는
"OptiCore(1).exe" 같은 이름 중복 문제를 피할 수 있다.
실제 반영은 프로그램을 다시 시작해야 적용된다 (재시작 여부는 사용자에게 확인).

토큰 불필요: 공개 저장소의 Releases API만 사용하므로 인증 정보가 필요 없다.
안전 장치: .py는 교체 전 compile()로 문법 검증 + 교체 직전 .bak 백업 생성.
"""

import os
import sys
import json
import urllib.request
import urllib.error

from PyQt6.QtCore import QThread, pyqtSignal

from config import GITHUB_API_LATEST_RELEASE, get_entry_point_path, write_log


# =====================================================================
# [v1.2.0_alpha] 자동 업데이트 기능
# =====================================================================
# 배포된 .exe(또는 이 .py 파일 그대로)가 실행되는 동안, GitHub의 최신 릴리스와
# 버전을 비교해 새 버전이 있으면 물어보고 자동으로 내려받아 "같은 경로/같은
# 파일명"으로 교체합니다. 브라우저로 직접 재다운로드할 때 생기는
# "OptiCore(1).exe" 같은 이름 중복 문제를 피할 수 있습니다.
# 실제 반영은 프로그램을 다시 시작해야 적용됩니다 (재시작 여부는 사용자에게 확인).

def _parse_version_tuple(version_str: str):
    """'1.2.0_alpha' -> ((1, 2, 0), 'alpha') 형태로 분리한다."""
    base, _, suffix = (version_str or "").partition("_")
    try:
        parts = tuple(int(p) for p in base.split("."))
    except ValueError:
        parts = (0, 0, 0)
    return parts, suffix


def is_newer_version(remote_version: str, local_version: str) -> bool:
    """remote_version이 local_version보다 최신인지 판단한다.
    숫자(MAJOR.MINOR.PATCH)가 더 크면 최신이고, 숫자가 같다면 접미사가 없는
    정식판이 접미사(_alpha 등)가 붙은 버전보다 더 최신인 것으로 취급한다."""
    r_parts, r_suffix = _parse_version_tuple(remote_version)
    l_parts, l_suffix = _parse_version_tuple(local_version)
    if r_parts != l_parts:
        return r_parts > l_parts
    return (not r_suffix) and bool(l_suffix)


def get_running_program_path() -> str:
    """현재 실행 중인 프로그램 자기 자신의 실제 경로.
    PyInstaller 등으로 빌드된 .exe라면 그 exe 경로, 아니라면 진입점 OptiCore.py 경로.

    ⚠️ [v2.0.0 모듈 분리 시 주의] 예전에는 이 함수가 os.path.abspath(__file__)을
    썼지만, 이제 __file__은 "updater.py"를 가리킨다. 그대로 뒀다면 업데이트가
    OptiCore.py 대신 updater.py를 덮어써서 프로그램이 망가졌을 것이다.
    그래서 config.get_entry_point_path()로 진입점 경로를 받아 쓴다."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return get_entry_point_path()


def check_latest_release():
    """GitHub 최신 릴리스 정보를 조회한다. 실패해도 예외를 던지지 않고 (False, 사유)를 반환."""
    try:
        req = urllib.request.Request(
            GITHUB_API_LATEST_RELEASE,
            headers={"User-Agent": "OptiCore-UpdateChecker", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        tag = (data.get("tag_name") or "").lstrip("vV")
        return True, {
            "version": tag,
            "assets": data.get("assets", []) or [],
            "html_url": data.get("html_url", ""),
            "notes": data.get("body", "") or "",
        }
    except Exception as e:
        return False, str(e)


def pick_update_asset(assets: list):
    """실행 형태(exe/py)에 맞는 다운로드 URL을 릴리스 에셋 목록에서 찾는다."""
    is_frozen = getattr(sys, "frozen", False)
    preferred_ext = ".exe" if is_frozen else ".py"
    for asset in assets:
        name = (asset.get("name") or "").lower()
        if name.endswith(preferred_ext):
            return asset.get("browser_download_url")
    return None


def download_and_apply_update(download_url: str, target_path: str):
    """
    새 버전 파일을 내려받아 실행 중인 파일 자체를 안전하게 교체한다.
    - .py 파일이면 교체 전에 문법 검증(compile)까지 수행해 손상된 파일로
      바뀌는 사고를 방지한다.
    - 교체 직전 기존 파일을 .bak으로 백업해두어 문제가 생기면 수동 복구가 가능하다.
    """
    try:
        req = urllib.request.Request(
            download_url, headers={"User-Agent": "OptiCore-UpdateChecker"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            new_content = resp.read()
        if not new_content:
            return False, "다운로드한 내용이 비어 있습니다."

        if target_path.lower().endswith(".py"):
            try:
                compile(new_content.decode("utf-8", errors="ignore"), target_path, "exec")
            except SyntaxError as e:
                return False, f"다운로드한 파일이 손상되었을 수 있습니다 (문법 오류: {e})"

        tmp_path = target_path + ".new"
        with open(tmp_path, "wb") as f:
            f.write(new_content)

        backup_path = target_path + ".bak"
        try:
            if os.path.exists(target_path):
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.replace(target_path, backup_path)
        except Exception:
            pass  # 백업 실패는 치명적이지 않으므로 무시하고 계속 진행

        os.replace(tmp_path, target_path)
        write_log(f"자동 업데이트 적용 완료: {target_path}")
        return True, "새 버전을 내려받아 적용했습니다. 프로그램을 다시 시작해주세요."
    except Exception as e:
        return False, str(e)

class UpdateCheckThread(QThread):
    """[v1.2.0_alpha] GitHub 최신 릴리스 조회를 백그라운드에서 수행 (네트워크 지연으로 UI가 멈추지 않도록)."""
    result_ready = pyqtSignal(bool, object)

    def run(self):
        ok, data = check_latest_release()
        self.result_ready.emit(ok, data)


class UpdateApplyThread(QThread):
    """[v1.2.0_alpha] 새 버전 다운로드 + 파일 교체를 백그라운드에서 수행."""
    result_ready = pyqtSignal(bool, str)

    def __init__(self, download_url: str, target_path: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_path = target_path

    def run(self):
        ok, msg = download_and_apply_update(self.download_url, self.target_path)
        self.result_ready.emit(ok, msg)
