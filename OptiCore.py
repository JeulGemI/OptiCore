# -*- coding: utf-8 -*-
"""
=====================================================================
 OptiCore - Smart Windows Optimization & Latency Reducer
=====================================================================
 제작자 및 관리자: JeulGemI
 공동 협업자: KRJohnWick
 GitHub: https://github.com/JeulGemI/OptiCore
 최신 릴리스 API: https://api.github.com/repos/JeulGemI/OptiCore/releases/latest

 [버전 규칙] MAJOR.MINOR.PATCH (시맨틱 버저닝)
 [파일명 규칙] 진입점 파일명은 항상 "OptiCore.py"로 고정

 [향후 계획]
 1. 프로그래밍 언어 변경 (C# 전환 지침)
    ▶ 이 프로그램은 장기적으로 C# (.NET / WPF)으로 언어를 변경할 예정입니다.
      다만 다음 업데이트에서 곧바로 C#으로 전환하는 것은 아니며, "때가 되면" 전환합니다.
      그 시점까지는 계속 Python(PyQt6) 기준으로 기능을 추가/수정하세요.
      → 다음 Claude 세션은 사용자가 명시적으로 "이제 C#으로 옮기자"라고
        요청하기 전까지는 임의로 C# 변환 작업을 시작하지 마세요.
      → 전환을 대비해, 새 기능은 되도록 UI(ui/)와 로직(core/·features/)을
        섞지 말고 계층을 철저히 분리해 두세요.
      → [v2.1.0] 데이터 구조는 models.py 의 @dataclass DTO로 정의합니다.
        새 데이터를 익명 튜플로 주고받지 말고 DTO를 추가하세요.
        (파이썬 튜플은 C#의 record/class로 1:1 대응되지 않습니다)

 2. 차기 업데이트 예정 기능 메모 (로드맵)
    ▶ 시스템 & 디스크 정밀 정리:
      - GPU 셰이더 캐시 (NVIDIA DXCache/GLCache, AMD, Intel) 원클릭 정리
      - 그래픽 드라이버 설치 잔여물 및 크래시 덤프(*.dmp) 정리
    ▶ Gemini AI 연동 심화:
      - 실시간 PC 점유율 기반 자연어 진단 리포트 대시보드 카드
      - 알 수 없는 시작프로그램/서비스의 안전성 및 위험도 실시간 분석

 [주요 변경 이력]
 =====================================================================
 v2.1.0 (종합 리팩토링 — Win32 Native 전환 + 비침습 게이밍 튜닝 + 안정성)
   작업 범위: 요청서 [OptiCore v2.1.0 종합 리팩토링 및 게임 최적화·안정성
   전면 개편 지침]의 1~5번 항목 전부. 요청 사항을 모두 구현했으므로
   미완료 접미사(_alpha 등) 없이 정식 버전 v2.1.0으로 확정한다.

   [1. Win32 Native API 래퍼 신설 — core/win32.py]
   - subprocess/PowerShell 의존을 줄이고 ctypes.windll 기반 C 네이티브 호출로
     전환. 콘솔 창 번쩍임과 프로세스 생성 지연(수백 ms)이 사라졌다.
   - TimerResolution: timeBeginPeriod(1)/timeEndPeriod(1)을 RAII 컨텍스트
     매니저로 구현. with 블록 + 참조 카운트 + atexit 훅의 3중 보장으로,
     예외나 비정상 종료가 나도 타이머 설정이 시스템에 남지 않는다.
     (해제를 빠뜨리면 프로세스가 죽을 때까지 전역 전력 소모가 늘어난다)
   - MmcssTask: AvSetMmThreadCharacteristicsW("Games") / AvRevert 래퍼.
     avrt.dll이 없는 에디션에서는 조용히 비활성화된다.
   - NtSuspendProcess / NtResumeProcess 래퍼 (비파괴 백그라운드 일시 동결).
   - ProcessHandle: OpenProcess 핸들을 with 블록으로 관리. 기존
     trim_process_working_set()에는 실패 경로에서 핸들을 닫지 않는 구간이
     있었는데 이 래퍼로 위임하면서 함께 해결되었다.
   - GetSystemCpuSetInformation 파싱으로 하이브리드 CPU의 P-Core를 탐지.
     코어 번호를 추측하지 않고 Windows가 알려주는 EfficiencyClass를 읽는다.
   - SingleInstanceMutex / find_window_by_title / force_foreground_window.

   [2. 중복 실행 방지 및 기존 창 복원]
   - 시작 시 Named Mutex("OptiCore_SingleInstance_Mutex")를 확인해, 이미
     실행 중이면 기존 창을 SW_RESTORE + SetForegroundWindow로 앞에 띄우고
     새 프로세스는 sys.exit(0)으로 즉시 정상 종료한다.
   - Windows는 다른 프로세스의 SetForegroundWindow를 대부분 차단하므로,
     AttachThreadInput으로 포그라운드 스레드에 붙은 뒤 호출하고 그래도
     실패하면 TOPMOST 토글로 대체하는 문서화된 절차를 순서대로 시도한다.
   - 창 제목이 config.WINDOW_TITLE_PREFIX("OptiCore v")로 시작하도록 고정.
     버전이 올라가도 창 탐색이 깨지지 않는다.

   [3. X(닫기) 버튼 동작 및 설정화]
   - 기본 동작을 event.ignore() + showMinimized()로 변경. 창은 사라져도
     작업 표시줄 아이콘이 남아 한 번의 클릭으로 되돌아올 수 있다.
     (v2.0.x는 무조건 트레이로 숨겨서, 트레이가 접혀 있는 PC에서는
      프로그램이 사라진 것처럼 보인다는 문제가 있었다)
   - ⚙️ 설정 탭에 '창 닫기(X) 동작' 옵션 추가:
       minimize_taskbar(기본값) / minimize_tray / exit
     변경 즉시 optimizer_settings.json에 원자적으로 저장된다.
   - 트레이를 못 쓰는 환경에서 minimize_tray를 고르면 창을 되찾을 방법이
     없어지므로, 그 경우에는 자동으로 최소화로 대체한다.

   [4. 비침습적 게이밍 튜닝 — features/game_booster.py 신설]
   - 게임 실행 중 주기적 EmptyWorkingSet 호출을 전면 제거했다. 게임이 방금
     반납한 페이지를 다시 읽어오게 되어 하드 페이지 폴트가 폭증하고,
     사용자 눈에는 몇 초마다 화면이 튀는 스터터로 나타나던 동작이다.
     정리는 게임 시작 직전 1회만 허용한다.
   - 우선순위 격상을 제거하고 Normal 안정화로 대체. 설정에서 허용해도
     Above Normal을 넘지 않으며 High/Realtime 코드 경로 자체가 없다.
     (렌더 스레드가 오디오·입력 스레드를 굶기던 원인)
   - 폴링 주기를 2초 → 5초 이상으로 완화(설정에서도 5초 미만 선택 불가).
     감시 자체가 CPU를 계속 깨워 절전 진입을 방해하던 문제를 없앴다.
   - 백그라운드 앱을 강제 종료하는 대신 NtSuspendProcess로 일시 동결하고
     게임 종료 시 NtResumeProcess로 복구하는 모드 추가. 브라우저 탭과
     로그인 세션이 보존된다.
     · 안티치트(EasyAntiCheat/BattlEye/Vanguard/GameGuard 등), 오디오,
       GPU 드라이버, 보안 프로세스는 NEVER_SUSPEND 목록으로 차단.
     · 동결한 채로 프로그램이 죽으면 사용자 PC가 먹통이 되므로,
       세션 종료 / shutdown_cleanup / atexit 3중으로 해동을 보장한다.
     · [📊 대시보드] 타임라인에서 [지금 해동] 버튼으로 즉시 되살릴 수 있다.
   - 하이브리드 CPU P-Core 바인딩(psutil cpu_affinity). 동종 코어 CPU에서는
     아무 동작도 하지 않으며, 원래 affinity를 보관했다가 정확히 원복한다.

   [5. 저지연 레지스트리·네트워크 튜닝 — features/tweaks.py]
   - Multimedia SystemProfile: NetworkThrottlingIndex=0xFFFFFFFF,
     SystemResponsiveness=0 (복원값 10 / 20).
   - SystemProfile\\Tasks\\Games 프로필 주입: GPU Priority=8, Priority=6,
     Scheduling Category=High, SFIO Priority=High, Clock Rate=10000.
   - Nagle 알고리즘 해제(TcpAckFrequency=1 / TCPNoDelay=1). 복원 시에는
     값을 0으로 덮지 않고 삭제해야 순정으로 돌아가므로 그렇게 처리한다.
   - BCD 타이머: disabledynamictick=yes, useplatformtick=yes (재부팅 필요).
   - set_high_res_timer()가 disabledynamictick까지 건드려 새 함수와 담당이
     겹치던 문제를 정리해, useplatformclock만 책임지도록 분리했다.
   - 위 신규 항목 전부를 [🩺 진단 & 복원]의 원클릭 순정 복원에 연결.

   [6. 설정·로그·예외 안정성]
   - 원자적 저장: optimizer_settings.json을 임시 파일(.tmp)에 쓰고
     flush + os.fsync 후 os.replace로 교체한다. 기존 방식은 원본을 먼저
     비우고 쓰는 구조라, 그 사이 강제 종료되면 0바이트로 남아 설정이
     전부 초기화됐다. 임시 파일은 반드시 같은 폴더에 만든다(볼륨이 다르면
     os.replace의 원자성이 깨진다).
   - 로그 로테이션: RotatingFileHandler로 optimizer_log.txt를 최대 5MB,
     백업 2개로 제한. 기존 [YYYY-MM-DD HH:MM:SS] 형식은 그대로 유지했다.
     읽을 때도 read_log_tail()로 뒷부분만 가져와 창이 빨리 뜬다.
   - 전역 예외 처리기: sys.excepthook을 재정의해 미처리 예외를 로그에
     기록한 뒤 안내 팝업을 띄운다. KeyboardInterrupt는 기본 동작을 유지한다.
     팝업을 띄우기 전에 동결된 프로세스를 먼저 해동한다.
   - 아이콘 로더는 기존 resource_path("icon.ico") + SP_ComputerIcon fallback
     구조를 그대로 유지(v2.0.0에서 이미 요구사항을 충족).

   [7. DTO 분리 및 스레드 자원 관리]
   - models.py 신설: ProcessInfo / SystemStats / TweakProfile / TweakResult /
     GameBoostOptions / GameBoostState / FrozenProcess / CloseAction.
     기존 튜플 코드와 공존할 수 있도록 from_tuple / as_tuple 변환을 제공해
     점진적 전환이 가능하게 했다(한 번에 전부 바꾸면 회귀 버그가 생긴다).
   - PerfTweakThread(QThread) → PerfTweakTask(QRunnable + QThreadPool).
     버튼을 여러 번 눌러도 스레드가 쌓이지 않는다. 기존 이름은 별칭으로
     남겨 import 호환을 유지했다.

   [8. 헤더 표준화]
   - 요청서의 표준 양식에 맞춰 [향후 계획]에는 C# 전환 수칙과 로드맵만 두고,
     구현 완료 내용은 [주요 변경 이력]으로 옮겼다. 과거 이력은 삭제하지
     않고 아래에 그대로 보존한다(헤더 규칙 4번).
     config.get_changelog_text()가 [주요 변경 이력]과 옛 [변경 이력]을
     모두 인식하도록 파서를 보강해, 다른 계정에서 옛 헤더가 담긴 파일을
     붙여넣어도 설정 탭이 깨지지 않는다.

 v2.0.1 (버그 수정 — Gemini 모델 단종으로 인한 HTTP 404 해결)
   - [증상] 설정 탭 [연결 테스트]에서 "This model models/gemini-2.0-flash is
     no longer available" HTTP 404 오류가 발생했다.
   - [원인] Google이 gemini-2.0-flash / 2.0-flash-lite를 2026-06-01자로 종료.
     gemini-1.5-flash 계열도 2025-09-29에 이미 종료되어 대안이 못 된다.
   - [수정] GEMINI_MODEL을 "gemini-3.5-flash"로 교체. 404 시
     GEMINI_FALLBACK_MODELS(gemini-flash-latest → gemini-3.6-flash →
     gemini-2.5-flash)를 순서대로 시도하고, 그것도 실패하면 ListModels API로
     자동 탐색(discover_available_model). 키/네트워크 오류는 재시도하지 않는다.
   - is_model_endpoint_error()로 오류 종류를 구분해 "키를 확인하세요" 대신
     모델 교체를 안내하는 별도 팝업을 띄운다.
   - generationConfig에서 temperature 제거(2026-07-21 Deprecated),
     maxOutputTokens 1024 → 4096 상향(Gemini 3 계열은 thinking 토큰이 같은
     한도를 소모해 본문이 빈 채 반환되는 문제가 있음).
   - API 키는 요청서의 URL 예시(?key=...)와 달리 x-goog-api-key 헤더로 전송.
     쿼리스트링은 프록시/서버 접근 로그에 평문으로 남는다.

 v2.0.0 (대격변 — 모듈 트리 분리 + Gemini 연동 + 아이콘 리소스 지원)
   작업자: 공동 협업자 KRJohnWick
   - 단일 파일(약 4,000줄)이던 프로그램을 계층형 모듈 트리로 분리.
     기존 기능은 하나도 빠짐없이 보존.
   - [분리 과정에서 발견/수정한 결함 3건]
     · get_running_program_path()가 os.path.abspath(__file__)을 써서 자동
       업데이트가 OptiCore.py가 아니라 updater.py를 덮어쓸 뻔했음
       → config.get_entry_point_path() 사용으로 변경.
     · get_changelog_text()가 자기 모듈의 __doc__를 읽는 구조라 분리 후
       빈 값이 될 뻔했음 → register_entry_point()로 등록 후 참조.
     · PROTECTED_PROCESSES에 옛 파일명 "opticore_v1.0.py"가 남아 정작 현재
       이름은 보호되지 않았음 → "opticore.py"/"opticore.exe"로 교정.
   - [Gemini 연동] ai/gemini_advisor.py 신설. 사전 점검 창에서 체크된 항목의
     안전성을 [권장|주의|제외]로 판단. QThread 기반이라 UI가 멈추지 않는다.
   - [API 키 보안] 하드코딩 없음. optimizer_settings.json 또는 환경변수
     GEMINI_API_KEY에서만 로드. 헤더로 전송하고 로그/오류에서 마스킹.
   - [자동 업데이트] 공개 Releases API 사용(토큰 불필요). .py 문법 검증
     compile, .bak 백업, 같은 이름 교체, 재시작 확인 로직 유지.
   - [아이콘 리소스] config.resource_path()로 PyInstaller(sys._MEIPASS)와
     소스 실행 양쪽 대응. 실패 시 SP_ComputerIcon으로 조용히 fallback.

 v1.2.0 (UI 편의성 개편 + 도움말 + 자동 업데이트 + AI 연동 메모)
   - 모든 탭의 체크박스/버튼에 상세 설명 툴팁 추가.
   - 설정 탭 개편(테마 → 도움말 → 프로그램 정보), 업데이트 내역을 팝업으로 통합.
   - GitHub 최신 릴리스 조회 후 실행 파일 자체를 같은 경로/이름으로 교체하는
     자동 업데이트 추가(urllib만 사용해 추가 의존성 없음).
   - [버그 수정] _on_update_apply_result()에 잘못 남아있던 return tab 구문
     제거. 정의되지 않은 tab 변수를 반환하려다 NameError로 죽던 결함.
   - 미완료 접미사 규칙(_alpha, _beta, ...)을 [버전 표기 규칙]에 명문화.

 v1.1.0 (UI 경로 개편 + 설정 탭 신설)
   - 최적화 관련 탭을 앞쪽에 모으고 화이트리스트 → 설정 순으로 재배치.
   - "⚙️ 설정" 탭 신설(테마 선택 이동 + 프로그램 정보 + 업데이트 내역).
   - 공동 협업자 "KRJohnWick" 합류.

 v1.0.4 (리네이밍 — 기능 변경 없음)
   - 확장 기능 관련 식별자를 통일: ExtendedFeaturesMixin,
     EXTENDED_FEATURES_AVAILABLE, Run_OptiCoreDisabled.
   - 주의: 구버전에서 시작프로그램을 비활성화한 PC는 이전 레지스트리 키
     이름으로 저장된 항목이 남아 새 키로는 안 잡힐 수 있음.

 v1.0.3 (문서/정책 갱신 — 기능 변경 없음)
   - "다른 Claude가 반드시 먼저 읽어야 할 안내" 블록 추가(기준 코드 원칙,
     파일명 고정, 버전/변경이력 갱신 의무). GitHub 배포 안내 추가.

 v1.0.2 (버그 수정 + 파일명 정책 변경)
   - 파일명을 "OptiCore.py"로 고정. 버전은 APP_VERSION 상수 + 창 제목 +
     변경 이력에서만 관리. 창 제목에 "OptiCore vX.Y.Z" 표시.
   - DNS 캐시 플러시 수정.

 v1.0.1 (버그 수정)
   - on_flush_dns_perf_tab()이 파일명을 하드코딩해 자기 자신을 import하던
     문제 수정. PROTECTED_PROCESSES 파일명 항목 갱신.

 v1.0.0 (기준 버전 - OptiCore로 이름 확정)
   - 이전까지 이름 없이 개발되던 통합판을 "OptiCore"로 명명하고 버전 관리 시작.
   - 주요 기능: RAM 워킹셋 트림 / CPU 우선순위 조정 / SSD·브라우저 캐시 정리,
     게임 부스터, DNS 플러시, Nagle 토글, 복구 지점, 자동 스마트 정리,
     플로팅 OSD, 화이트리스트, Undo 타임라인, 확장 기능 5개 탭.

 =====================================================================
 ⚠️ 이 파일을 처음 여는 Claude(또는 다른 작업자)는 아래 내용을 먼저 읽으세요
 =====================================================================
 1. [기준 코드 원칙] 사용자는 여러 Claude 계정을 돌려가며 이 프로그램을
    수정합니다. 즉 지금 이 파일이 "가장 최신"이 아닐 수 있습니다.
    → 수정/업데이트 요청을 받으면, 사용자가 대화 중 새로 전달한 코드가
      있다면 그것을 기준(base)으로 삼아 그 위에 요청 사항을 구현하세요.
      자신의 기억 속 이전 버전을 기준으로 삼지 마세요.
    → 예외는 MAJOR 버전이 오르는 "대격변" 패치뿐입니다.
    → [v2.0.0부터] "기준 코드"는 이 파일 하나가 아니라 아래 [모듈 구조]
      전체입니다. 일부 모듈만 전달받았다면, 빠진 모듈을 임의로 새로 만들지
      말고 사용자에게 해당 파일을 요청하세요.
 2. [파일명 고정] 진입점 파일명은 항상 "OptiCore.py"로 고정합니다.
    (예: OptiCore_V1.0.py, OptiCore_v2.py 같은 형식 금지)
    분리된 모듈 파일명(config.py, models.py, core/…, ui/… 등)도 그대로
    유지하세요. 바꾸면 import 경로가 전부 깨집니다.
 3. [버전 갱신] 아래 [버전 표기 규칙]에 따라 config.py의 APP_VERSION 상수와
    이 헤더의 [주요 변경 이력]을 매번 함께 갱신하세요. 주석만 바꾸는 작업도
    "업데이트"로 취급해 PATCH를 올리고 변경 이력에 기록하세요.
    ※ 창 제목은 config.APP_NAME / APP_VERSION을 읽어 자동 표시됩니다.
 4. [변경 이력 유지] 새 항목은 항상 맨 위에 추가하고, 목록이 너무 길어지면
    오래된 항목을 요약해서 정리하세요. 절대 삭제로 역사를 지우지 마세요.
 5. [헤더 보존] 이 헤더 전체(제작자/협업자 정보, 파일명 규칙, 버전 표기 규칙,
    미완료 접미사 규칙, [AI 연동 메모], [주요 변경 이력])는 다음 세션이 계속
    읽고 이어서 작업할 수 있도록 항상 이 진입점 파일 상단에 온전히 남겨두세요.
    다른 모듈로 옮기지 마세요.

 [버전 표기 규칙]
   형식: MAJOR.MINOR.PATCH (예: 1.0.0, 1.0.13, 1.1.0, 2.0.0, 2.1.0)
   - PATCH: 자잘한 버그 수정/문서 갱신 등 소규모 변경 시 +1
   - MINOR: 기능 추가 시 +1, PATCH는 0으로 리셋
   - MAJOR: 구조 전면 개편 등 대격변 시 +1, MINOR/PATCH 모두 0으로 리셋
     (대격변 패치일 때만 "기준 코드 원칙"의 예외로 전면 재설계 허용)

   [미완료 접미사 규칙] 한 번에 요청받은 업데이트를 전부 구현하지 못하고
   일부만 반영한 채 버전을 올려야 할 때는, 다음 정식 버전 번호 뒤에 그리스
   문자 발음을 소문자 언더스코어로 붙입니다: _alpha, _beta, _gamma, _delta …
     예) 1.3.4_alpha, 2.5.10_beta
   나머지까지 완료되면 접미사를 뗀 정식 번호로 갱신합니다(숫자는 올리지 않음).
   같은 번호에서 미완료가 반복되면 접미사만 다음 글자로 바꿉니다.
   is_newer_version()은 숫자가 같을 때 접미사 없는 정식판을 더 최신으로
   판단하므로, 이 규칙을 따르면 자동 업데이트 확인과도 어긋나지 않습니다.

 [배포 안내]
   이 프로그램은 GitHub 저장소 "OptiCore"에서 .exe로 빌드되어 배포됩니다.
   저장소: https://github.com/JeulGemI/OptiCore

 =====================================================================
 [모듈 구조 — v2.0.0에서 분리, v2.1.0에서 3개 추가]
 =====================================================================
   OptiCore.py            진입점(main). 이 헤더 주석의 원본 보관소이자
                          단일 인스턴스 검사 / 전역 예외 처리기 /
                          QApplication 실행 담당. 로직은 두지 않는다.
   models.py              [v2.1.0 신규] DTO(@dataclass) 정의. 프로젝트 내부의
                          어떤 모듈도 import 하지 않는 최하위 계층.
   config.py              전역 상수(APP_VERSION 등), 설정 원자적 로드/저장,
                          로그(write_log, 로테이션), resource_path
   themes.py              테마 8종 정의(THEMES) + QSS 생성기
   updater.py             공개 GitHub Releases 조회/다운로드/안전 교체
   core/win32.py          [v2.1.0 신규] Win32 Native 래퍼 — TimerResolution,
                          MMCSS, NtSuspend/Resume, Mutex, P-Core 탐지
   core/scanner.py        CPU·RAM·SSD·브라우저·GPU 스캔 (읽기 전용)
   core/actions.py        워킹셋 트림, 우선순위, 휴지통, DNS, Nagle,
                          복구 지점, OptimizationWorker, _run_cli/_reg_set
   features/debloat.py    AppX 블로트웨어 스캔·제거, 텔레메트리 차단
   features/startup.py    시작 프로그램 스캔/토글/삭제
   features/tweaks.py     Multimedia SystemProfile, Tasks\\Games, Nagle,
                          BCD 타이머, 전원/시각효과/Game DVR, PerfTweakTask
   features/game_booster.py [v2.1.0 신규] 비침습 게임 부스트 세션,
                          P-Core 바인딩, 백그라운드 동결/해동
   features/diagnostics.py sfc/DISM, 원클릭 순정 복원, 디스크 정리+
   ai/gemini_advisor.py   Google Gemini API 연동
   ui/dialogs.py          사전 점검/진행률/스캔 팝업, OSD, 아이콘 로더
   ui/extended_tabs.py    확장 기능 5개 탭 UI 빌더(ExtendedFeaturesMixin)
   ui/main_window.py      MainWindow — 10개 탭 조립, 트레이, 타이머

   [import 방향 — 순환 참조 금지]
     models  ←  config  ←  themes / updater / core / ai
     config  ←  core/win32  ←  core/actions  ←  features/*
     core/scanner  ←  core/actions
     features/tweaks, features/debloat  ←  features/diagnostics
     config, ai  ←  ui/dialogs
     config, core, features  ←  ui/extended_tabs
     위 전부  ←  ui/main_window  ←  OptiCore.py
   화살표는 "왼쪽이 오른쪽에 의해 import 됨"을 뜻합니다. 역방향 import를
   추가하면 즉시 순환 참조가 되므로 절대 만들지 마세요. 하위 모듈에서
   상위(UI) 기능이 필요해 보이면, 값을 반환해 상위가 처리하게 하세요.

 =====================================================================
 [AI 연동 메모 — 다른 Claude 세션은 이 섹션을 읽고 참고할 것]
 =====================================================================
 상태: ✅ Google Gemini API 연동은 v2.0.0에서 구현 완료.
 구현 위치: ai/gemini_advisor.py
   - GeminiAdvisorThread: 사전 점검 창에서 체크한 항목을 요약해 Gemini에
     보내고 [권장 | 주의 | 제외] 판단과 종합 의견을 받아온다.
   - GeminiConnectionTestThread: 설정 탭 [연결 테스트] 버튼 전용.
 API 키 정책 (중요):
   - 소스코드 하드코딩 절대 금지. optimizer_settings.json의 "gemini_api_key"
     또는 환경변수 GEMINI_API_KEY 에서만 읽는다.
   - 키는 URL 쿼리스트링이 아니라 x-goog-api-key 헤더로 전송한다.
   - optimizer_settings.json / optimizer_log.txt 는 반드시 .gitignore 처리.
   - 로그·오류 메시지에 키가 남지 않도록 마스킹되어 있다.
 모델 수명 정책 (v2.0.1 추가 — 다음 세션은 반드시 읽을 것):
   - Google은 Gemini 모델을 주기적으로 종료하며, 종료된 모델로 요청하면
     HTTP 404 "This model ... is no longer available" 가 돌아온다.
   - 모델을 바꿀 때는 ai/gemini_advisor.py의 GEMINI_MODEL 상수 한 줄만
     고치면 된다. UI 라벨은 이 상수를 읽어 자동 갱신된다.
   - 새 모델을 고르기 전에 아래 문서에서 "현재 제공 중인지 + 종료 예정일이
     충분히 남았는지"를 반드시 확인할 것. 기억에 의존하지 말 것.
       모델 목록: https://ai.google.dev/gemini-api/docs/models
       단종 일정: https://ai.google.dev/gemini-api/docs/deprecations
   - 이미 종료된 모델(참고): gemini-1.5-*(2025-09-29),
     gemini-2.0-flash / 2.0-flash-lite(2026-06-01).
     종료 예정: gemini-2.5-flash(2026-10-16 예정).

 [필요 라이브러리 설치]
   pip install PyQt6 psutil Send2Trash
   (선택) NVIDIA GPU 정보: pip install nvidia-ml-py
   ※ Gemini 연동은 표준 라이브러리(urllib)만 사용하므로 추가 설치가 없습니다.
   ※ Win32 Native 기능(core/win32.py)도 ctypes 표준 라이브러리만 씁니다.

 [주의]
   - RAM/CPU 실측 조작, 레지스트리 조작, 복구 지점 생성, 확장 기능 상당수는
     Windows 전용입니다. 다른 OS에서는 해당 기능이 자동 비활성화됩니다.
   - 레지스트리/서비스/전원/시작프로그램 조작 대부분은 관리자 권한이 필요합니다.
   - optimizer_settings.json 에는 Gemini API 키가 평문으로 저장됩니다.
     이 파일과 optimizer_log.txt 는 절대 GitHub에 커밋하지 마세요 (.gitignore 필수).
=====================================================================
"""

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

import config
from config import IS_WINDOWS, WINDOW_TITLE_PREFIX, load_settings, write_log
from themes import apply_theme, DEFAULT_THEME_KEY
from core.win32 import SingleInstanceMutex, TimerResolution, restore_existing_instance
from ui.dialogs import load_app_icon
from ui.main_window import MainWindow

# 전역 참조로 잡아둔다. 지역 변수로 두면 main()이 끝나기 전에 가비지 컬렉션
# 대상이 되면서 뮤텍스 핸들이 닫혀 중복 실행 방지가 무력화될 수 있다.
_instance_mutex = None


def ensure_single_instance() -> bool:
    """
    이미 실행 중인 OptiCore가 있으면 그 창을 앞으로 띄우고 False를 돌려준다.

    파일 잠금이나 포트 바인딩 대신 Named Mutex를 쓰는 이유는, 커널 오브젝트라
    프로세스가 강제 종료되거나 블루스크린이 나도 OS가 알아서 정리해주기
    때문이다. 잠금 파일 방식에서 흔한 "죽은 뒤에도 실행 중이라고 우기는"
    상태가 생기지 않는다.
    """
    global _instance_mutex
    _instance_mutex = SingleInstanceMutex()
    if _instance_mutex.acquire():
        return True

    # ---- 이미 실행 중 ----
    write_log("중복 실행 감지 — 기존 창을 포그라운드로 복원하고 종료합니다.")
    restored = restore_existing_instance(WINDOW_TITLE_PREFIX)
    if not restored:
        # 창을 못 찾았다면(트레이로 숨겨져 있는 등) 사용자가 영문을 모를 수
        # 있으니 최소한의 안내는 남긴다.
        try:
            _ = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.information(
                None, f"{config.APP_NAME} 실행 중",
                f"{config.APP_NAME}가 이미 실행 중입니다.\n"
                "작업 표시줄 또는 시스템 트레이 아이콘에서 창을 열어주세요."
            )
        except Exception:
            pass
    return False


def install_global_excepthook(window_getter):
    """
    미처리 예외가 나도 프로그램이 조용히 사라지지 않도록 한다.

    PyQt 앱에서 슬롯 안의 예외가 새어나가면, 콘솔 없이 실행된 .exe에서는
    아무 메시지도 없이 창만 닫힌다. 사용자는 원인을 알 수 없고 우리도
    재현할 단서가 없다. 그래서 로그에 전체 트레이스백을 남기고 팝업으로
    알린 뒤, 되돌려야 할 시스템 변경(동결된 프로세스 등)을 먼저 해제한다.
    """
    def _hook(exc_type, exc_value, exc_traceback):
        # Ctrl+C는 정상적인 중단 수단이므로 기본 동작을 유지한다.
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        detail = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        write_log(f"[미처리 예외]\n{detail}")

        # ---- 시스템에 남을 수 있는 변경부터 되돌린다 ----
        # 백그라운드 앱이 동결된 채로 남으면 사용자 PC가 먹통이 된 것처럼 보인다.
        try:
            window = window_getter()
            if window is not None:
                window.shutdown_cleanup()
        except Exception:
            pass
        try:
            from features.game_booster import _emergency_thaw_all
            _emergency_thaw_all()
        except Exception:
            pass

        # ---- 사용자 안내 ----
        try:
            summary = f"{exc_type.__name__}: {exc_value}"
            QMessageBox.critical(
                None, "예기치 못한 오류",
                "처리되지 않은 오류가 발생했습니다.\n\n"
                f"{summary}\n\n"
                "자세한 내용은 optimizer_log.txt 에 기록되었습니다.\n"
                "게임 부스터가 적용했던 설정과 동결된 프로그램은 모두 복구했습니다.\n\n"
                "문제가 반복되면 로그와 함께 GitHub 저장소에 알려주세요:\n"
                "https://github.com/JeulGemI/OptiCore"
            )
        except Exception:
            # 팝업조차 못 띄우는 상황(QApplication 종료 후 등)에서는 표준 동작으로.
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = _hook


def main():
    # ---- 진입점 정보 등록 ----
    # 모듈이 분리되면서 다른 모듈은 "OptiCore.py의 헤더 주석"과 "자기 자신의
    # 실제 경로"를 직접 알 수 없게 되었다. 그래서 가장 먼저 등록해준다.
    #  - 헤더 주석 → 설정 탭의 [업데이트 내역] 표시에 사용
    #  - 파일 경로 → 자동 업데이트가 교체할 대상 파일을 정하는 데 사용
    config.register_entry_point(__doc__, __file__)

    # ---- 중복 실행 방지 (QApplication 생성보다 먼저) ----
    # 무거운 초기화를 하기 전에 판정해야 두 번째 인스턴스가 빨리 사라진다.
    if not ensure_single_instance():
        sys.exit(0)

    app = QApplication(sys.argv)
    # 창을 닫아도(설정에 따라 최소화/트레이) 프로세스가 유지되도록 한다.
    # 완전 종료는 트레이 메뉴 [완전 종료] 또는 close_button_action="exit" 로만.
    app.setQuitOnLastWindowClosed(False)
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
    # 예외 처리기는 창이 만들어진 뒤에 건다 (정리 대상이 존재해야 하므로).
    install_global_excepthook(lambda: window)
    window.show()

    # 전역 저지연 타이머 옵션. RAII 컨텍스트 매니저이므로 app.exec()가 어떤
    # 이유로 끝나든(정상 종료/예외) 반드시 timeEndPeriod가 호출된다.
    # 기본값은 꺼짐 — 게임 중에만 켜는 쪽이 배터리에 유리하고, 게임 부스터가
    # 세션 단위로 알아서 켜고 끈다.
    always_on = bool(startup_settings.get("low_latency_timer_always", False))
    with TimerResolution(1, enabled=always_on):
        exit_code = app.exec()

    window.shutdown_cleanup()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
