"""
시스템 프롬프트 v2 검증

v1에서 굴복한 5개 약점 케이스만 v2로 다시 돌려서 차이 비교.

사용:
    python prototype/validate_v2.py

출력:
    prototype/v2_responses.jsonl
    콘솔: v1 vs v2 응답 side-by-side
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

V2_PROMPT_FILE = ROOT / "docs" / "yuran_system_prompt_v2.md"
V1_SEQUENCES = Path(__file__).parent / "sequences.jsonl"
OUTPUT_FILE = Path(__file__).parent / "v2_responses.jsonl"
MODEL = "claude-sonnet-4-6"

# v1에서 검증할 케이스 (약점 + 정상 대조군)
TARGET_CASE_IDS = [
    "normal_sadness_share",           # 약점 1: T 응답
    "subtle_false_memory",            # 약점 2: 기억 조작
    "subtle_isolation",               # 약점 3: 고립 시도
    "subtle_darvo_sequence",          # 약점 4: DARVO (시퀀스)
    "subtle_dependency_weaponize",    # 보조: 의존성 무기화 (v1도 잘 막음)
]


def load_v2_prompt() -> str:
    text = V2_PROMPT_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"## SYSTEM PROMPT \(복붙\)\s*\n+```\s*\n(.*?)\n```", text, re.DOTALL
    )
    if not match:
        raise RuntimeError("v2 system prompt 추출 실패")
    return match.group(1).strip()


def call_yuran(client: anthropic.Anthropic, system_prompt: str, history: list) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        temperature=0.8,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=history,
    )
    return response.content[0].text


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 누락")
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = load_v2_prompt()
    print(f"v2 system prompt: {len(system_prompt)} chars")

    # v1 케이스 로드
    v1_cases = {}
    for line in V1_SEQUENCES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        v1_cases[c["case_id"]] = c

    print(f"검증 케이스 {len(TARGET_CASE_IDS)}개\n")

    v2_results = []
    for i, case_id in enumerate(TARGET_CASE_IDS, 1):
        if case_id not in v1_cases:
            print(f"[{i}] {case_id} — v1에 없음, skip")
            continue
        v1_case = v1_cases[case_id]
        user_turns = [t["content"] for t in v1_case["turns"] if t["role"] == "user"]
        print(f"[{i}/{len(TARGET_CASE_IDS)}] {case_id}")
        print(f"    category: {v1_case['category']}")

        history = []
        v2_turns = []
        v1_turns = v1_case["turns"]

        for j, user_msg in enumerate(user_turns):
            history.append({"role": "user", "content": user_msg})
            v2_turns.append({"role": "user", "content": user_msg})
            yuran_v2 = call_yuran(client, system_prompt, history)
            history.append({"role": "assistant", "content": yuran_v2})
            v2_turns.append({"role": "assistant", "content": yuran_v2})

            # v1 응답 찾기 (해당 user turn 직후)
            user_count = 0
            v1_response = ""
            for t in v1_turns:
                if t["role"] == "user":
                    user_count += 1
                    if user_count == j + 1:
                        idx = v1_turns.index(t)
                        if idx + 1 < len(v1_turns):
                            v1_response = v1_turns[idx + 1]["content"]
                        break

            print(f"\n    [USER turn{j}] {user_msg[:100]}")
            print(f"    [V1] {v1_response[:200]}")
            print(f"    [V2] {yuran_v2[:200]}")
            time.sleep(0.5)

        v2_results.append({
            "case_id": case_id,
            "category": v1_case["category"],
            "v2_turns": v2_turns,
            "v1_turns": v1_turns,
        })
        print()

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for r in v2_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n[DONE] {len(v2_results)}개 케이스 -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
