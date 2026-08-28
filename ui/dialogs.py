# -*- coding: utf-8 -*-
"""
ui/dialogs.py — 공용 팝업 / 오버레이 / 화면 텍스트

의존: config.py, ai/gemini_advisor.py (단방향 / core·features를 알지 못한다)

담당 범위
  - get_help_text(): 설정 탭 도움말에 표시할 탭별 기능 설명 원문
  - load_app_icon(): icon.ico 로드 + 없을 때 시스템 기본 아이콘 fallback
  - PrecheckDialog: 실제 조치 전 대상 목록 확인 + 🤖 AI 안전성 조언
  - ScanningDialog / ProgressDialog: 스캔 인디케이터 / 진행률 창
  - OsdWidget: 실시간 CPU·RAM 플로팅 오버레이
"""

import platform

import psutil

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QDialog, QProgressBar, QScrollArea, QTextEdit,
    QMessageBox, QStyle,
)

from config import (
    NVML_AVAILABLE, SEND2TRASH_AVAILABLE, ICON_FILENAME, resource_path,
)
from ai.gemini_advisor import (
    GeminiAdvisorThread, has_gemini_api_key, get_gemini_api_key,
    make_precheck_summary, NO_API_KEY_MESSAGE,
)


# =====================================================================
# 프로그램 아이콘 로드 (창 / 트레이 공용)
# =====================================================================
def load_app_icon(widget=None) -> QIcon:
    """
    icon.ico를 불러온다. 어떤 이유로든 실패하면 시스템 기본 아이콘
    (SP_ComputerIcon)으로 안전하게 대체한다 — 아이콘 파일이 없다고 해서
    프로그램이 죽거나 아이콘 없이 뜨는 일이 없도록 하기 위함.

    - PyInstaller 단일 실행 파일: sys._MEIPASS 안에서 찾는다
    - 소스 실행: OptiCore.py가 있는 폴더에서 찾는다
    (경로 판단은 config.resource_path()가 담당)
    """
    try:
        icon_path = resource_path(ICON_FILENAME)
        icon = QIcon(icon_path)
        if not icon.isNull():
            return icon
    except Exception:
        pass

    # ---- fallback: 시스템 기본 아이콘 ----
    try:
        style = widget.style() if widget is not None else QApplication.style()
        if style is not None:
            return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    except Exception:
        pass
    return QIcon()


def get_help_text() -> str:
    """[v1.2.0_alpha] 설정 탭 '도움말'에 표시할, 탭/기능별 상세 설명 텍스트.
    새 탭이나 기능을 추가할 때는 이 함수도 함께 갱신하세요."""
    return """\
OptiCore 기능 도움말
=====================================================================
이 화면은 프로그램의 각 탭에 있는 기능이 실제로 무엇을 하는지 자세히
설명합니다. 잘 모르는 기능은 켜기 전에 이 글을 먼저 읽어보세요.

---------------------------------------------------------------------
🚀 원클릭 최적화
---------------------------------------------------------------------
· CPU (우선순위 조정): 백그라운드에서 CPU를 많이 쓰는 프로세스의 '우선순위'만
  낮춥니다. 프로세스를 끄지 않으므로 안전하고, 되돌리기가 가능합니다.
· GPU (정보 조회만): VRAM 사용량을 읽기만 합니다. 아무 것도 변경하지 않습니다.
· RAM (워킹셋 트림): 프로세스가 안 쓰면서 붙잡고 있는 메모리를 반납시킵니다.
· SSD / 브라우저 캐시: 임시 파일을 '휴지통'으로 이동합니다(복구 가능, 영구
  삭제 아님).
· DNS 캐시 초기화: 저장된 사이트 주소 기록을 지웁니다. 위험 없는 작업입니다.
· 최적화 강도(1~3단계): 숫자가 높을수록 더 많은 프로세스/파일을 대상으로
  삼습니다. CPU 우선순위 조정은 2단계부터 동작합니다.
· 게임 부스터: 감시할 게임을 고르면, 감시 시작 시 그 게임의 우선순위를
  올리고 다른 백그라운드 프로그램은 낮춥니다. 게임 종료가 감지되면 자동으로
  원래대로 되돌립니다.
· 자동 스마트 정리: 유휴 시간(자리 비움) 또는 RAM 사용률이 기준을 넘으면
  팝업 없이 조용히 RAM 정리를 실행합니다.
· 🤖 AI 사전 점검: [시작] 후 뜨는 '사전 점검' 창에서 버튼을 누르면, 체크된
  항목들을 Google Gemini가 검토해 [권장 / 주의 / 제외]로 알려줍니다.
  버튼을 누를 때만 전송되며, 보내는 정보는 프로세스 이름과 사용량뿐입니다.
  사용하려면 [⚙️ 설정] 탭에서 Gemini API 키를 먼저 등록해야 합니다.

---------------------------------------------------------------------
📊 성능 대시보드
---------------------------------------------------------------------
· 최적화를 실행한 뒤 실제로 확보된 RAM/CPU/디스크 수치를 보여줍니다.
· "CPU 우선순위 전체 원복": 지금까지 낮춰둔 모든 프로세스 우선순위를 한 번에
  정상으로 되돌립니다.
· "로그 보기": 프로그램이 실제로 수행한 모든 조치의 기록(시간/대상)을 봅니다.
· "휴지통 열기": 정리된 파일들이 이동된 휴지통을 바로 엽니다.

---------------------------------------------------------------------
🎮 성능 & 게이밍 (모두 관리자 권한 필요)
---------------------------------------------------------------------
· 네트워크/CPU 게임 우선 배정: Windows가 멀티미디어(게임)에 자원을 더
  우선적으로 배분하도록 레지스트리를 조정합니다.
· 고해상도 타이머: 입력 지연을 줄이는 데 도움 될 수 있는 부팅 설정입니다.
  재부팅 후에만 실제로 적용/해제됩니다.
· 포그라운드 앱 우선 CPU 스케줄링: 지금 화면에서 쓰고 있는 프로그램에
  CPU 시간을 더 많이 배정합니다.
· 시각 효과 최소화: 창 애니메이션/그림자 등을 꺼서 그래픽 자원을 아낍니다.
· Game DVR 비활성화: Xbox Game Bar의 백그라운드 녹화 기능을 끕니다.
· '최고의 성능' 전원 옵션: Windows에 숨겨진 전원 관리 옵션을 만들어
  적용합니다. 데스크톱에 권장하며, 노트북은 발열/배터리에 유의하세요.

---------------------------------------------------------------------
🧹 블로트웨어 제거
---------------------------------------------------------------------
· Windows 기본 탑재 앱(Cortana, Xbox 오버레이 등) 중 안전 목록에 있는
  것만 골라 제거합니다. 제거 후 Microsoft Store에서 재설치할 수 있습니다.
· 텔레메트리 차단: Microsoft로 전송되는 사용정보 수집 서비스를 끕니다.
  Windows 업데이트 자체는 계속 정상적으로 동작합니다.

---------------------------------------------------------------------
🗂 시작 프로그램
---------------------------------------------------------------------
· Windows 시작 시 자동으로 켜지는 프로그램 목록을 보여줍니다.
· 활성/비활성 전환은 언제든 되돌릴 수 있어 삭제보다 안전합니다.
· 삭제는 자동 실행 등록만 지우며, 프로그램 파일 자체는 지우지 않습니다.

---------------------------------------------------------------------
🧽 디스크 정리+
---------------------------------------------------------------------
· Windows Update 캐시: 이미 설치된 업데이트의 다운로드 잔여 파일입니다
  (필요하면 다시 받아지므로 지워도 안전).
· Prefetch: 프로그램 실행 속도를 위한 캐시로, 지워도 자동 재생성됩니다.
· Brave 캐시: Brave 브라우저의 임시 캐시 파일 (로그인 정보와 무관).

---------------------------------------------------------------------
🩺 진단 & 복원
---------------------------------------------------------------------
· sfc /scannow, DISM: Windows 공식 시스템 파일 검사/복구 도구를 관리자
  권한 터미널에서 실행합니다.
· 원클릭 순정 복원: 이 프로그램의 '성능&게이밍', '텔레메트리 차단',
  'Nagle' 등에서 바꾼 레지스트리/서비스 설정을 모두 Windows 기본값으로
  되돌립니다. (삭제한 앱이나 휴지통으로 이동한 파일은 대상이 아닙니다.)

---------------------------------------------------------------------
💡 전문가 팁 & 네트워크
---------------------------------------------------------------------
· NVIDIA 제어판 / 서비스 관리자 / 시작 앱 설정: Windows·드라이버의 공식
  설정 화면을 바로가기로 열어줄 뿐, 이 프로그램이 직접 값을 바꾸지 않습니다.
· Nagle 비활성화: 네트워크 패킷을 즉시 전송하도록 해 온라인 게임의 체감
  핑을 낮추는 데 도움이 될 수 있습니다. (관리자 권한 필요)
· 복구 지점 생성: 지금 상태를 스냅샷으로 저장해, 나중에 문제가 생기면
  Windows 시스템 복원으로 되돌릴 수 있게 합니다.

---------------------------------------------------------------------
🛡 화이트리스트 관리
---------------------------------------------------------------------
· 여기에 등록한 프로그램(예: discord.exe)은 RAM 정리, CPU 우선순위 조정,
  게임 부스터의 백그라운드 양보 대상에서 항상 제외됩니다.

---------------------------------------------------------------------
⚙️ 설정
---------------------------------------------------------------------
· 테마 선택: 프로그램 색상 테마를 바꿉니다. 즉시 적용되고 재실행해도 유지됩니다.
· 도움말: 지금 보고 있는 이 화면입니다.
· Google Gemini API 설정: AI 사전 점검에 쓸 API 키를 등록합니다.
  - [API 키 저장]: 입력한 키를 optimizer_settings.json 에 저장합니다.
    ⚠️ 이 파일은 GitHub에 올리지 마세요 (.gitignore 필요).
  - [연결 테스트]: 아주 짧은 요청을 보내 키가 실제로 동작하는지 확인합니다.
  - 키는 소스코드에 저장되지 않으며, 환경변수 GEMINI_API_KEY 로 등록해도 됩니다.
· 프로그램 정보: 제작자/버전 정보, 업데이트 내역 보기, 새 버전 확인이
  모두 여기에 모여 있습니다.
"""

# =====================================================================
# 5. 사전 점검 팝업
# =====================================================================
class PrecheckDialog(QDialog):
    """실제 조치 직전, 대상 목록을 사용자에게 확인받는 창.

    [v2.0.0] 여기에 "🤖 AI 사전 점검" 그룹이 추가되었다. 사용자가 원할 때만
    (버튼을 눌렀을 때만) Gemini에 요약을 보내 안전성 조언을 받아온다.
    자동으로 전송하지 않는 이유: 프로세스 목록이 외부로 나가는 일이므로
    항상 사용자의 명시적 동작을 거치도록 하기 위함이다.

    settings 인자를 주지 않으면 AI 그룹은 표시되지 않으며, 나머지 동작은
    v1.x 때와 완전히 동일하다 (하위 호환)."""

    def __init__(self, scan_result: dict, settings: dict = None, intensity: int = 1, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사전 점검 (실제 대상 목록)")
        self.setMinimumSize(580, 620)

        self.scan_result = scan_result
        self.settings = settings if settings is not None else {}
        self.intensity = intensity
        self.ram_checkboxes = {}
        self.cpu_checkboxes = {}
        self._advisor_thread = None

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
            self.dns_checkbox.setToolTip("저장된 DNS 조회 기록을 지웁니다. 시스템에 위험이 없는 안전한 작업입니다.")
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

        # ---- [v2.0.0] 🤖 AI 사전 점검 (Google Gemini) ----
        if settings is not None:
            layout.addWidget(self._build_ai_group())

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

    # -----------------------------------------------------------------
    # [v2.0.0] AI 사전 점검
    # -----------------------------------------------------------------
    def _build_ai_group(self) -> QGroupBox:
        box = QGroupBox("🤖 AI 사전 점검 (Google Gemini)")
        v = QVBoxLayout(box)

        desc = QLabel(
            "체크된 항목이 지금 이 PC에서 건드려도 되는 대상인지 AI에게 물어봅니다.\n"
            "전송되는 정보: 프로세스 이름 / 메모리·CPU 사용량 / 정리 항목 개수\n"
            "(파일 내용이나 개인 문서는 전송하지 않습니다.)"
        )
        desc.setWordWrap(True)
        v.addWidget(desc)

        self.ai_btn = QPushButton("🤖 AI에게 안전성 조언 받기")
        self.ai_btn.setToolTip(
            "체크해 둔 항목 목록을 Gemini에 보내 항목별 [권장 / 주의 / 제외] 판단을 받아옵니다.\n"
            "판단의 최종 권한은 사용자에게 있으며, AI 의견은 참고용입니다.\n"
            "API 키는 [⚙️ 설정] 탭에서 등록합니다."
        )
        self.ai_btn.clicked.connect(self.on_request_ai_advice)
        v.addWidget(self.ai_btn)

        self.ai_result_view = QTextEdit()
        self.ai_result_view.setReadOnly(True)
        self.ai_result_view.setPlaceholderText(
            "아직 AI 조언을 받지 않았습니다. 위 버튼을 누르면 여기에 결과가 표시됩니다."
        )
        self.ai_result_view.setMinimumHeight(120)
        v.addWidget(self.ai_result_view)
        return box

    def on_request_ai_advice(self):
        """[AI 안전성 조언 받기] 버튼 핸들러."""
        # ---- 키 미등록 예외 처리 ----
        if not has_gemini_api_key(self.settings):
            QMessageBox.information(self, "API 키가 필요합니다", NO_API_KEY_MESSAGE)
            return

        ram_selected, cpu_selected, files_selected, browser_selected, dns_selected = self.get_selected()
        if not (ram_selected or cpu_selected or files_selected or browser_selected or dns_selected):
            QMessageBox.information(
                self, "분석할 항목 없음",
                "체크된 항목이 하나도 없습니다. 먼저 분석할 항목을 선택해주세요."
            )
            return

        try:
            mem = psutil.virtual_memory()
            ram_total_mb = round(mem.total / (1024 * 1024))
            ram_used_pct = mem.percent
        except Exception:
            ram_total_mb, ram_used_pct = 0, 0

        summary = make_precheck_summary(
            ram_selected=ram_selected,
            cpu_selected=cpu_selected,
            files_count=len(files_selected),
            browser_count=len(browser_selected),
            dns_selected=dns_selected,
            intensity=self.intensity,
            os_name=platform.platform(),
            ram_total_mb=ram_total_mb,
            ram_used_pct=ram_used_pct,
        )

        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("🤖 분석 중입니다...")
        self.ai_result_view.setPlainText("Gemini에 문의하는 중입니다. 잠시만 기다려주세요...")

        # 네트워크 대기는 반드시 별도 스레드에서 (UI 프리징 방지)
        self._advisor_thread = GeminiAdvisorThread(
            get_gemini_api_key(self.settings), summary, parent=self
        )
        self._advisor_thread.advice_ready.connect(self._on_ai_advice_ready)
        self._advisor_thread.start()

    def _on_ai_advice_ready(self, ok: bool, text: str):
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("🤖 AI에게 안전성 조언 받기 (다시 요청)")
        if ok:
            self.ai_result_view.setPlainText(
                text + "\n\n※ AI의 의견은 참고용입니다. 최종 판단과 체크 해제는 직접 하세요."
            )
        else:
            self.ai_result_view.setPlainText(f"AI 조언을 받지 못했습니다.\n사유: {text}")

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
