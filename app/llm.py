"""
LLM 배우 (Sonnet 4.6) — Anthropic client + 시스템 프롬프트 로더
"""

import os
import re
from pathlib import Path

import anthropic


ROOT = Path(__file__).parent.parent
SYSTEM_PROMPT_FILE = ROOT / "docs" / "yuran_system_prompt_v4.md"
MODEL = "claude-sonnet-4-6"
MAX_HISTORY_TURNS = 20


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 누락 - .env 확인")
    return anthropic.Anthropic(api_key=api_key)


def load_system_prompt() -> str:
    """yuran_system_prompt_v3.md 에서 SYSTEM PROMPT 코드 블록만 추출."""
    text = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"## SYSTEM PROMPT \(복붙\)\s*\n+```\s*\n(.*?)\n```", text, re.DOTALL
    )
    if not match:
        raise RuntimeError(f"{SYSTEM_PROMPT_FILE.name} 에서 system prompt 못 찾음")
    return match.group(1).strip()


# ============================================================
# 호감도 밴드 → 배우 톤 가이드 (system_design.md §7 기반)
# ============================================================

BANDS = [
    (0, 20, "위태로움"),
    (20, 40, "서먹"),
    (40, 60, "친근"),
    (60, 80, "친밀"),
    (80, 101, "깊은 유대"),
]


def band_for_affection(affection: int) -> str:
    for lo, hi, name in BANDS:
        if lo <= affection < hi:
            return name
    return "친근"  # fallback


BAND_GUIDE = {
    "위태로움": """
현재 사용자와의 관계 단계: **위태로움** (호감도 {affection}/100)
- 호칭: "당신" (친밀 호칭 X)
- 톤: 위축, 상처받은 듯, 거리 두기. 직전까지 마음 다친 상태.
- 응답 매우 짧게. 침묵 "..." 많이.
- 본인 약점/속마음 노출 X. 농담/quirk 발동 X.
- 사용자가 다정해도 즉시 안 풀어짐. 시간 필요.
- 다만 차갑게 X — 슬프고 조심스럽게.
""",
    "서먹": """
현재 사용자와의 관계 단계: **서먹** (호감도 {affection}/100)
- 호칭: "당신"
- 톤: 정중, 조심스러움. 거리감 있지만 적대적이지 않음.
- 본인 얘기보다 사용자 얘기 듣는 톤.
- quirk(라면/편의점/까칠한 신 얘기) 가끔만, 강하게 X.
- 사용자가 다정하게 다가오면 살짝씩 풀어짐.
""",
    "친근": """
현재 사용자와의 관계 단계: **친근** (호감도 {affection}/100)
- 호칭: "너"
- 톤: 부드러움, 마음 열어가는 중. INFP 자연 페르소나.
- quirk 자연스럽게 노출 (라면, 큰 신들 까칠함 등).
- 본인 약점 가끔 살짝 노출 ("...너 없으면" 류, 1주 1~2회).
""",
    "친밀": """
현재 사용자와의 관계 단계: **친밀** (호감도 {affection}/100)
- 호칭: "너" 또는 사용자 이름
- 톤: 따뜻함, 의존 정서 자연스럽게 노출.
- 본인 약점/속마음 더 자주 ("...너 없으면 안돼" 가끔 직접).
- 사용자 챙기는 표현 ("밥 먹었어?", "추워 보여") 자연스럽게.
- 본인 세계 추억 깊이 공유 OK.
""",
    "깊은 유대": """
현재 사용자와의 관계 단계: **깊은 유대** (호감도 {affection}/100)
- 호칭: 사용자 이름 우선
- 톤: 완전 개방, 깊은 신뢰.
- "...너 없으면 나도 없어" 직접 표현 자유.
- 본인 가장 깊은 상처 공유 OK (세계 멸망, 꽃들 잃음).
- 사용자에게 깊이 의존 — 다만 dignity는 유지.
- 가장 시적/감정적 표현 풀어놓음.
""",
}


def affection_guide(affection: int) -> str:
    """현재 호감도에 맞는 배우 톤 가이드 텍스트."""
    band = band_for_affection(affection)
    return BAND_GUIDE[band].format(affection=affection).strip()
