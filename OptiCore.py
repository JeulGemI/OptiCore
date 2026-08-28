# -*- coding: utf-8 -*-
"""
=====================================================================
 ⚠️ 이 파일을 처음 여는 Claude(또는 다른 작업자)는 아래 내용을 먼저 읽으세요
=====================================================================
 제작자 및 관리자: JeulGemI
 공동 협업자: KRJohnWick

 이 파일은 GitHub에 소스로 공개되고, 사용자가 이를 .exe로 빌드해 배포합니다.
 즉 여기서 만든 코드가 그대로 최종 배포판의 기반이 됩니다. 아래 원칙을
 반드시 지켜서 작업하세요.

 1. [기준 코드 원칙] 사용자는 여러 Claude 계정을 돌려가며 이 프로그램을
    수정합니다. 즉 지금 이 파일이 "가장 최신"이 아닐 수 있습니다.
    → 수정/업데이트 요청을 받으면, 사용자가 대화 중 새로 전달한
      'OptiCore.py' 코드가 있다면 그것을 기준(base)으로 삼아 그 위에
      요청 사항을 구현하세요. 자신의 기억 속 이전 버전을 기준으로 삼지 마세요.
    → 예외는 MAJOR 버전이 오르는 "대격변" 패치뿐입니다. 이 경우에만
      구조를 전면 재설계해도 됩니다.
    → [v2.0.0부터] 프로그램이 여러 모듈 파일로 분리되었습니다. 이제 "기준
      코드"는 이 파일 하나가 아니라 아래 [모듈 구조] 전체입니다. 코드를
      전달받을 때 일부 모듈만 왔다면, 빠진 모듈은 임의로 새로 만들지 말고
      사용자에게 해당 파일을 요청하세요.
 2. [파일명 고정] 실제 진입점 파일명은 항상 "OptiCore.py"로 고정합니다.
    버전이 올라가도 파일명은 절대 바꾸지 않습니다.
    (예: OptiCore_V1.0.py, OptiCore_v2.py 같은 형식 금지)
    사용자가 다른 계정에서 받은 코드의 파일명이 이 규칙과 다르면
    (예: OptiCore_V1_0.py), 작업 결과물은 다시 "OptiCore.py"로 저장하세요.
    분리된 모듈 파일명(config.py, themes.py, core/…, ui/… 등)도 그대로
    유지하세요. 바꾸면 import 경로가 전부 깨집니다.
 3. [버전 갱신] 아래 [버전 표기 규칙]에 따라 config.py의 APP_VERSION 상수,
    창 제목, 그리고 이 헤더의 [변경 이력]을 매번 함께 갱신하세요. 주석만
    바꾸는 작업(문서 정책 변경 등)도 "업데이트"로 취급해 PATCH를 올리고
    변경 이력에 기록하세요.
    ※ v2.0.0부터 APP_VERSION 상수의 실제 위치는 config.py입니다.
      (창 제목은 config.APP_NAME / APP_VERSION을 읽어 자동으로 표시됩니다)
 4. [변경 이력 유지] 새 항목은 항상 맨 위에 추가하고, 목록이 너무
    길어지면 오래된 항목을 요약해서 정리하세요. 절대 삭제로 역사를
    지우지 마세요.
 5. [헤더 보존] 이 최상단 안내문 전체(제작자/협업자 정보, 파일명 규칙,
    버전 표기 규칙, 미완료 접미사 규칙, [AI 연동 예정 메모], [변경 이력])는
    다음 세션이 계속 읽고 이어서 작업할 수 있도록 항상 이 진입점 파일
    (OptiCore.py) 상단에 온전히 남겨두세요. 다른 모듈로 옮기지 마세요.

=====================================================================
 OptiCore - 스마트 시스템 최적화 프로그램
 제작자 및 관리자: JeulGemI
 공동 협업자: KRJohnWick
 현재 버전: v2.0.0
=====================================================================
 [파일명 규칙]
   실제 진입점 파일명은 항상 "OptiCore.py"로 고정합니다. 버전이 올라가도
   파일명은 바꾸지 않습니다 (예: OptiCore_V1.0.py 같은 형식 금지).
   버전 표시는 config.py의 APP_VERSION 상수 + 창 제목 + 이 헤더의
   [변경 이력]에서만 관리합니다. 사용자가 다른 계정에서 받은 코드를 붙여줄 때
   파일명이 이 규칙과 다르면(OptiCore_V1_0.py 등) 응답 코드에서는
   "OptiCore.py"로 되돌려서 저장하세요.

 [버전 표기 규칙]
   형식: MAJOR.MINOR.PATCH (예: 1.0.0, 1.0.1, ..., 1.0.13, 1.1.0, 1.12.3, 2.0.0)
   - PATCH (세 번째 숫자): 자잘한 버그 수정/문서 갱신 등 소규모 변경 시 +1
     (예: 1.0.0 -> 1.0.1 -> ... -> 1.0.13)
   - MINOR (두 번째 숫자): 기능 추가 시 +1, PATCH는 0으로 리셋 (예: 1.0.13 -> 1.1.0)
   - MAJOR (첫 번째 숫자): 구조 전면 개편 등 대격변 시 +1, MINOR/PATCH 모두 0으로 리셋
     (예: 1.x.x -> 2.0.0). 대격변 패치일 때만 "기준 코드 원칙"의 예외로,
     기존 코드 구조를 전면 재설계해도 됩니다.
   업데이트할 때마다 이 헤더의 "버전"(및 config.py의 APP_VERSION 상수)과 아래
   "변경 이력"을 함께 갱신합니다. 변경 이력은 최신 버전이 맨 위로 오도록
   추가하고, 너무 길어지면 오래된 항목은 요약합니다.

   [미완료 접미사 규칙] 사용자가 한 번에 요청한 업데이트 사항들을 전부 구현하지
   못하고 일부만 반영한 채로 버전을 올려야 할 때는, 다음 정식 버전 번호 뒤에
   그리스 문자 발음을 소문자 언더스코어로 붙입니다: _alpha, _beta, _gamma,
   _delta ... 순서로 사용합니다.
     예) 1.3.4_alpha, 2.5.10_beta
   이후 나머지 요청 사항까지 전부 완료되면, 접미사를 뗀 정식 버전 번호로
   갱신합니다 (숫자 자체는 올리지 않음). 예) 1.3.4_alpha -> 1.3.4
   같은 정식 버전 번호에서 미완료 상태가 반복되면 접미사만 다음 그리스 문자로
   바꿉니다 (예: 1.3.4_alpha -> 1.3.4_beta), 번호 자체는 바꾸지 않습니다.
   is_newer_version() 함수는 숫자가 같을 때 접미사 없는 정식판을 접미사가
   붙은 버전보다 더 최신으로 판단하므로, 이 규칙을 그대로 따르면 자동
   업데이트 확인 기능과도 어긋나지 않습니다.

 [배포 안내]
   이 프로그램은 GitHub 저장소 "OptiCore"에서 .exe로 빌드되어 배포됩니다.
   저장소: https://github.com/JeulGemI/OptiCore
   Claude가 수정한 코드는 사용자가 이후 GitHub에 반영합니다.

 =====================================================================
 [모듈 구조 — v2.0.0에서 분리됨]
 =====================================================================
   OptiCore.py            진입점(main). 이 헤더 주석의 원본 보관소이자
                          QApplication 실행 담당. 로직은 두지 않는다.
   config.py              전역 상수(APP_VERSION 등), 설정 파일 로드/저장,
                          로그(write_log), 리소스 경로 헬퍼(resource_path),
                          .gitignore 보안 가이드
   themes.py              테마 8종 정의(THEMES) + QSS 생성기(make_theme_qss)
   updater.py             공개 GitHub Releases 조회/다운로드/안전 교체
                          (UpdateCheckThread, UpdateApplyThread)
   core/scanner.py        CPU·RAM·SSD·브라우저·GPU 스캔, 권한/유휴시간 조회,
                          ScannerWorker (읽기 전용)
   core/actions.py        워킹셋 트림, 우선순위 조절, 휴지통 이동, DNS 플러시,
                          Nagle, 복구 지점, OptimizationWorker,
                          공용 헬퍼 _run_cli/_reg_set/_reg_delete_value
   features/debloat.py    AppX 블로트웨어 스캔·제거, 텔레메트리 차단
   features/startup.py    시작 프로그램 스캔/토글/삭제
   features/tweaks.py     게이밍 네트워크·CPU 우선순위, 고해상도 타이머,
                          전원 옵션, 시각 효과, Game DVR
   features/diagnostics.py sfc/DISM, 원클릭 순정 복원, 디스크 정리+
   ai/gemini_advisor.py   Google Gemini API 연동 (사전 점검 안전성 조언)
   ui/dialogs.py          사전 점검/진행률/스캔 팝업, OSD 위젯, 도움말 원문,
                          아이콘 로더(load_app_icon)
   ui/extended_tabs.py    확장 기능 5개 탭 UI 빌더(ExtendedFeaturesMixin)
   ui/main_window.py      MainWindow — 10개 탭 조립, 트레이, 타이머

   [import 방향 — 순환 참조 금지]
     config  ←  themes / updater / core / ai
     core/scanner  ←  core/actions  ←  features/*
     features/tweaks, features/debloat  ←  features/diagnostics
     config, ai  ←  ui/dialogs
     config, core, features  ←  ui/extended_tabs
     위 전부  ←  ui/main_window  ←  OptiCore.py
   화살표는 "왼쪽이 오른쪽에 의해 import 됨"을 뜻합니다. 역방향 import를
   추가하면 즉시 순환 참조가 되므로 절대 만들지 마세요. 하위 모듈에서
   상위(UI) 기능이 필요해 보이면, 값을 반환해 상위가 처리하게 하세요.

 =====================================================================
 [AI 연동 예정 메모 — 다른 Claude 세션은 이 섹션을 읽고 참고할 것]
 =====================================================================
 상태: ✅ Google Gemini API 연동은 v2.0.0에서 **구현 완료**되었습니다.
   (v1.2.0 시점의 "예정" 메모는 아래 구현 설명으로 대체되었습니다.)
 구현 위치: ai/gemini_advisor.py
   - GeminiAdvisorThread: 사전 점검(Precheck) 창에서 사용자가 체크한
     프로세스/정리 항목을 요약해 Gemini에 보내고, 항목별
     [권장 | 주의 | 제외] 판단과 종합 의견을 받아온다.
   - GeminiConnectionTestThread: 설정 탭 [연결 테스트] 버튼 전용.
   - 두 스레드 모두 QThread 기반이라 응답을 기다리는 동안 UI가 멈추지 않는다
     (UpdateCheckThread/UpdateApplyThread와 동일한 기존 관례).
 통합 지점: ui/dialogs.py의 PrecheckDialog 안 "🤖 AI 사전 점검" 그룹
   → MainWindow.on_scan_finished()가 PrecheckDialog에 settings를 넘겨준다.
 API 키 정책 (중요):
   - 소스코드 하드코딩 절대 금지. 키는 optimizer_settings.json의
     "gemini_api_key" 또는 환경변수 GEMINI_API_KEY 에서만 읽는다.
   - 키는 URL 쿼리스트링이 아니라 x-goog-api-key 헤더로 전송한다.
   - optimizer_settings.json / optimizer_log.txt 는 반드시 .gitignore 처리
     (가이드는 config.py 최상단 주석에 있음).
   - 로그·오류 메시지에 키가 남지 않도록 마스킹 처리되어 있다.
 모델 수명 정책 (v2.0.1 추가 — 다음 세션은 반드시 읽을 것):
   - Google은 Gemini 모델을 주기적으로 종료(shut down)하며, 종료된 모델로
     요청하면 HTTP 404 "This model ... is no longer available" 가 돌아온다.
     실제로 v2.0.0의 gemini-2.0-flash가 2026-06-01자로 종료돼 404가 났다.
   - 모델을 바꿀 때는 ai/gemini_advisor.py 의 GEMINI_MODEL 상수 한 줄만
     고치면 된다. UI 라벨은 이 상수를 읽어 자동으로 갱신된다.
   - 새 모델을 고르기 전에 아래 문서에서 "현재 제공 중인지 + 종료 예정일이
     충분히 남았는지"를 반드시 확인할 것. 기억에 의존하지 말 것.
       모델 목록: https://ai.google.dev/gemini-api/docs/models
       단종 일정: https://ai.google.dev/gemini-api/docs/deprecations
   - 이미 종료된 모델(참고): gemini-1.5-*(2025-09-29),
     gemini-2.0-flash / 2.0-flash-lite(2026-06-01).
     종료 예정: gemini-2.5-flash(2026-10-16 예정).

 [향후 계획 — 프로그래밍 언어 변경]
   ▶ 이 프로그램은 장기적으로 **C#으로 언어를 변경할 예정**입니다.
     다만 다음 업데이트에서 곧바로 C#으로 전환하는 것은 아니며,
     "때가 되면" 전환합니다. 그 시점까지는 계속 Python(PyQt6) 기준으로
     기능을 추가/수정하세요.
     → 다음 Claude 세션은 사용자가 명시적으로 "이제 C#으로 옮기자"라고
       요청하기 전까지는 임의로 C# 변환 작업을 시작하지 마세요.
     → 전환을 대비해, 새 기능은 되도록 UI(ui/)와 로직(core/·features/)을
       섞지 말고 지금처럼 계층을 분리해 두는 편이 이후 이식에 유리합니다.

 [필요 라이브러리 설치]
   pip install PyQt6 psutil Send2Trash
   (선택) NVIDIA GPU 정보: pip install nvidia-ml-py
   ※ Gemini 연동은 표준 라이브러리(urllib)만 사용하므로 추가 설치가 없습니다.

 =====================================================================
 [변경 이력]
 =====================================================================
 v2.0.1 (버그 수정 — Gemini 모델 단종으로 인한 HTTP 404 해결)
   - [증상] 설정 탭 [연결 테스트]에서 다음 오류가 발생했다.
       "HTTP 404: This model models/gemini-2.0-flash is no longer available..."
   - [원인] Google이 gemini-2.0-flash / 2.0-flash-lite 를 2026-06-01자로
     완전히 종료(shut down)했다. 종료된 모델로 요청하면 404가 돌아온다.
     참고로 gemini-1.5-flash 계열도 2025-09-29에 이미 종료되어 대안이 못 된다.
   - [수정 1 — 모델 교체] ai/gemini_advisor.py 의 GEMINI_MODEL 을
     "gemini-2.0-flash" → "gemini-3.5-flash" 로 변경. Google이 2.0-flash의
     공식 대체 모델로 안내하는 모델이다.
     ※ 요청서에는 gemini-2.5-flash가 적혀 있었으나, 이 모델도 2026-10-16
       종료가 예고되어 있고 그 전에 같은 404가 난다는 보고가 있어 기본값에서
       제외하고 아래 자동 대체 목록의 마지막 후보로만 남겼다.
   - [수정 2 — 자동 대체(fallback)] 같은 사고가 반복되어도 프로그램이 계속
     동작하도록, 기본 모델이 404면 GEMINI_FALLBACK_MODELS
     (gemini-flash-latest → gemini-3.6-flash → gemini-2.5-flash)를 순서대로
     시도한다. 그것도 전부 실패하면 ListModels API로 실제 사용 가능한 모델을
     자동 탐색해 한 번 더 시도한다(discover_available_model). 키 오류·네트워크
     오류처럼 모델과 무관한 실패는 재시도하지 않고 즉시 반환한다.
   - [수정 3 — 예외 처리 보강] HTTP 404(또는 "no longer available" 문구)일 때
     "[모델 엔드포인트 확인 필요]" 표식과 함께 원인·해결 방법·모델 목록/단종
     일정 문서 링크를 담은 메시지를 출력한다. is_model_endpoint_error()를
     추가해 UI가 오류 종류를 구분하고, 이 경우에는 "키를 확인하세요" 대신
     모델 교체를 안내하는 별도 팝업을 띄운다.
   - [수정 4 — UI 표기] 설정 탭 라벨이 하드코딩 대신 GEMINI_MODEL 상수와
     자동 대체 목록을 함께 표시하도록 변경. 연결 테스트가 대체 모델로
     성공한 경우 어떤 모델로 연결됐는지와 상수 갱신 방법을 알려준다.
   - [부수 수정] generationConfig에서 temperature 제거(2026-07-21자 Deprecated),
     maxOutputTokens 1024 → 4096 상향(Gemini 3 계열은 thinking 토큰이 같은
     한도를 소모해 본문이 빈 채로 반환되는 문제가 있음), finishReason이
     MAX_TOKENS/SAFETY일 때의 안내 문구 추가, 5xx 오류 안내 분리.
   - [유지] API 키는 요청서의 URL 예시(?key=...)와 달리 기존대로
     x-goog-api-key 헤더로 전송한다. 쿼리스트링은 프록시/서버 접근 로그에
     평문으로 남아 이 파일 [AI 연동 예정 메모]의 키 보안 원칙에 어긋난다.
   - 버그 수정이므로 PATCH만 올림 (2.0.0 -> 2.0.1).

 v2.0.0 (대격변 — 모듈 트리 분리 + Gemini 연동 + 아이콘 리소스 지원)
   작업자: 공동 협업자 KRJohnWick
   - [구조 개편] 단일 파일(약 4,000줄)이던 프로그램을 역할과 탭(도메인)
     기준의 계층형 모듈 트리로 분리. 진입점 OptiCore.py는 헤더 주석 보존과
     QApplication 실행만 담당한다. 전체 구조와 import 방향은 위 [모듈 구조]
     섹션 참고. 기존 기능(RAM 트림, CPU 정규화 스캔, 게임 부스터, OSD 오버레이,
     블로트웨어 제거, 시작프로그램, 게이밍 튜닝, 진단/복원, 디스크 정리+,
     화이트리스트, 다중 테마, 도움말, 자동 업데이트)은 하나도 빠짐없이 보존.
     MAJOR 버전을 올리는 "대격변"에 해당하므로 1.2.0 -> 2.0.0.
   - [분리 과정에서 발견/수정한 결함 3건]
     · get_running_program_path()가 os.path.abspath(__file__)을 쓰고 있어,
       모듈 분리 후 그대로 뒀다면 자동 업데이트가 OptiCore.py가 아니라
       updater.py를 덮어쓸 뻔했음 → config.get_entry_point_path() 사용으로 변경.
     · get_changelog_text()가 자기 모듈의 __doc__를 읽는 구조라 분리 후
       빈 값이 될 뻔했음 → OptiCore.py가 시작 시 헤더 주석을 config에
       등록(register_entry_point)하고 그 값을 읽도록 변경. 파일에서 직접
       파싱하는 예비 경로도 추가.
     · PROTECTED_PROCESSES에 옛 파일명 "opticore_v1.0.py"가 남아 있어 정작
       현재 이름은 보호되지 않았음 → "opticore.py"/"opticore.exe"로 교정.
   - [Gemini 연동] ai/gemini_advisor.py 신설. 원클릭 최적화 사전 점검 창에
     "🤖 AI 사전 점검" 그룹을 추가해, 체크된 프로세스/정리 항목의 안전성을
     Gemini가 [권장|주의|제외]로 판단해준다. QThread 기반이라 UI가 멈추지 않음.
   - [API 키 보안] 키 하드코딩 없음. optimizer_settings.json의
     "gemini_api_key" 또는 환경변수 GEMINI_API_KEY에서만 로드. 설정 탭에
     'Google Gemini API 설정' 그룹(비밀번호 마스킹 입력창 + [API 키 저장] +
     [연결 테스트]) 추가. 키 미등록 상태로 AI 분석을 누르면 설정 탭 등록을
     안내하는 팝업이 뜬다. 키는 헤더로 전송하고 로그/오류 메시지에서 마스킹.
     .gitignore 가이드 주석을 config.py 상단에 명시.
   - [자동 업데이트] GITHUB_OWNER/GITHUB_REPO를 실제 공개 저장소
     (JeulGemI/OptiCore)로 확정. 토큰 없이 공개 Releases API 사용.
     기존 안전 로직(에셋 자동 선택, .py 문법 검증 compile, .bak 백업,
     같은 이름으로 교체, 재시작 확인)은 그대로 유지.
   - [아이콘 리소스] config.resource_path() 추가로 PyInstaller
     단일 실행 파일(sys._MEIPASS)과 소스 실행 양쪽에서 icon.ico를 안전하게
     로드. ui.dialogs.load_app_icon()이 창 아이콘과 트레이 아이콘에 공통
     적용되며, 파일이 없거나 손상되면 시스템 기본 아이콘(SP_ComputerIcon)으로
     조용히 fallback 한다.
   - [AI 연동 예정 메모 갱신] Gemini 연동 완료 내용으로 교체하고,
     "때가 되면 C#으로 프로그래밍 언어 변경 예정(다음 업데이트에 즉시
     전환하는 것은 아님)" 항목을 추가.

 v1.2.0 (UI 편의성 개편 + 도움말 + 자동 업데이트 + AI 연동 메모 + 최종 점검)
   - [기능 설명] 모든 탭의 체크박스/버튼에 상세 설명 툴팁(setToolTip) 추가.
   - [설정 탭 개편] 순서를 테마 선택 → 도움말 → 프로그램 정보로 재배치.
     "업데이트 내역"을 프로그램 정보 안 버튼(스크롤 가능한 640x560 팝업)으로 통합.
     새로 "❓ 도움말" 버튼 추가: get_help_text()로 탭별 기능을 자세히 설명.
   - [자동 업데이트] GitHub 최신 릴리스를 조회해 새 버전이 있으면 물어보고
     내려받아 실행 파일 자체를 같은 경로/이름으로 교체하는 기능 추가
     (UpdateCheckThread/UpdateApplyThread, urllib만 사용해 추가 의존성 없음).
     .py 다운로드분은 교체 전 compile()로 문법 검증, 교체 전 .bak 백업 생성.
     시작 3초 후 자동 확인(설정에서 끌 수 있음) + 설정 탭 수동 확인 버튼 제공.
     GITHUB_OWNER/GITHUB_REPO 상수는 임시값이므로 실제 저장소로 교체 필요.
   - [버그 수정] _on_update_apply_result()에 잘못 남아있던 return tab 구문
     제거. 정의되지 않은 tab 변수를 반환하려다 업데이트 적용 완료/재시작
     확인 직후 NameError로 죽는 결함이었음 (최종 점검 중 발견).
   - [버전 규칙 추가] 요청받은 업데이트를 한 번에 다 구현하지 못했을 때 붙이는
     그리스 문자 접미사 규칙(_alpha, _beta, ...)을 [버전 표기 규칙]에 명문화.
   - [AI 연동 예정 메모] Gemini API 연동은 공동 협업자(KRJohnWick)가 진행할
     예정이라 실제 구현은 하지 않되, 요청대로 목적/사용 API/담당/통합 지점
     후보를 정리한 "[AI 연동 예정 메모]" 섹션을 헤더에 추가해 다른 Claude
     세션이 참고할 수 있게 함 (실제 코드 없음, 순수 메모 — 이 항목의 요청
     자체가 "메모 작성"이었으므로 이것으로 완료 처리).
   - [최종 점검] 위 변경 사항 전체에 대해 중복 정의/미정의 심볼/컴파일 여부를
     재검사하고, changelog 자동 추출 로직(get_changelog_text)이 새로 추가된
     AI 연동 메모 섹션과 충돌하지 않는지 확인함.
   - 요청받은 사항(1~6번)을 모두 완료하여 접미사 없는 정식 버전 v1.2.0으로 확정.

 v1.1.0 (UI 경로 개편 + 설정 탭 신설)
   - 상단 탭 배치를 일관성 있게 재정렬: 최적화 관련 기능(원클릭 최적화 → 성능
     대시보드 → 성능&게이밍 → 블로트웨어 제거 → 시작 프로그램 → 디스크 정리+ →
     진단&복원 → 전문가 팁&네트워크)을 앞쪽에 모으고, 화이트리스트 관리 →
     설정(신규) 순으로 뒤에 배치.
   - "⚙️ 설정" 탭 신설: 기존에 화이트리스트 탭 안에 깊숙이 있던 "🎨 테마 선택"을
     이곳으로 이동. 그 외 프로그램 정보(제작자/협업자/버전)와 업데이트 내역을
     함께 확인할 수 있도록 구성.
   - 공동 협업자 "KRJohnWick" 합류. 파일 상단 주석 및 설정 탭 프로그램 정보에 반영.

 v1.0.4 (리네이밍 — 기능 변경 없음)
   - 이전에 별도 모듈로서 기능하던 일부 확장 기능(블로트웨어 제거/시작프로그램
     관리/성능&게이밍 튜닝/진단&복원/디스크 정리+ 등) 관련 식별자를 프로그램
     기본 기능에 맞게 정리. 동작/로직은 동일하며 이름만 변경:
     · 탭 UI를 담당하던 믹스인 클래스명을 ExtendedFeaturesMixin으로 통일
     · 관련 가용 여부 플래그를 EXTENDED_FEATURES_AVAILABLE으로 통일
     · 시작프로그램 비활성화 저장용 레지스트리 키를 Run_OptiCoreDisabled로 통일
     · 관련 주석/문서 표현을 "확장 기능(기본 내장)"으로 통일
   - 주의: 구버전에서 시작프로그램을 비활성화한 적이 있는 PC는 이전 레지스트리
     키 이름으로 저장된 항목이 남아있을 수 있어 새 키 이름으로는 안 잡힐 수
     있음. 필요 시 시작프로그램 탭에서 항목을 다시 한번 확인하는 것을 권장.

 v1.0.3 (문서/정책 갱신 — 기능 변경 없음)
   - 파일 최상단에 "다른 Claude가 반드시 먼저 읽어야 할 안내" 블록 추가:
     제작자/관리자 "JeulGemI" 명시, 기준 코드 원칙(대격변 아니면 항상
     사용자가 전달한 OptiCore.py 코드를 기준으로 수정할 것), 파일명 고정
     원칙, 버전/변경이력 갱신 의무를 명문화.
   - GitHub 배포 안내 추가 (OptiCore가 GitHub에서 .exe로 빌드/배포됨).

 v1.0.2 (버그 수정 + 파일명 정책 변경)
   - 파일명을 "OptiCore.py"로 고정. 버전 번호를 파일명(OptiCore_V1.0.py 등)에
     박아두지 않고, APP_NAME/APP_VERSION 상수 + 창 제목 + 이 변경 이력에서만
     관리하도록 변경 (버전 오를 때마다 파일명을 바꿔야 하는 문제 해결).
   - 창 제목에 "OptiCore vX.Y.Z"가 표시되도록 setWindowTitle() 수정.

 v1.0.1 (버그 수정)
   - on_flush_dns_perf_tab()이 파일명을 하드코딩해 자기 자신을 import하던 문제 수정
     (main_real__2_ 모듈을 찾는 방식이라 파일명이 바뀌면 항상 실패하던 구조였음).
     이미 모듈에 정의되어 있던 flush_dns()를 바로 호출하도록 변경.
   - PROTECTED_PROCESSES 목록의 파일명 항목을 새 프로그램 이름에 맞게 갱신.

 v1.0.0 (기준 버전 - OptiCore로 이름 확정)
   - 이전까지 이름 없이 개발되던 통합판을 "OptiCore"로 명명하고 버전 관리를 시작함.
   - 포함된 주요 기능:
     · 실제 RAM 워킹셋 트림 / CPU 우선순위 조정 / SSD·브라우저 캐시 정리 (휴지통 이동)
     · 게임 부스터 (감시 시작 시 우선순위 부스트, 종료 시 자동 원복)
     · DNS 캐시 초기화, Nagle 알고리즘 토글, 시스템 복구 지점 생성
     · 자동 스마트 정리(유휴시간/RAM 임계값 기반), 플로팅 OSD, 화이트리스트 관리, Undo 타임라인
     · 확장 기능 모듈(기본 내장): 블로트웨어 제거, 시작 프로그램 관리, 성능&게이밍 튜닝,
       진단&복원, 디스크 정리+ (5개 탭 추가)
   - CPU 사용량 코어 수 정규화, 첫 호출 0% 문제, UI 프리징(QThread 분리), RAM 측정 시차,
     트레이 고립 방지 등 이전 단계에서 발견된 버그들은 이 기준 버전에 이미 반영되어 있음.

 [주의]
   - RAM/CPU 실측 조작, 레지스트리 조작, 복구 지점 생성, 확장 기능 모듈 상당수는 Windows 전용입니다.
   - 레지스트리/서비스/전원/시작프로그램 조작 기능 대부분은 관리자 권한이 필요합니다.
   - optimizer_settings.json 에는 Gemini API 키가 평문으로 저장됩니다.
     이 파일과 optimizer_log.txt 는 절대 GitHub에 커밋하지 마세요 (.gitignore 필수).
=====================================================================
"""

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

import config
from config import IS_WINDOWS, load_settings
from themes import apply_theme, DEFAULT_THEME_KEY
from ui.dialogs import load_app_icon
from ui.main_window import MainWindow


def main():
    # ---- 진입점 정보 등록 ----
    # 모듈이 분리되면서 다른 모듈은 "OptiCore.py의 헤더 주석"과 "자기 자신의
    # 실제 경로"를 직접 알 수 없게 되었다. 그래서 가장 먼저 등록해준다.
    #  - 헤더 주석 → 설정 탭의 [업데이트 내역] 표시에 사용
    #  - 파일 경로 → 자동 업데이트가 교체할 대상 파일을 정하는 데 사용
    config.register_entry_point(__doc__, __file__)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 창을 닫아도 트레이에서 계속 실행
    app.setApplicationName(config.APP_NAME)

    # 프로그램 아이콘 (icon.ico 없으면 시스템 기본 아이콘으로 자동 대체)
    app.setWindowIcon(load_app_icon())

    startup_settings = load_settings()
    apply_theme(startup_settings.get("theme", DEFAULT_THEME_KEY))

    if not IS_WINDOWS:
        QMessageBox.warning(
            None, "환경 안내",
            "RAM/CPU/레지스트리/복구 지점 기능은 Windows 전용입니다.\n"
            "다른 OS에서는 SSD/브라우저 캐시 정리와 GPU 정보 조회만 동작합니다."
        )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
