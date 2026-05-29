"""
LLM 배우 (Sonnet 4.6) — Anthropic client + 시스템 프롬프트 로더
"""

import os
import re
from pathlib import Path

import anthropic


ROOT = Path(__file__).parent.parent
SYSTEM_PROMPT_FILE = ROOT / "docs" / "yuran_system_prompt_v3.md"
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
