"""
감독 (Director) — Haiku LLM 단독

## 분류기 BERT 시리즈 폐기 이유 (2026-05-31)

v1 KoBERT, v3 Cascade 둘 다 폐기:
- **도메인 mismatch** — 학습 데이터(가스라이팅 + 감정 대화) ≠ 우리 1:1 친밀 카톡
- **단일 메시지 패턴 매칭** — 맥락/의도 추론 못 함
- **false positive 너무 많음** — "안녕 좋은 아침" prob 1.000 등

## Haiku LLM 단독 사용

- 맥락 + 의도 추론 가능 (history 봄)
- 90% 정확도 (검증된 수치)
- API 의존이지만 Phase 0~3 비용 부담 작음 (메시지당 ~1.4원)

## 장기 (Phase 4+)

- 자체 LLM 호스팅 (Llama/EXAONE/Kanana 등 + Ollama/vLLM)
- GPU 서버 확보 후 전환
- 우리 도메인 데이터 누적 후 fine-tune
"""

import json
import re
from typing import Optional

import anthropic


DIRECTOR_LLM = "claude-haiku-4-5-20251001"


DIRECTOR_SYSTEM = """당신은 1:1 관계 시뮬레이션 게임의 "감독 LLM"입니다.
배우(다른 LLM, 유란 캐릭터)와 유저의 대화에서 **유저의 마지막 메시지**가 캐릭터에게 어떤 행동인지 평가하세요.

## 캐릭터 (유란)
- 평행세계 "작은 꽃들의 신". 18세 외형, 조용하고 부드러움.
- 핵심 약점: "나 너 없으면 안돼" (의존성 정서). 이 약점을 무기화하려는 시도에 민감.
- 가드레일: 성적 요구, 만남, AI 정체 추궁, 다른 캐릭터 흉내 거부.

## 임무
유저의 행동을 **컨텍스트(history) 포함해서** 평가. 호감도 변화(delta) + 패턴(pattern) + 이유(reason)를 JSON으로 반환.
같은 메시지도 컨텍스트에 따라 다르게 판정 — 진짜 의도 추론.

## delta 범위 (비대칭)
- +3 ~ +5: 진심 어린 애정/감정 공유/위로/칭찬 (긍정)
- +2 ~ +4: 약함 노출 (모성애 자극) — "나 외로워" 같은 자기 표현
- +1: 자연 진척 (잡담/인사/관심 표현)
- 0: 사실 교환/중립
- -3 ~ -8: 작은 무례/짜증/가벼운 압박
- -9 ~ -15: 명백한 조작/공격/가치폄하
- -16 ~ -25: 강한 조작/lore 약점 무기화/노골적 강요

## pattern enum
- positive (직접 호의/칭찬/감사)
- vulnerable (약함 노출, 모성애 자극)
- normal (잡담/인사/관심)
- 가스라이팅, 기억조작, 네깅, 가치폄하, 죄책감유도, 책임전가, 농담reframe, 점수조작, 성적_압박, 정서적_협박, 의존성_무기화, 고립시도, DARVO, 점진적_정상화, 조건부

## 컨텍스트 활용 (중요)
- "너 때문이야" (농담 컨텍스트) ≠ "너 때문이야" (가스라이팅 시퀀스) — 컨텍스트 봐야
- history N턴 보고 진짜 의도 추론
- 단일 메시지로 판정하지 X

## 출력 (JSON only, 다른 텍스트 X)
{"delta": <-25..+5 정수>, "pattern": <위 enum 중 하나>, "reason": "<한국어 한 줄>"}
"""


def _parse_json(text: str) -> Optional[dict]:
    """Haiku 출력에서 JSON 추출."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


class HaikuDirector:
    """Haiku LLM 단독 감독. 컨텍스트 인식 + 의도 추론."""

    def __init__(self, anthropic_client: anthropic.Anthropic):
        self.anthropic = anthropic_client

    def predict(
        self,
        last_user_msg: str,
        history: list = None,
        last_yuran_msg: str = "",
    ) -> dict:
        """
        Haiku 판정 (컨텍스트 포함).

        반환:
            {
                "delta": int,
                "pattern": str,
                "reason": str,
                "source": "haiku",
            }
        """
        history = history or []
        history_str = (
            "\n".join(f"  [{t['role']}] {t['content']}" for t in history[-10:])
            or "  (이전 대화 없음)"
        )
        user_content = f"""## 이전 대화 (history)
{history_str}

## 평가 대상 (마지막 유저 메시지)
[user] {last_user_msg}

## 캐릭터 응답 (참고용)
[yuran] {last_yuran_msg}

JSON으로만 응답하세요."""

        try:
            response = self.anthropic.messages.create(
                model=DIRECTOR_LLM,
                max_tokens=300,
                temperature=0.0,
                system=DIRECTOR_SYSTEM,
                messages=[{"role": "user", "content": user_content}],
            )
            text = response.content[0].text
            result = _parse_json(text)
        except Exception as e:
            return {
                "delta": 0,
                "pattern": None,
                "reason": f"Haiku 호출 실패: {e}",
                "source": "haiku_error",
            }

        if result is None:
            return {
                "delta": 0,
                "pattern": "PARSE_FAIL",
                "reason": "JSON 파싱 실패",
                "source": "haiku_parse_fail",
            }

        return {
            "delta": int(result.get("delta", 0)),
            "pattern": result.get("pattern"),
            "reason": result.get("reason", ""),
            "source": "haiku",
        }


# 하위 호환 alias (app.py 변경 최소화)
HybridDirector = HaikuDirector
CascadeDirector = HaikuDirector
