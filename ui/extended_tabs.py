# -*- coding: utf-8 -*-
"""
ui/extended_tabs.py — 확장 기능 5개 탭의 UI 빌더 (MainWindow에 믹스인으로 결합)

의존: config.py, core/*, features/* (단방향 / main_window.py를 import 하지 않는다)

담당 탭
  🧹 블로트웨어 제거 / 🗂 시작 프로그램 / 🎮 성능 & 게이밍 /
  🩺 진단 & 복원 / 🧽 디스크 정리+

⚠️ 이 믹스인은 MainWindow와 결합된 상태에서만 동작한다 (self.settings,
   self.add_history_entry 등 MainWindow의 속성을 사용). 결합은
   ui/main_window.py의 `class MainWindow(ExtendedFeaturesMixin, QMainWindow)`
   에서 이루어진다.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QGroupBox, QListWidget, QListWidgetItem, QProgressBar, QScrollArea,
    QMessageBox, QAbstractItemView,
)

from config import IS_WINDOWS, save_settings
from core.scanner import is_admin
from core.actions import flush_dns
from features.debloat import AppxDebloatThread, set_telemetry_disabled
from features.startup import (
    StartupScanThread, toggle_startup_item, delete_startup_item, open_in_explorer,
)
from features.tweaks import (
    PerfTweakTask, create_ultimate_performance_plan,
    set_multimedia_system_profile, set_high_res_timer, set_priority_separation,
    set_visual_effects_performance, set_game_dvr_disabled,
    set_games_task_profile, set_nagle_low_latency, set_bcd_timer_tweaks,
)
from features.diagnostics import (
    run_sfc_scan, run_dism_scan, RestoreDefaultsThread,
    ExtraCleanScanThread, ExtraCleanRunThread,
)


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
        box_layout.addWidget(QLabel(
            "스캔 후 제거할 앱을 선택하세요. 목록은 게임/작업에 보통 불필요한\n"
            "안전 목록(Cortana, Xbox 오버레이, 당신의 휴대폰 등) 기준으로만 표시됩니다.\n"
            "제거 후에도 Microsoft Store에서 다시 설치할 수 있지만, 이 프로그램에서\n"
            "자동으로 되돌리는 기능은 없습니다."
        ))
        self.debloat_list = QListWidget()
        self.debloat_list.setToolTip("Ctrl/Shift 클릭으로 여러 개를 한 번에 선택할 수 있습니다.")
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
        tel_off_btn.setToolTip(
            "Microsoft로 전송되는 사용정보 수집 서비스(DiagTrack, dmwappushservice)를 끄고,\n"
            "관련 레지스트리 정책 값을 최소 수집으로 설정합니다. Windows 업데이트 자체는\n"
            "계속 정상 동작합니다."
        )
        tel_off_btn.clicked.connect(lambda: self.on_telemetry_toggle(True))
        tel_on_btn = QPushButton("기본값 복원")
        tel_on_btn.setToolTip("차단했던 서비스와 레지스트리 값을 Windows 기본 상태로 되돌립니다.")
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
        toggle_btn.setToolTip(
            "선택한 항목이 Windows 시작 시 자동으로 실행될지 여부를 전환합니다.\n"
            "삭제와 달리 언제든 다시 켤 수 있어 안전합니다."
        )
        toggle_btn.clicked.connect(self.on_startup_toggle)
        delete_btn = QPushButton("삭제")
        delete_btn.setToolTip("자동 실행 등록 자체를 영구히 제거합니다. 프로그램 파일은 삭제되지 않습니다.")
        delete_btn.setObjectName("secondaryButton")
        delete_btn.clicked.connect(self.on_startup_delete)
        open_btn = QPushButton("파일 위치 열기")
        open_btn.setToolTip("선택한 항목이 실제로 실행하는 프로그램 파일의 위치를 탐색기로 엽니다.")
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
        self.cb_net_priority.setToolTip(
            "Windows가 멀티미디어(게임 포함) 작업에 네트워크/CPU 자원을 더 우선적으로\n"
            "배분하도록 레지스트리 값을 조정합니다. NetworkThrottlingIndex를 최대값으로,\n"
            "SystemResponsiveness를 0으로 설정해 백그라운드 작업의 간섭을 줄입니다.\n"
            "관리자 권한이 필요하며, 원클릭 순정 복원으로 되돌릴 수 있습니다."
        )
        self.cb_high_res_timer = QCheckBox("고해상도 타이머 사용 (bcdedit, 재부팅 필요)")
        self.cb_high_res_timer.setToolTip(
            "Windows의 타이머 정밀도를 높여(useplatformclock 비활성화) 입력 지연을\n"
            "줄이는 데 도움이 될 수 있는 설정입니다. 부팅 구성(BCD)을 변경하므로\n"
            "적용/해제 모두 재부팅 후에 실제로 반영됩니다. 관리자 권한이 필요합니다."
        )
        self.cb_priority_sep = QCheckBox("포그라운드 앱 우선 CPU 스케줄링 (Win32PrioritySeparation)")
        self.cb_priority_sep.setToolTip(
            "현재 화면에서 조작 중인(포그라운드) 프로그램에 CPU 시간을 더 길게\n"
            "배정하도록 레지스트리 값을 조정합니다. 게임처럼 포그라운드에서 계속\n"
            "실행되는 프로그램의 체감 반응성을 높이는 데 도움이 됩니다."
        )
        self.cb_visual_fx = QCheckBox("시각 효과 최소화 (성능 우선)")
        self.cb_visual_fx.setToolTip(
            "창 애니메이션, 그림자, 투명 효과 등 화면을 꾸미는 시각 효과를 줄여\n"
            "그래픽 자원을 절약합니다. '제어판 → 시스템 속성 → 성능 우선'과 동일한 효과이며\n"
            "디자인이 단순해지는 대신 체감 반응 속도가 빨라질 수 있습니다."
        )
        self.cb_game_dvr = QCheckBox("Game DVR 비활성화")
        self.cb_game_dvr.setToolTip(
            "Xbox Game Bar의 백그라운드 녹화 기능(Game DVR)을 끕니다.\n"
            "게임 실행 중 자동 녹화로 인한 성능 저하와 오버레이 팝업을 방지합니다."
        )

        # ---- [v2.1.0] 비침습 저지연 튜닝 3종 ----
        self.cb_games_task = QCheckBox("게임 작업 프로필 주입 (SystemProfile\\Tasks\\Games)")
        self.cb_games_task.setToolTip(
            "Windows의 멀티미디어 스케줄러(MMCSS)가 게임 스레드에 적용하는 규칙을 조정합니다.\n"
            "GPU Priority 8 / Priority 6 / Scheduling Category High 를 주입해\n"
            "게임이 스스로 'Games' 범주로 등록한 스레드가 더 우선 처리되도록 합니다.\n"
            "게임이 등록한 스레드에만 적용되므로 다른 프로그램에는 영향이 없습니다.\n"
            "관리자 권한이 필요하며 원클릭 순정 복원으로 되돌릴 수 있습니다."
        )
        self.cb_nagle_off = QCheckBox("Nagle 알고리즘 해제 (TcpAckFrequency / TCPNoDelay)")
        self.cb_nagle_off.setToolTip(
            "작은 TCP 패킷을 모아 보내는 Nagle 알고리즘을 끕니다.\n"
            "조작 입력처럼 작은 패킷을 계속 주고받는 게임에서 최대 200ms까지\n"
            "생기던 대기 시간을 줄일 수 있습니다. 대신 패킷 수가 늘어나므로\n"
            "대역폭이 아주 좁은 회선에서는 권장하지 않습니다.\n"
            "복원 시에는 값을 0으로 덮지 않고 완전히 삭제해 순정 상태로 되돌립니다."
        )
        self.cb_bcd_timer = QCheckBox("BCD 타이머 설정 (disabledynamictick / useplatformtick, 재부팅 필요)")
        self.cb_bcd_timer.setToolTip(
            "부팅 구성(BCD)에서 동적 틱을 끄고 플랫폼 타이머를 틱 소스로 씁니다.\n"
            "타이머 주기가 일정해져 프레임 페이싱의 흔들림(지터)이 줄어듭니다.\n"
            "일부 메인보드에서는 오히려 불안정할 수 있으니, 이상하면 순정 복원으로\n"
            "되돌리세요. 적용/해제 모두 재부팅 후 반영됩니다."
        )

        for cb in (self.cb_net_priority, self.cb_games_task, self.cb_nagle_off,
                   self.cb_bcd_timer, self.cb_high_res_timer, self.cb_priority_sep,
                   self.cb_visual_fx, self.cb_game_dvr):
            box_layout.addWidget(cb)

        safety_note = QLabel(
            "ℹ️ 여기 있는 항목은 모두 Microsoft가 문서화한 레지스트리 값과 bcdedit 옵션입니다.\n"
            "드라이버 후킹이나 커널 조작이 전혀 없어 안티치트가 오탐할 여지가 없고,\n"
            "[🩺 진단 & 복원] 탭의 '원클릭 순정 복원'으로 전부 되돌릴 수 있습니다."
        )
        safety_note.setWordWrap(True)
        safety_note.setStyleSheet("color:#9a9ab0; padding:4px;")
        box_layout.addWidget(safety_note)

        apply_btn = QPushButton("선택 항목 일괄 적용")
        apply_btn.setToolTip("체크한 항목들을 순서대로 적용합니다. 진행 중 오류가 나도 나머지 항목은 계속 시도합니다.")
        apply_btn.clicked.connect(self.on_apply_perf_tweaks)
        box_layout.addWidget(apply_btn)

        self.perf_progress = QProgressBar()
        self.perf_progress.setValue(0)
        box_layout.addWidget(self.perf_progress)
        layout.addWidget(box)

        power_box = QGroupBox("⚡ 전원 옵션")
        power_layout = QVBoxLayout(power_box)
        power_btn = QPushButton("'최고의 성능' 전원 옵션 생성 및 적용")
        power_btn.setToolTip(
            "Windows에 기본적으로 숨겨져 있는 '최고의 성능(Ultimate Performance)'\n"
            "전원 관리 옵션을 새로 만들어 활성화합니다. CPU 절전 기능을 최소화해\n"
            "성능을 우선시하지만, 배터리 소모나 발열이 늘어날 수 있습니다 (데스크톱 권장)."
        )
        power_btn.clicked.connect(self.on_create_ultimate_power_plan)
        power_layout.addWidget(power_btn)
        layout.addWidget(power_box)

        dns_box = QGroupBox("🌐 DNS 캐시")
        dns_layout = QVBoxLayout(dns_box)
        dns_btn = QPushButton("DNS 캐시 플러시 (ipconfig /flushdns)")
        dns_btn.setToolTip("저장된 DNS 조회 기록을 지웁니다. 사이트 접속이 이상할 때 시도해볼 수 있는 안전한 작업입니다.")
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
            tasks.append(("네트워크/CPU 게임 우선 배정", lambda: set_multimedia_system_profile(True)))
        if self.cb_games_task.isChecked():
            tasks.append(("게임 작업 프로필(Tasks\\Games) 주입", lambda: set_games_task_profile(True)))
        if self.cb_nagle_off.isChecked():
            tasks.append(("Nagle 알고리즘 해제", lambda: set_nagle_low_latency(True)))
        if self.cb_bcd_timer.isChecked():
            tasks.append(("BCD 타이머 설정", lambda: set_bcd_timer_tweaks(True)))
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

        # [v2.1.0] QThread 를 매번 새로 만들지 않고 전역 QThreadPool 에 제출한다.
        #   (버튼을 여러 번 눌러도 스레드가 쌓이지 않음 — 자원 누수 방지)
        self._perf_thread = PerfTweakTask(tasks)
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
        sfc_btn.setToolTip(
            "Windows 시스템 파일의 손상 여부를 검사하고 자동으로 복구를 시도하는\n"
            "공식 명령어입니다. 새 관리자 권한 터미널 창에서 실행되며 수 분 정도 걸릴 수 있습니다."
        )
        sfc_btn.clicked.connect(self.on_run_sfc)
        dism_btn = QPushButton("DISM 이미지 복구 실행")
        dism_btn.setToolTip(
            "Windows 구성 요소 저장소(이미지) 자체의 손상을 복구하는 공식 명령어입니다.\n"
            "sfc로 해결되지 않는 심각한 시스템 파일 문제에 사용하며, 인터넷 연결이 필요할 수 있고\n"
            "완료까지 10분 이상 걸릴 수 있습니다."
        )
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
        restore_btn.setToolTip(
            "이 프로그램의 '성능&게이밍', '블로트웨어 제거'(텔레메트리),\n"
            "네트워크(Nagle) 탭 등에서 변경한 레지스트리/서비스 설정을 모두\n"
            "Windows 기본값으로 되돌립니다. 앱 삭제나 휴지통으로 이동한 파일은\n"
            "복원 대상이 아닙니다 (Microsoft Store 재설치 / 휴지통 복구를 이용하세요)."
        )
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
            "Windows Update 캐시와 Prefetch는 관리자 권한이 필요합니다.\n"
            "· Windows Update 캐시: 이미 설치된 업데이트의 다운로드 잔여 파일 (재다운로드 가능)\n"
            "· Prefetch: 프로그램 실행 속도 향상을 위한 시스템 캐시 (삭제해도 자동 재생성됨,\n"
            "  단 정리 직후 해당 프로그램의 첫 실행은 약간 느려질 수 있음)\n"
            "· Brave 캐시: Brave 브라우저의 임시 캐시 파일 (로그인 정보와 무관)"
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
