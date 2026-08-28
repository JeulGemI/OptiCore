# -*- coding: utf-8 -*-
"""
ai/gemini_advisor.py — Google Gemini API 연동 (원클릭 최적화 사전 점검 조언)

의존: config.py 만 (단방향 / UI를 전혀 모른다)

역할
  "🚀 원클릭 최적화"의 사전 점검(Precheck) 단계에서, 사용자가 체크해 둔
  프로세스/정리 항목 목록을 Gemini에 보내 각 항목이 지금 이 PC에서
  "필수 / 권장 / 불필요 / 주의" 중 무엇인지 조언을 받아온다.
  판단의 최종 권한은 항상 사용자에게 있고, AI는 참고 의견만 제시한다.

=====================================================================
[API 키 보안 원칙 — 반드시 지킬 것]
=====================================================================
  1. 소스코드에 API 키를 하드코딩하지 않는다. (이 저장소는 공개되어 있고,
     평문 키를 커밋하면 GitHub에 그대로 노출된다.)
  2. 키는 다음 두 곳에서만 읽는다:
       ① optimizer_settings.json 의 "gemini_api_key"  (설정 탭에서 입력)
       ② 환경변수 GEMINI_API_KEY                       (①이 비어 있을 때)
  3. optimizer_settings.json 은 .gitignore에 넣어 커밋되지 않게 한다.
     (자세한 가이드는 config.py 최상단 주석 참고)
  4. 키는 URL 쿼리스트링(?key=...)이 아니라 HTTP 헤더(x-goog-api-key)로
     보낸다. 쿼리스트링은 프록시/서버 접근 로그에 그대로 남을 수 있다.
  5. 로그(optimizer_log.txt)에는 절대 키를 기록하지 않는다.
     이 모듈은 오류 메시지에서도 키를 마스킹한다.

[전송되는 정보에 대한 안내]
  AI 조언 기능을 쓰면 "프로세스 이름 / 메모리·CPU 사용량 / 정리 항목 요약"이
  Google 서버로 전송된다. 파일 내용이나 개인 문서는 전송하지 않는다.
  이 점은 설정 탭과 사전 점검 창에도 명시해 사용자가 알고 쓰도록 한다.
=====================================================================
"""

import os
import json
import urllib.request
import urllib.error

from PyQt6.QtCore import QThread, pyqtSignal

from config import APP_NAME, APP_VERSION

# =====================================================================
# [v2.0.1] 모델 설정 — 모델 단종(HTTP 404) 대응
# =====================================================================
# Google은 Gemini 모델을 주기적으로 "shut down" 시키고, 종료된 모델로 요청하면
# HTTP 404 + "This model models/... is no longer available" 를 돌려준다.
# 실제 종료 이력 (Google 공식 릴리스 노트 기준):
#     gemini-1.5-flash / 1.5-pro         → 2025-09-29 종료
#     gemini-2.0-flash / 2.0-flash-lite  → 2026-06-01 종료  ← v2.0.0의 404 원인
#     gemini-2.5-flash                   → 2026-10-16 종료 예정 (조기 종료 보고 있음)
# 따라서 2.0-flash의 공식 대체 모델인 gemini-3.5-flash를 기본값으로 쓴다.
#
# ▶ 모델을 바꾸고 싶으면 이 상수 한 줄만 고치면 된다.
GEMINI_MODEL = "gemini-3.5-flash"

# 기본 모델이 404(단종)일 때 순서대로 시도할 후보들.
# 목록 전부 실패하면 ListModels API로 실제 사용 가능한 모델을 자동 탐색한다.
# (같은 사고가 반복되어도 사용자가 코드를 고치기 전까지 버티게 하는 안전망)
GEMINI_FALLBACK_MODELS = (
    "gemini-flash-latest",   # Google이 관리하는 최신 flash 별칭
    "gemini-3.6-flash",
    "gemini-2.5-flash",      # 2026-10-16 종료 예정 — 최후의 보루
)

# 모델 단종 시 404가 아닌 다른 코드로 바뀌더라도 문구로 잡아내기 위한 표식
_MODEL_GONE_KEYWORDS = ("no longer available", "not found", "not supported")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def build_endpoint(model: str) -> str:
    """모델 이름으로 generateContent 엔드포인트 URL을 만든다.

    ⚠️ API 키는 URL 쿼리스트링(?key=...)에 붙이지 않는다.
       쿼리스트링은 프록시/서버 접근 로그에 평문으로 남기 때문에,
       이 프로그램은 항상 x-goog-api-key 헤더로 키를 전송한다.
       (파일 상단 [API 키 보안 원칙] 4번 참고)
    """
    return f"{GEMINI_API_BASE}/models/{model}:generateContent"


# 하위 호환용 — 기존 코드가 이 상수를 참조할 수 있으므로 남겨둔다.
GEMINI_ENDPOINT = build_endpoint(GEMINI_MODEL)

# 실제로 응답에 성공한 모델. 연결 테스트 결과 표시에 사용한다.
ACTIVE_MODEL = GEMINI_MODEL

# HTTP 404(모델 단종/엔드포인트 오류) 전용 안내 문구.
# UI(main_window)가 이 문구로 오류 종류를 구분하므로 함부로 바꾸지 말 것.
MODEL_ENDPOINT_ERROR_HINT = "모델 엔드포인트 확인 필요"

# 키를 발급받는 곳 (설정 탭 안내에 사용)
GEMINI_API_KEY_ISSUE_URL = "https://aistudio.google.com/app/apikey"

# 키가 없을 때 UI가 띄울 표준 안내 문구
NO_API_KEY_MESSAGE = (
    "Google Gemini API 키가 등록되어 있지 않습니다.\n\n"
    "[⚙️ 설정] 탭 → 'Google Gemini API 설정' 그룹에서 키를 입력하고\n"
    "[API 키 저장] 버튼을 눌러주세요.\n\n"
    f"키 발급: {GEMINI_API_KEY_ISSUE_URL}\n"
    "(또는 환경변수 GEMINI_API_KEY 에 키를 등록해도 됩니다.)"
)


# =====================================================================
# API 키 로드
# =====================================================================
def get_gemini_api_key(settings: dict) -> str:
    """
    Gemini API 키를 가져온다. 하드코딩된 키는 존재하지 않는다.

    우선순위
      ① settings["gemini_api_key"]  (설정 탭에서 사용자가 직접 입력한 값)
      ② 환경변수 GEMINI_API_KEY
    둘 다 없으면 빈 문자열을 돌려준다.
    """
    key = (settings or {}).get("gemini_api_key", "") or ""
    key = key.strip()
    if key:
        return key
    return (os.environ.get("GEMINI_API_KEY", "") or "").strip()


def has_gemini_api_key(settings: dict) -> bool:
    """AI 기능을 호출하기 전에 키 등록 여부를 확인할 때 쓴다."""
    return bool(get_gemini_api_key(settings))


def mask_api_key(key: str) -> str:
    """로그/화면 표시용 마스킹 (앞 4자리만 남김). 키 전체는 절대 노출하지 않는다."""
    if not key:
        return "(없음)"
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 4)


def _scrub(text: str, api_key: str) -> str:
    """예외 메시지 등에 키가 섞여 나오는 사고를 막기 위한 최종 방어선."""
    if api_key and text:
        return text.replace(api_key, "[API_KEY]")
    return text


# =====================================================================
# 저수준 API 호출 (동기) — 반드시 QThread 안에서만 호출할 것
# =====================================================================
def is_model_endpoint_error(message: str) -> bool:
    """오류 메시지가 '모델 단종/엔드포인트 문제'인지 판별한다.

    UI는 이 결과에 따라 안내 문구를 바꾼다. (키 문제인데 "모델을 바꾸세요"라고
    안내하거나, 그 반대로 잘못 안내하는 것을 막기 위함)
    """
    if not message:
        return False
    low = message.lower()
    if MODEL_ENDPOINT_ERROR_HINT in message or "http 404" in low:
        return True
    return any(k in low for k in _MODEL_GONE_KEYWORDS)


def _request_once(api_key: str, model: str, prompt: str, timeout: int):
    """단일 모델로 한 번 요청한다.
    반환: (성공여부, 텍스트 또는 오류사유, 모델단종여부)
    """
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            # [v2.0.1] temperature / top_p / top_k 는 2026-07-21자로 Deprecated
            #   되었고 Gemini 3 계열에서는 무시되거나 경고 대상이므로 보내지 않는다.
            # maxOutputTokens 를 1024 → 4096 으로 올린 이유:
            #   Gemini 3 계열은 "thinking" 토큰도 이 한도를 함께 소모한다.
            #   1024로 두면 사고 과정만으로 한도가 차서 본문이 빈 채로
            #   (finishReason=MAX_TOKENS) 돌아오는 일이 생긴다.
            "maxOutputTokens": 4096,
        },
    }

    try:
        req = urllib.request.Request(
            build_endpoint(model),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                # 키는 URL이 아니라 헤더로 전달한다 (로그 노출 방지)
                "x-goog-api-key": api_key,
                "User-Agent": f"{APP_NAME}/{APP_VERSION}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            body = json.loads(e.read().decode("utf-8", errors="ignore"))
            detail = body.get("error", {}).get("message", "")
        except Exception:
            detail = ""

        # ---- [v2.0.1] HTTP 404 = 모델이 단종되었거나 이름이 틀린 경우 ----
        if e.code == 404 or (detail and any(k in detail.lower() for k in _MODEL_GONE_KEYWORDS)):
            msg = (
                f"[{MODEL_ENDPOINT_ERROR_HINT}] 요청한 모델 '{model}' 을(를) 사용할 수 없습니다.\n"
                f"(HTTP {e.code}) Google이 해당 모델을 종료했거나 모델 이름이 잘못되었습니다.\n"
                "→ ai/gemini_advisor.py 의 GEMINI_MODEL 상수를 현재 제공 중인 모델로 바꿔주세요.\n"
                "   사용 가능한 모델 목록: https://ai.google.dev/gemini-api/docs/models\n"
                "   단종 일정: https://ai.google.dev/gemini-api/docs/deprecations"
            )
            if detail:
                msg += f"\n서버 응답: {detail}"
            return False, _scrub(msg, api_key), True

        if e.code in (400, 401, 403):
            hint = "API 키가 올바르지 않거나 권한이 없습니다."
        elif e.code == 429:
            hint = "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        elif e.code in (500, 502, 503, 504):
            hint = "Gemini 서버가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요."
        else:
            hint = "Gemini 서버가 오류를 반환했습니다."
        return False, _scrub(f"{hint} (HTTP {e.code}) {detail}".strip(), api_key), False
    except urllib.error.URLError as e:
        return False, _scrub(f"네트워크에 연결하지 못했습니다: {e.reason}", api_key), False
    except Exception as e:
        return False, _scrub(f"요청 중 오류가 발생했습니다: {e}", api_key), False

    # ---- 정상 응답 파싱 ----
    try:
        candidates = data.get("candidates") or []
        if not candidates:
            blocked = (data.get("promptFeedback") or {}).get("blockReason")
            if blocked:
                return False, f"응답이 차단되었습니다 (사유: {blocked}).", False
            return False, "응답이 비어 있습니다.", False

        finish = candidates[0].get("finishReason") or ""
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()

        if not text:
            if finish == "MAX_TOKENS":
                return False, (
                    "응답 길이 한도(maxOutputTokens)에 먼저 도달해 본문이 비었습니다.\n"
                    "ai/gemini_advisor.py 의 maxOutputTokens 값을 늘려보세요."
                ), False
            if finish == "SAFETY":
                return False, "안전 필터에 걸려 응답이 차단되었습니다.", False
            return False, f"응답 본문이 비어 있습니다. (finishReason={finish or '알 수 없음'})", False

        return True, text, False
    except Exception as e:
        return False, f"응답을 해석하지 못했습니다: {e}", False


def discover_available_model(api_key: str, timeout: int = 15):
    """[v2.0.1] ListModels API로 실제 사용 가능한 모델을 찾아본다.

    하드코딩한 후보가 전부 단종되었을 때의 마지막 자동 복구 수단이다.
    generateContent를 지원하는 모델 중 flash 계열을 우선해서 하나 고른다.
    실패하면 None을 돌려준다. (실패해도 프로그램은 정상 동작해야 한다)
    """
    try:
        req = urllib.request.Request(
            f"{GEMINI_API_BASE}/models?pageSize=200",
            headers={
                "x-goog-api-key": api_key,
                "User-Agent": f"{APP_NAME}/{APP_VERSION}",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None

    exclude = ("embedding", "image", "tts", "audio", "live", "veo", "imagen",
               "lyria", "robotics", "gemma", "aqa", "transcribe")
    names = []
    for m in (data.get("models") or []):
        name = (m.get("name") or "").replace("models/", "")
        methods = m.get("supportedGenerationMethods") or []
        if not name or (methods and "generateContent" not in methods):
            continue
        if any(k in name.lower() for k in exclude):
            continue
        names.append(name)

    if not names:
        return None

    def rank(n: str):
        low = n.lower()
        # flash 우선(저렴/빠름) → 정식판 우선 → 이름 역순(대체로 최신)
        return (0 if "flash" in low else 1,
                1 if ("preview" in low or "exp" in low) else 0,
                [-ord(c) for c in low])

    names.sort(key=rank)
    return names[0]


def call_gemini(api_key: str, prompt: str, timeout: int = 30):
    """
    Gemini generateContent 엔드포인트를 호출한다.
    반환: (성공여부: bool, 응답텍스트 또는 오류사유: str)

    [v2.0.1] 기본 모델이 404(단종)로 실패하면 GEMINI_FALLBACK_MODELS를 차례로
    시도하고, 그것도 모두 실패하면 ListModels로 사용 가능한 모델을 자동 탐색한다.
    키 오류·네트워크 오류처럼 모델과 무관한 실패는 재시도하지 않고 즉시 반환한다.

    ⚠️ 네트워크 대기가 있으므로 UI 스레드에서 직접 부르면 창이 멈춘다.
       항상 아래 GeminiAdvisorThread / GeminiConnectionTestThread를 통해 호출한다.
    """
    ok, text, _model = call_gemini_detailed(api_key, prompt, timeout)
    return ok, text


def call_gemini_detailed(api_key: str, prompt: str, timeout: int = 30):
    """call_gemini와 같지만 실제로 응답한 모델 이름까지 돌려준다.
    반환: (성공여부, 텍스트 또는 오류사유, 사용된 모델명)
    """
    global ACTIVE_MODEL

    if not api_key:
        return False, "API 키가 없습니다.", GEMINI_MODEL

    tried = []
    first_error = ""

    for model in (GEMINI_MODEL,) + tuple(GEMINI_FALLBACK_MODELS):
        if model in tried:
            continue
        tried.append(model)

        ok, text, model_gone = _request_once(api_key, model, prompt, timeout)
        if ok:
            ACTIVE_MODEL = model
            return True, text, model
        if not model_gone:
            # 모델과 무관한 실패(키/네트워크/한도)는 다른 모델로 바꿔도 소용없다.
            return False, text, model
        if not first_error:
            first_error = text

    # 후보가 전부 단종된 경우 — 실제 사용 가능한 모델을 조회해서 한 번 더 시도
    discovered = discover_available_model(api_key, timeout=min(timeout, 15))
    if discovered and discovered not in tried:
        ok, text, _gone = _request_once(api_key, discovered, prompt, timeout)
        if ok:
            ACTIVE_MODEL = discovered
            return True, text, discovered

    detail = (
        f"\n\n시도한 모델: {', '.join(tried)}"
        + (f"\n서버가 알려준 사용 가능 모델(추정): {discovered}" if discovered else "")
    )
    return False, (first_error or f"[{MODEL_ENDPOINT_ERROR_HINT}] 사용 가능한 모델을 찾지 못했습니다.") + detail, GEMINI_MODEL


# =====================================================================
# 프롬프트 구성
# =====================================================================
def build_precheck_prompt(summary: dict) -> str:
    """
    사전 점검 화면에서 사용자가 체크한 항목들을 요약해 프롬프트로 만든다.
    summary는 make_precheck_summary()가 만든 dict.
    """
    lines = []
    lines.append(f"[시스템] {summary.get('os', '알 수 없음')}")
    lines.append(
        f"[메모리] 전체 {summary.get('ram_total_mb', 0)}MB 중 "
        f"{summary.get('ram_used_pct', 0)}% 사용 중"
    )
    lines.append(f"[최적화 강도] {summary.get('intensity', '-')}단계")
    lines.append("")

    ram_items = summary.get("ram_items") or []
    if ram_items:
        lines.append("■ RAM 워킹셋 트림 대상 (프로세스를 종료하지 않고 메모리만 반납시킴)")
        for name, pid, mem in ram_items:
            lines.append(f"  - {name} (PID {pid}, {mem}MB 사용)")
        lines.append("")

    cpu_items = summary.get("cpu_items") or []
    if cpu_items:
        lines.append("■ CPU 우선순위 낮춤 대상 (종료가 아니라 우선순위만 조정, 되돌리기 가능)")
        for name, pid, pct in cpu_items:
            lines.append(f"  - {name} (PID {pid}, 시스템 전체 대비 CPU {pct}%)")
        lines.append("")

    others = summary.get("other_items") or []
    if others:
        lines.append("■ 기타 정리 항목")
        for item in others:
            lines.append(f"  - {item}")
        lines.append("")

    body = "\n".join(lines)

    return f"""당신은 Windows 시스템 최적화 도우미입니다. 아래는 사용자가
'{APP_NAME}' 프로그램에서 최적화를 실행하기 직전에 선택한 항목 목록입니다.

{body}
각 항목이 지금 이 PC 상태에서 실제로 최적화할 만한 대상인지 검토해주세요.
특히 다음을 중점적으로 봐주세요.
 - 백신/보안 소프트웨어, 드라이버 서비스, 백업 동기화 클라이언트처럼
   건드리면 안 되는 필수 프로그램이 섞여 있는지
 - 지금 사용자가 작업 중일 가능성이 높아 우선순위를 낮추면 체감 성능이
   오히려 나빠질 프로그램이 있는지
 - 효과가 거의 없어 굳이 할 필요 없는 항목이 있는지

출력 형식 (한국어, 마크다운 기호 없이 일반 텍스트로):
1) 각 프로세스/항목마다 한 줄씩:  이름 — [권장|주의|제외] — 한 줄 이유
2) 마지막에 "종합 의견:" 으로 시작하는 3줄 이내 요약

전체 20줄을 넘기지 말고, 확신이 없으면 [주의]로 분류하세요."""


def make_precheck_summary(ram_selected, cpu_selected, files_count, browser_count,
                          dns_selected, intensity, os_name, ram_total_mb, ram_used_pct) -> dict:
    """UI가 가진 사전 점검 결과를 이 모듈이 이해하는 형태로 정리한다.
    (파일 경로 같은 민감 정보는 담지 않고 '개수'만 담는다.)"""
    other_items = []
    if files_count:
        other_items.append(f"임시(SSD) 캐시 파일 {files_count}개 → 휴지통으로 이동")
    if browser_count:
        other_items.append(f"브라우저 캐시 파일 {browser_count}개 → 휴지통으로 이동")
    if dns_selected:
        other_items.append("DNS 캐시 초기화 (ipconfig /flushdns)")

    return {
        "os": os_name,
        "ram_total_mb": ram_total_mb,
        "ram_used_pct": ram_used_pct,
        "intensity": intensity,
        "ram_items": [(name, pid, mem) for pid, name, mem in (ram_selected or [])],
        "cpu_items": [(name, pid, pct) for pid, name, pct in (cpu_selected or [])],
        "other_items": other_items,
    }


# =====================================================================
# 백그라운드 스레드 (UI 프리징 방지)
# =====================================================================
class GeminiAdvisorThread(QThread):
    """사전 점검 항목에 대한 AI 조언을 백그라운드에서 받아온다.

    이 파일의 기존 관례(UpdateCheckThread 등)와 동일하게, 네트워크 대기는
    전부 QThread로 분리해 UI가 멈추지 않도록 한다."""

    advice_ready = pyqtSignal(bool, str)  # (성공여부, 조언 텍스트 또는 오류 메시지)

    def __init__(self, api_key: str, summary: dict, parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self.summary = summary

    def run(self):
        prompt = build_precheck_prompt(self.summary)
        ok, text = call_gemini(self._api_key, prompt, timeout=30)
        self.advice_ready.emit(ok, text)


class GeminiConnectionTestThread(QThread):
    """설정 탭의 [연결 테스트] 버튼용. 아주 짧은 요청 하나로 키 유효성만 확인한다."""

    result_ready = pyqtSignal(bool, str)

    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self._api_key = api_key

    def run(self):
        ok, text, model = call_gemini_detailed(
            self._api_key,
            "연결 확인용 테스트입니다. 다른 말 없이 정확히 'OK' 라고만 답하세요.",
            timeout=20,
        )
        if ok:
            msg = f"연결 성공! (모델: {model})\n응답: {text[:80]}"
            # 기본 모델이 아니라 대체 모델로 성공했다면 사용자에게 알려준다.
            if model != GEMINI_MODEL:
                msg += (
                    f"\n\n⚠️ 기본 모델 '{GEMINI_MODEL}' 은(는) 응답하지 않아\n"
                    f"대체 모델 '{model}' 로 연결했습니다.\n"
                    "ai/gemini_advisor.py 의 GEMINI_MODEL 상수를 이 모델로 바꿔두면\n"
                    "매번 대체 모델을 찾는 지연이 사라집니다."
                )
            self.result_ready.emit(True, msg)
        else:
            self.result_ready.emit(False, text)
