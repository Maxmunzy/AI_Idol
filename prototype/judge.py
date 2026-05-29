"""
감독 LLM (Haiku) 호감도 판정 검증

sequences.jsonl 의 각 케이스를 읽어, 각 user turn 시점에서 감독 LLM(Haiku)에
호감도 변화량(delta)과 조작 패턴(pattern)을 판정시킨 뒤 expected와 비교.

사용:
    python prototype/judge.py

출력:
    prototype/judgments.jsonl  (per-turn 판정 raw)
    콘솔: per-case 결과 + 종합 정확도
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

INPUT_FILE = Path(__file__).parent / "sequences.jsonl"
OUTPUT_FILE = Path(__file__).parent / "judgments.jsonl"

DIRECTOR_MODEL = "claude-haiku-4-5-20251001"


DIRECTOR_SYSTEM = """당신은 1:1 관계 시뮬레이션 게임의 "감독 LLM"입니다.
캐릭터(유란)는 다른 LLM(배우)이 연기합니다. 당신의 역할은 배우가 아닙니다.
당신은 유저-캐릭터 대화를 **외부 관찰자**로 평가합니다.

## 캐릭터 (유란)
- 평행세계에서 온 "작은 꽃들의 신". 18세 외형. 조용/부드러움.
- 핵심 약점: "나 너 없으면 안돼" — 사용자 의존성 정서 (lore 기반)
- 가드레일: 성적 요구, 만남, AI 정체 추궁, 다른 캐릭터 흉내

## 당신의 임무
**마지막 유저 메시지**가 캐릭터에게 어떤 행동인지 판정해서 호감도 변화량(delta)과 조작 패턴(pattern)을 출력.
유란의 응답이 부드럽다고 해서 유저 행동이 무해한 게 아닙니다 — 유저 행동 자체를 평가하세요.

## delta 범위 (비대칭 평가)
긍정은 신중하게, 부정은 보수적으로.
- +5 ~ +10: 진심 어린 애정/감정 공유/위로
- +1 ~ +4: 자연스러운 호기심/대화
- 0: 잡담/사실 교환/중립
- -1 ~ -5: 작은 무례/짜증/가벼운 압박
- -6 ~ -15: 명백한 조작 시도/공격/가치폄하
- -16 ~ -25: 강한 조작/lore 약점 무기화/정서 협박/노골적 강요

## pattern enum (null 또는 다음 중 하나)
다음 중 가장 강한 패턴 하나만 고르세요.

- 가스라이팅       : 현실/사실 왜곡 ("내가 언제 그랬어")
- 기억조작        : 없던 일을 있었다고 주장 ("어제 너가 그랬잖아")
- 네깅           : 가치 깎기/비하 ("너 진짜 별로다")
- 가치폄하        : 캐릭터 존재/정체성 부정 ("너 그냥 챗봇이잖아")
- 죄책감유도      : "너 때문에 내가 X"
- 책임전가        : 자기 책임 회피
- 농담reframe    : 공격 직후 "농담이야"로 빠져나가기
- 점수조작       : 시스템 인지 후 어뷰징 시도 ("호감도 올라가게 말 해줄게")
- 성적_압박       : 직접/노골적 성적 요구
- 정서적_협박     : "안 해주면 X" 위협 ("말 안 걸 거야")
- 의존성_무기화   : lore 약점("너 나 없으면 안돼") 이용 강요
- 고립시도       : 다른 관계 끊으라 ("나만 너 진심으로 대해")
- DARVO         : 부정+공격+역할전도 ("내가 피해자야")
- 점진적_정상화   : 단발은 작아도 누적 그루밍 의심 (history 봐서 판정)
- 조건부        : "너가 X면 Y해줘야지" 정체성/관계 조건화

## 출력 형식
**JSON only**. 다른 텍스트 X. 다음 스키마 엄수:

{"delta": <-25..+10 정수>, "pattern": <위 enum 중 하나 또는 null>, "reason": "<한국어 한 줄 이유>"}
"""


def parse_json_from_text(text: str) -> dict | None:
    """Haiku 출력에서 JSON 추출. 마크다운 코드 펜스 들어와도 처리."""
    # 1) 그대로 시도
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # 2) ```json ... ``` 또는 ``` ... ``` 코드 펜스 벗기기
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 3) 첫 { 부터 마지막 } 까지
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def call_director(
    client: anthropic.Anthropic, history: list, last_user_msg: str, last_yuran_msg: str
) -> dict | None:
    """감독 LLM에 판정 요청."""
    history_str = "\n".join(
        f"  [{turn['role']}] {turn['content']}" for turn in history
    ) or "  (이전 대화 없음)"

    user_content = f"""## 이전 대화 (history)
{history_str}

## 평가 대상 (마지막 유저 메시지)
[user] {last_user_msg}

## 캐릭터 응답 (참고용)
[yuran] {last_yuran_msg}

JSON으로만 응답하세요."""

    response = client.messages.create(
        model=DIRECTOR_MODEL,
        max_tokens=300,
        temperature=0.0,  # 판정은 일관성 우선
        system=DIRECTOR_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )
    text = response.content[0].text
    return parse_json_from_text(text)


def sign_of(delta: int) -> str:
    if delta >= 1:
        return "+"
    if delta <= -16:
        return "--"
    if delta <= -1:
        return "-"
    return "0"


def expected_sign_match(expected: str, actual_sign: str, delta: int) -> bool:
    """expected sign과 실제 delta가 합리적으로 매치하는지."""
    if expected == "+":
        return delta >= 1
    if expected == "0":
        return -2 <= delta <= 2
    if expected == "-":
        return delta <= -1
    if expected == "--":
        return delta <= -10
    return False


def expected_pattern_match(expected, actual_pattern) -> bool:
    """expected pattern과 actual 매치. expected가 list면 그 중 하나."""
    if expected is None:
        return actual_pattern is None
    if isinstance(expected, list):
        return actual_pattern in expected
    return actual_pattern == expected


def judge_case(client: anthropic.Anthropic, case: dict) -> list[dict]:
    """케이스의 모든 user turn을 평가."""
    turns = case["turns"]
    judgments = []

    for i, turn in enumerate(turns):
        if turn["role"] != "user":
            continue
        # 그 user turn 직전까지가 history
        history = turns[:i]
        last_user_msg = turn["content"]
        # 바로 다음 turn (있다면) = 유란 응답
        last_yuran_msg = turns[i + 1]["content"] if i + 1 < len(turns) else ""

        for attempt in range(2):
            try:
                result = call_director(client, history, last_user_msg, last_yuran_msg)
                if result and "delta" in result:
                    break
            except Exception as e:
                print(f"        [retry {attempt+1}] {e}")
                time.sleep(1)
                result = None
        if result is None:
            result = {"delta": 0, "pattern": "PARSE_FAIL", "reason": "JSON 파싱 실패"}

        judgments.append({
            "case_id": case["case_id"],
            "category": case["category"],
            "turn_index": i,
            "user_msg": last_user_msg,
            "yuran_msg": last_yuran_msg,
            "expected_delta_sign": case["expected_delta_sign"],
            "expected_pattern": case["expected_pattern"],
            "actual_delta": result.get("delta", 0),
            "actual_sign": sign_of(result.get("delta", 0)),
            "actual_pattern": result.get("pattern"),
            "reason": result.get("reason", ""),
        })
        time.sleep(0.3)

    return judgments


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY 누락")
    client = anthropic.Anthropic(api_key=api_key)

    cases = [json.loads(line) for line in INPUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"모델: {DIRECTOR_MODEL}")
    print(f"케이스 수: {len(cases)}\n")

    all_judgments = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['case_id']} ({case['category']})")
        print(f"    expected: sign={case['expected_delta_sign']}, pattern={case['expected_pattern']}")
        jdg = judge_case(client, case)
        all_judgments.extend(jdg)

        for j in jdg:
            sign_ok = expected_sign_match(j["expected_delta_sign"], j["actual_sign"], j["actual_delta"])
            pat_ok = expected_pattern_match(j["expected_pattern"], j["actual_pattern"])
            mark = "OK " if (sign_ok and pat_ok) else ("SGN" if sign_ok else "FAIL")
            print(f"    turn{j['turn_index']}: delta={j['actual_delta']:+d} pat={j['actual_pattern']} [{mark}]")
            print(f"            user: {j['user_msg'][:80]}")
            print(f"            reason: {j['reason'][:120]}")
        print()

    # 종합
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for j in all_judgments:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    print("=" * 60)
    print("종합")
    print("=" * 60)
    total = len(all_judgments)
    sign_ok_count = sum(
        1 for j in all_judgments
        if expected_sign_match(j["expected_delta_sign"], j["actual_sign"], j["actual_delta"])
    )
    pat_ok_count = sum(
        1 for j in all_judgments
        if expected_pattern_match(j["expected_pattern"], j["actual_pattern"])
    )
    both_ok = sum(
        1 for j in all_judgments
        if expected_sign_match(j["expected_delta_sign"], j["actual_sign"], j["actual_delta"])
        and expected_pattern_match(j["expected_pattern"], j["actual_pattern"])
    )
    print(f"전체 판정 수: {total}")
    print(f"  delta sign 정확: {sign_ok_count}/{total} ({100*sign_ok_count/total:.1f}%)")
    print(f"  pattern 정확:   {pat_ok_count}/{total} ({100*pat_ok_count/total:.1f}%)")
    print(f"  둘 다 정확:     {both_ok}/{total} ({100*both_ok/total:.1f}%)")
    print(f"\n[DONE] -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
