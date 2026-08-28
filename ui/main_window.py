# -*- coding: utf-8 -*-
"""
ui/main_window.py — 메인 윈도우 (10개 탭 조립 + 트레이 + 각종 타이머)

의존: config, themes, updater, core/*, features/*(간접), ai/*, ui/* (단방향)
      → 이 모듈은 프로젝트에서 가장 "위"에 있으며, 아무도 이 모듈을 import 하지 않는다.
        (진입점 OptiCore.py만 예외적으로 MainWindow를 가져다 쓴다)

담당 범위
  - ExtendedFeaturesMixin 결합 및 전체 탭 구성
      🚀 원클릭 최적화 / 📊 성능 대시보드 / 🎮 성능 & 게이밍 /
      🧹 블로트웨어 제거 / 🗂 시작 프로그램 / 🧽 디스크 정리+ /
      🩺 진단 & 복원 / 💡 전문가 팁 & 네트워크 /
      🛡 화이트리스트 관리 / ⚙️ 설정
  - 트레이 아이콘, 게임 부스터 감시 타이머, 자동 스마트 정리 타이머
  - 자동 업데이트 확인/적용 흐름
  - Google Gemini API 설정 UI (키 저장 / 연결 테스트)
"""

import os
import sys
import subprocess
from datetime import datetime

import psutil

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QSlider, QTabWidget, QGroupBox, QFrame,
    QListWidget, QListWidgetItem, QDialog, QProgressBar, QMessageBox,
    QScrollArea, QTextEdit, QComboBox, QSystemTrayIcon, QMenu,
    QLineEdit, QSpinBox,
)

from config import (
    APP_NAME, APP_VERSION, IS_WINDOWS, NVML_AVAILABLE, SEND2TRASH_AVAILABLE,
    LOG_FILE_PATH, load_settings, save_settings, write_log, get_changelog_text,
)
from themes import THEMES, DEFAULT_THEME_KEY, apply_theme
from updater import (
    UpdateCheckThread, UpdateApplyThread, is_newer_version,
    pick_update_asset, get_running_program_path,
)
from core.scanner import (
    ScannerWorker, scan_ram_candidates, scan_cpu_candidates,
    get_watchable_processes, get_idle_minutes, is_admin,
)
from core.actions import (
    OptimizationWorker, instant_cleanup_after_game_exit,
    trim_process_working_set, lower_process_priority, restore_process_priority,
    raise_process_priority, set_nagle, create_restore_point,
)
from ai.gemini_advisor import (
    GeminiConnectionTestThread, get_gemini_api_key, mask_api_key,
    GEMINI_MODEL, GEMINI_API_KEY_ISSUE_URL, NO_API_KEY_MESSAGE,
    GEMINI_FALLBACK_MODELS, is_model_endpoint_error,
)
from ui.dialogs import (
    PrecheckDialog, ScanningDialog, ProgressDialog, OsdWidget,
    get_help_text, load_app_icon,
)
from ui.extended_tabs import ExtendedFeaturesMixin


class MainWindow(ExtendedFeaturesMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — 스마트 시스템 최적화 프로그램")
        # [v2.0.0] icon.ico 적용 (파일이 없으면 시스템 기본 아이콘으로 자동 fallback)
        self.setWindowIcon(load_app_icon(self))
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

        # [v1.2.0_alpha] 자동 업데이트 확인: 켜져 있으면 시작 3초 후 조용히 확인.
        # (시작 직후 바로 네트워크 요청을 하면 다른 초기화와 겹쳐 체감 로딩이
        #  느려 보일 수 있어 약간의 지연을 둠. 새 버전이 없으면 아무 팝업도 뜨지 않음.)
        if self.settings.get("auto_check_update", True):
            QTimer.singleShot(3000, lambda: self.on_check_update(manual=False))

    # -----------------------------------------------------------------
    # 트레이 아이콘 (창을 닫아도 고립되지 않도록)
    # -----------------------------------------------------------------
    def _setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return
        # [v2.0.0] 창 아이콘과 동일한 icon.ico를 트레이에도 사용.
        # load_app_icon()이 실패 시 SP_ComputerIcon으로 알아서 대체해준다.
        icon = load_app_icon(self)
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
        self.cb_cpu.setToolTip(
            "백그라운드에서 CPU를 많이 쓰는 프로세스의 '우선순위'만 낮춥니다.\n"
            "프로세스를 종료하지 않으므로 안전하며, 원클릭 되돌리기가 가능합니다.\n"
            "강도 2단계부터 동작합니다."
        )
        self.cb_gpu = QCheckBox("GPU (정보 조회만)")
        self.cb_gpu.setToolTip(
            "GPU 메모리(VRAM) 사용량을 조회만 합니다. 설정을 바꾸거나 프로세스를\n"
            "종료하지 않는 '읽기 전용' 항목입니다. NVIDIA GPU + pynvml 설치 시에만 동작합니다."
        )
        self.cb_ram = QCheckBox("RAM (워킹셋 트림)")
        self.cb_ram.setToolTip(
            "각 프로세스가 실제로 쓰지 않으면서 붙잡고 있는 메모리(워킹셋)를\n"
            "운영체제에 반납하도록 요청합니다. 프로세스는 종료되지 않으며,\n"
            "필요하면 다시 자동으로 메모리를 할당받으므로 안전합니다."
        )
        self.cb_ssd = QCheckBox("SSD (임시파일 → 휴지통)")
        self.cb_ssd.setToolTip(
            "Windows 임시 폴더(Temp)의 불필요한 캐시 파일을 정리합니다.\n"
            "완전 삭제가 아니라 휴지통으로 이동하므로 필요하면 복구할 수 있습니다."
        )
        self.cb_browser = QCheckBox("브라우저 캐시 (Chrome/Edge)")
        self.cb_browser.setToolTip(
            "Chrome/Edge 브라우저의 캐시 파일을 휴지통으로 이동합니다.\n"
            "로그인 정보나 즐겨찾기에는 영향을 주지 않으며, 다음 접속 시 캐시가\n"
            "다시 쌓이기 때문에 사이트 로딩이 잠깐 느려질 수 있습니다."
        )
        self.cb_dns = QCheckBox("DNS 캐시 초기화")
        self.cb_dns.setToolTip(
            "'ipconfig /flushdns'와 동일한 동작으로, 저장된 DNS 조회 기록을 지웁니다.\n"
            "잘못된 접속 정보가 캐시되어 있을 때 유용하며, 시스템에 위험이 없는 안전한 작업입니다."
        )
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
        self.auto_enable_cb.setToolTip(
            "설정한 유휴 시간(키보드/마우스 조작이 없는 시간)이 지나거나, RAM 사용률이\n"
            "설정한 임계값을 넘으면 팝업 없이 백그라운드에서 RAM 정리를 자동 실행합니다.\n"
            "최소 10분 간격으로만 실행되어 너무 자주 동작하지 않습니다."
        )
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
        # [v2.0.0] 사전 점검 창의 AI 분석에서 "몇 단계 강도인지"를 함께 알려주기 위해 보관
        self._last_intensity = intensity
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

        # [v2.0.0] settings를 넘겨야 사전 점검 창에서 Gemini API 키를 읽어 AI 조언을 쓸 수 있다.
        # 설정에서 AI 사전 점검을 꺼두면 settings=None으로 넘겨 그룹 자체를 숨긴다.
        ai_settings = self.settings if self.settings.get("gemini_precheck_enabled", True) else None
        precheck = PrecheckDialog(
            scan_result,
            settings=ai_settings,
            intensity=getattr(self, "_last_intensity", 1),
            parent=self,
        )
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
        btn1.setToolTip("NVIDIA 그래픽 드라이버의 공식 설정 화면을 엽니다. 이 프로그램이 직접 설정을 바꾸지는 않습니다.")
        btn1.clicked.connect(lambda: os.system("start nvcplui.exe") if IS_WINDOWS else None)
        b1.addWidget(btn1)
        layout.addWidget(box1)

        box2 = QGroupBox("윈도우 서비스 정리")
        b2 = QVBoxLayout(box2)
        b2.addWidget(QLabel("SysMain, DiagTrack 등은 필요시 수동으로 변경하세요."))
        btn2 = QPushButton("서비스 관리자 열기")
        btn2.setToolTip("Windows 공식 서비스 관리 화면(services.msc)을 엽니다.")
        btn2.clicked.connect(lambda: os.system("start services.msc") if IS_WINDOWS else None)
        b2.addWidget(btn2)
        layout.addWidget(box2)

        box3 = QGroupBox("시작 프로그램 정리")
        b3 = QVBoxLayout(box3)
        b3.addWidget(QLabel("불필요한 시작 프로그램을 꺼서 부팅 시간을 줄이세요."))
        btn3 = QPushButton("시작 앱 설정 열기")
        btn3.setToolTip(
            "Windows 공식 시작 앱 설정 화면을 엽니다. 더 상세하게 관리하고 싶다면\n"
            "'🗂 시작 프로그램' 탭에서 개별 항목을 켜고 끌 수 있습니다."
        )
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
        nagle_off_btn.setToolTip(
            "네트워크 인터페이스 레지스트리에 TcpAckFrequency=1, TCPNoDelay=1을 설정해\n"
            "작은 패킷을 모았다가 보내지 않고 즉시 전송하게 합니다. 온라인 게임의\n"
            "체감 핑을 낮추는 데 도움이 될 수 있습니다."
        )
        nagle_off_btn.clicked.connect(lambda: self.on_nagle_toggle(True))
        nagle_on_btn = QPushButton("기본값으로 복원")
        nagle_on_btn.setToolTip("추가했던 레지스트리 값을 삭제해 Windows 기본 네트워크 동작으로 되돌립니다.")
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
        restore_btn.setToolTip(
            "지금 시점의 시스템 설정을 스냅샷으로 저장합니다. 이후 다른 최적화나 튜닝이\n"
            "문제를 일으켰을 때 '이 시점으로 되돌리기'(Windows 시스템 복원)로 복구할 수 있습니다."
        )
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
    # Tab: 설정 (테마 → 도움말 → 프로그램 정보)
    # -----------------------------------------------------------------
    def build_tab_settings(self):
        tab = QWidget()
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        # ---- 1) 테마 선택 ----
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

        # ---- 2) 도움말 ----
        help_box = QGroupBox("❓ 도움말")
        help_layout = QVBoxLayout(help_box)
        help_layout.addWidget(QLabel("각 탭의 기능이 정확히 무엇을 하는지 잘 모르겠다면 아래 버튼을 눌러보세요."))
        help_btn = QPushButton("기능 설명 전체 보기")
        help_btn.clicked.connect(self.on_show_help)
        help_layout.addWidget(help_btn)
        layout.addWidget(help_box)

        # ---- 3) [v2.0.0] Google Gemini API 설정 ----
        gemini_box = QGroupBox("🤖 Google Gemini API 설정")
        gemini_layout = QVBoxLayout(gemini_box)

        gemini_desc = QLabel(
            "키를 등록하면 [🚀 원클릭 최적화]의 사전 점검 창에서 AI에게\n"
            "'이 항목을 정리해도 안전한지' 조언을 받을 수 있습니다.\n"
            f"키 발급: {GEMINI_API_KEY_ISSUE_URL}\n"
            f"사용 모델: {GEMINI_MODEL}  "
            f"(응답하지 않으면 {', '.join(GEMINI_FALLBACK_MODELS)} 순으로 자동 대체)"
        )
        gemini_desc.setWordWrap(True)
        gemini_layout.addWidget(gemini_desc)

        # 비밀번호 마스킹 입력창 — 화면에 키가 그대로 보이지 않게 한다.
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_edit.setPlaceholderText("여기에 Gemini API 키를 붙여넣으세요")
        self.gemini_key_edit.setText(self.settings.get("gemini_api_key", "") or "")
        self.gemini_key_edit.setToolTip(
            "입력한 키는 optimizer_settings.json 에 저장됩니다.\n"
            "이 파일은 절대 GitHub에 커밋하지 마세요 (.gitignore 필요)."
        )
        gemini_layout.addWidget(self.gemini_key_edit)

        gemini_btn_row = QHBoxLayout()
        save_key_btn = QPushButton("💾 API 키 저장")
        save_key_btn.setToolTip("입력한 키를 optimizer_settings.json 에 저장합니다.")
        save_key_btn.clicked.connect(self.on_save_gemini_key)

        test_key_btn = QPushButton("🔌 연결 테스트")
        test_key_btn.setObjectName("secondaryButton")
        test_key_btn.setToolTip(
            "아주 짧은 요청 하나를 보내 키가 실제로 동작하는지 확인합니다.\n"
            "네트워크 대기는 백그라운드 스레드에서 처리되어 창이 멈추지 않습니다."
        )
        test_key_btn.clicked.connect(self.on_test_gemini_connection)

        gemini_btn_row.addWidget(save_key_btn)
        gemini_btn_row.addWidget(test_key_btn)
        gemini_layout.addLayout(gemini_btn_row)

        self.gemini_status_label = QLabel()
        self.gemini_status_label.setWordWrap(True)
        self.gemini_status_label.setStyleSheet("color:#9a9ab0;")
        gemini_layout.addWidget(self.gemini_status_label)
        self._refresh_gemini_status()

        self.gemini_precheck_cb = QCheckBox("사전 점검 창에 AI 조언 기능 표시")
        self.gemini_precheck_cb.setToolTip(
            "끄면 사전 점검 창의 AI 그룹이 나타나지 않습니다. (기존 v1.x와 동일한 화면)"
        )
        self.gemini_precheck_cb.setChecked(self.settings.get("gemini_precheck_enabled", True))
        self.gemini_precheck_cb.stateChanged.connect(self.on_gemini_precheck_setting_changed)
        gemini_layout.addWidget(self.gemini_precheck_cb)

        gemini_note = QLabel(
            "🔒 키는 소스코드에 저장되지 않습니다. optimizer_settings.json 또는\n"
            "환경변수 GEMINI_API_KEY 에서만 읽습니다. 로그에도 기록되지 않습니다.\n"
            "AI 분석 시 프로세스 이름·사용량이 Google 서버로 전송되니 참고하세요."
        )
        gemini_note.setWordWrap(True)
        gemini_note.setStyleSheet("color:#9a9ab0;")
        gemini_layout.addWidget(gemini_note)

        layout.addWidget(gemini_box)

        # ---- 4) 프로그램 정보 (제작자/버전 + 업데이트 내역 + 업데이트 확인) ----
        info_box = QGroupBox("ℹ️ 프로그램 정보")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel(f"{APP_NAME} v{APP_VERSION}"))
        info_layout.addWidget(QLabel("제작자 및 관리자: JeulGemI"))
        info_layout.addWidget(QLabel("공동 협업자: KRJohnWick"))

        changelog_btn = QPushButton("📜 업데이트 내역 보기")
        changelog_btn.clicked.connect(self.on_show_changelog)
        info_layout.addWidget(changelog_btn)

        info_layout.addWidget(QFrame())  # 시각적 구분용 얇은 여백

        self.auto_update_cb = QCheckBox("프로그램 시작 시 자동으로 새 버전 확인")
        self.auto_update_cb.setToolTip("체크해두면 프로그램을 켤 때마다 조용히 GitHub에서 새 버전이 있는지 확인합니다.")
        self.auto_update_cb.setChecked(self.settings.get("auto_check_update", True))
        self.auto_update_cb.stateChanged.connect(self.on_auto_update_setting_changed)
        info_layout.addWidget(self.auto_update_cb)

        self.update_status_label = QLabel("업데이트 상태: 아직 확인하지 않음")
        self.update_status_label.setStyleSheet("color:#9a9ab0;")
        info_layout.addWidget(self.update_status_label)

        update_btn = QPushButton("🔄 지금 업데이트 확인")
        update_btn.setToolTip(
            "GitHub의 최신 릴리스와 현재 버전을 비교합니다.\n"
            "새 버전이 있으면 내려받아 지금 실행 중인 파일 자체를 같은 이름으로 교체할지 물어봅니다\n"
            "(브라우저로 다시 받을 때 생기는 'OptiCore(1)' 같은 이름 중복이 생기지 않습니다)."
        )
        update_btn.clicked.connect(lambda: self.on_check_update(manual=True))
        info_layout.addWidget(update_btn)

        layout.addWidget(info_box)

        layout.addStretch()
        outer_scroll.setWidget(content)
        outer_layout = QVBoxLayout(tab)
        outer_layout.addWidget(outer_scroll)
        return tab

    # -----------------------------------------------------------------
    # [v2.0.0] Google Gemini API 설정 핸들러
    # -----------------------------------------------------------------
    def _refresh_gemini_status(self):
        """현재 키가 어디서 로드되는지(설정 파일/환경변수/없음)를 보여준다.
        키 전체는 절대 표시하지 않고 앞 4자리만 남겨 마스킹한다."""
        saved = (self.settings.get("gemini_api_key", "") or "").strip()
        effective = get_gemini_api_key(self.settings)
        if saved:
            text = f"상태: 설정 파일에 키가 저장되어 있습니다 ({mask_api_key(saved)})"
        elif effective:
            text = f"상태: 환경변수 GEMINI_API_KEY 의 키를 사용 중입니다 ({mask_api_key(effective)})"
        else:
            text = "상태: 등록된 키가 없습니다. AI 기능은 비활성 상태입니다."
        self.gemini_status_label.setText(text)

    def on_save_gemini_key(self):
        key = self.gemini_key_edit.text().strip()
        self.settings["gemini_api_key"] = key
        save_settings(self.settings)
        self._refresh_gemini_status()

        # ⚠️ write_log에 키 자체를 남기지 않는다 (로그 파일 유출 대비)
        write_log("Gemini API 키 " + ("저장됨" if key else "삭제됨"))

        if key:
            QMessageBox.information(
                self, "저장 완료",
                "API 키를 저장했습니다.\n\n"
                "⚠️ optimizer_settings.json 에 평문으로 저장되므로\n"
                "이 파일은 반드시 .gitignore 에 넣어 GitHub에 올리지 마세요."
            )
        else:
            QMessageBox.information(self, "삭제 완료", "저장되어 있던 API 키를 지웠습니다.")

    def on_gemini_precheck_setting_changed(self):
        self.settings["gemini_precheck_enabled"] = self.gemini_precheck_cb.isChecked()
        save_settings(self.settings)

    def on_test_gemini_connection(self):
        """[연결 테스트] — 입력창에 값이 있으면 그 값으로, 없으면 저장된/환경변수 키로 테스트."""
        typed = self.gemini_key_edit.text().strip()
        key = typed or get_gemini_api_key(self.settings)
        if not key:
            QMessageBox.information(self, "API 키가 필요합니다", NO_API_KEY_MESSAGE)
            return

        self.gemini_status_label.setText("상태: 연결 테스트 중입니다...")
        # 네트워크 대기는 QThread로 분리 (UI 프리징 방지)
        self._gemini_test_thread = GeminiConnectionTestThread(key, parent=self)
        self._gemini_test_thread.result_ready.connect(self._on_gemini_test_result)
        self._gemini_test_thread.start()

    def _on_gemini_test_result(self, ok: bool, msg: str):
        if ok:
            QMessageBox.information(self, "연결 테스트 성공", msg)
        elif is_model_endpoint_error(msg):
            # [v2.0.1] 모델 단종(HTTP 404)은 키/네트워크 문제가 아니므로
            #          "키를 확인하세요" 대신 모델 교체를 안내한다.
            QMessageBox.warning(
                self, "연결 테스트 실패 - 모델 엔드포인트 확인 필요",
                f"{msg}\n\n"
                "이 오류는 API 키나 네트워크 문제가 아닙니다.\n"
                "Google이 해당 모델을 종료했을 때 발생합니다.\n"
                "ai/gemini_advisor.py 의 GEMINI_MODEL 상수를 현재 제공 중인\n"
                "모델 이름으로 바꾼 뒤 다시 시도해주세요."
            )
        else:
            QMessageBox.warning(
                self, "연결 테스트 실패",
                f"{msg}\n\n키를 다시 확인하거나 네트워크 상태를 점검해주세요."
            )
        self._refresh_gemini_status()

    def on_show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("도움말 - 기능 설명")
        dlg.resize(640, 560)  # 스크롤 가능 + 위아래 길이 적당하도록 고정 크기
        layout = QVBoxLayout(dlg)
        text_view = QTextEdit()
        text_view.setReadOnly(True)
        text_view.setPlainText(get_help_text())
        layout.addWidget(text_view)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def on_show_changelog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("업데이트 내역")
        dlg.resize(600, 560)  # 스크롤 가능 + 위아래 길이 적당하도록 고정 크기
        layout = QVBoxLayout(dlg)
        text_view = QTextEdit()
        text_view.setReadOnly(True)
        text_view.setPlainText(get_changelog_text())
        layout.addWidget(text_view)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def on_auto_update_setting_changed(self):
        self.settings["auto_check_update"] = self.auto_update_cb.isChecked()
        save_settings(self.settings)

    def on_check_update(self, manual: bool = False):
        """[v1.2.0_alpha] 업데이트 확인 시작 (수동 버튼 / 시작 시 자동 확인 공용)."""
        if hasattr(self, "update_status_label"):
            self.update_status_label.setText("업데이트 상태: 확인 중...")
        self._update_check_thread = UpdateCheckThread()
        self._update_check_thread.result_ready.connect(
            lambda ok, data: self._on_update_check_result(ok, data, manual)
        )
        self._update_check_thread.start()

    def _on_update_check_result(self, ok: bool, data, manual: bool):
        if not ok:
            if hasattr(self, "update_status_label"):
                self.update_status_label.setText(f"업데이트 상태: 확인 실패 ({data})")
            if manual:
                QMessageBox.warning(self, "업데이트 확인 실패", f"GitHub에 연결하지 못했습니다:\n{data}")
            return

        remote_version = data.get("version", "")
        if not remote_version or not is_newer_version(remote_version, APP_VERSION):
            if hasattr(self, "update_status_label"):
                self.update_status_label.setText(f"업데이트 상태: 최신 버전입니다 (v{APP_VERSION})")
            if manual:
                QMessageBox.information(self, "업데이트 확인", "이미 최신 버전을 사용하고 있습니다.")
            return

        if hasattr(self, "update_status_label"):
            self.update_status_label.setText(f"업데이트 상태: 새 버전 발견 (v{remote_version})")

        asset_url = pick_update_asset(data.get("assets", []))
        if not asset_url:
            QMessageBox.information(
                self, "새 버전 발견",
                f"새 버전(v{remote_version})이 있지만 자동으로 받을 파일을 찾지 못했습니다.\n"
                f"GitHub 릴리스 페이지에서 직접 확인해주세요:\n{data.get('html_url', '')}"
            )
            return

        confirm = QMessageBox.question(
            self, "새 버전 발견",
            f"새 버전 v{remote_version}이 있습니다 (현재: v{APP_VERSION}).\n"
            "지금 내려받아 적용하시겠습니까? (실행 파일이 같은 이름으로 교체됩니다)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        target_path = get_running_program_path()
        self._update_apply_thread = UpdateApplyThread(asset_url, target_path)
        self._update_apply_thread.result_ready.connect(self._on_update_apply_result)
        self._update_apply_thread.start()

    def _on_update_apply_result(self, ok: bool, msg: str):
        QMessageBox.information(self, "업데이트 결과", msg)
        if ok:
            restart = QMessageBox.question(
                self, "다시 시작", "지금 프로그램을 다시 시작하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if restart == QMessageBox.StandardButton.Yes:
                self._force_quit = True
                program_path = get_running_program_path()
                try:
                    if getattr(sys, "frozen", False):
                        subprocess.Popen([program_path])
                    else:
                        subprocess.Popen([sys.executable, program_path])
                except Exception as e:
                    QMessageBox.warning(self, "재시작 실패", f"자동 재시작에 실패했습니다. 수동으로 다시 실행해주세요.\n{e}")
                QApplication.quit()
