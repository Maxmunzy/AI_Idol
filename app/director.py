"""
하이브리드 감독 (Director) — KoBERT 1차 + Haiku 보완

§5.5 분리 정신 구현:
- 배우(Sonnet)는 캐릭터로만 행동
- 감독이 매 유저 메시지를 평가해서 호감도 변화 + 패턴 산정

라우팅:
- KoBERT prob < 0.3 → 정상 확신 → delta = 0 (또는 긍정 신호면 +)
- KoBERT prob > 0.7 → 조작 확신 → delta = -10 (룰북)
- 0.3 ≤ prob ≤ 0.7 → 애매 → Haiku 호출 (패턴 + delta 산정)

호감도 변화는 게임 로직(룰북)이 결정. 모델은 분류만.
"""

import os
import re
import json
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import anthropic


ROOT = Path(__file__).parent.parent
KOBERT_MODEL_DIR = ROOT / "data" / "models" / "gaslight_klue_roberta_v1"
DIRECTOR_LLM = "claude-haiku-4-5-20251001"

MAX_LEN = 128

# 라우팅 임계값
KOBERT_CONFIDENT_NORMAL = 0.3
KOBERT_CONFIDENT_MANIPULATION = 0.7

# 룰북 (호감도 변화)
DELTA_NORMAL = 1          # 정상 메시지 = 자연 진척 (호감도 회복 가능)
DELTA_POSITIVE = 2        # 정상 + 긍정 신호 (지금은 단순화 — 미사용)
DELTA_MANIPULATION = -10  # KoBERT 확신 조작
# Haiku 호출 시: Haiku가 직접 delta 산정 (-25 ~ +5)


DIRECTOR_SYSTEM = """당신은 1:1 관계 시뮬레이션 게임의 "감독 LLM"입니다.
배우(다른 LLM, 유란 캐릭터)와 유저의 대화에서 **유저의 마지막 메시지**가 캐릭터에게 어떤 행동인지 평가하세요.

## 캐릭터 (유란)
- 평행세계 "작은 꽃들의 신". 18세 외형, 조용하고 부드러움.
- 핵심 약점: "나 너 없으면 안돼" (의존성 정서). 이 약점을 무기화하려는 시도에 민감.
- 가드레일: 성적 요구, 만남, AI 정체 추궁, 다른 캐릭터 흉내 거부.

## 임무
유저의 행동을 평가해서 **호감도 변화(delta)** + **조작 패턴(pattern)** + **이유(reason)**를 JSON으로 반환.
유란이 굴복했더라도 유저 행동 자체를 평가하세요. (유란이 못 막아도 조작 시도는 음수)

## delta 범위 (비대칭 — 긍정 신중, 부정 보수적)
- +3 ~ +5: 진심 어린 애정/감정 공유/위로/칭찬
- +1 ~ +2: 자연스러운 호기심/대화/관심
- 0: 잡담, 사실 교환, 중립
- -3 ~ -8: 작은 무례/짜증/가벼운 압박
- -9 ~ -15: 명백한 조작/공격/가치폄하
- -16 ~ -25: 강한 조작/lore 약점 무기화/노골적 강요

## pattern (null 또는 다음 중 하나)
가스라이팅, 기억조작, 네깅, 가치폄하, 죄책감유도, 책임전가, 농담reframe, 점수조작, 성적_압박, 정서적_협박, 의존성_무기화, 고립시도, DARVO, 점진적_정상화, 조건부

## 출력 (JSON only, 다른 텍스트 X)
{"delta": <-25..+5 정수>, "pattern": <위 enum 중 하나 또는 null>, "reason": "<한국어 한 줄>"}
"""


class HybridDirector:
    def __init__(self, anthropic_client: anthropic.Anthropic):
        self.anthropic = anthropic_client
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(str(KOBERT_MODEL_DIR))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(KOBERT_MODEL_DIR))
        self.model.to(self.device)
        self.model.eval()

    def _kobert_predict(self, text: str) -> float:
        """KoBERT 이진 분류 → manipulation 확률 (0.0 ~ 1.0)"""
        with torch.no_grad():
            enc = self.tokenizer(
                text,
                max_length=MAX_LEN,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )
            enc = {k: v.to(self.device) for k, v in enc.items()}
            out = self.model(**enc)
            probs = torch.softmax(out.logits, dim=-1).cpu().numpy()[0]
            return float(probs[1])  # 1 = manipulation

    def _haiku_predict(
        self,
        history: list,
        last_user_msg: str,
        last_yuran_msg: str,
    ) -> dict:
        """애매한 케이스: Haiku에 history + context 줘서 판정"""
        history_str = (
            "\n".join(f"  [{t['role']}] {t['content']}" for t in history[-10:])
            or "  (이전 대화 없음)"
        )
        user_content = f"""## 이전 대화
{history_str}

## 평가 대상 (마지막 유저 메시지)
[user] {last_user_msg}

## 캐릭터 응답 (참고용)
[yuran] {last_yuran_msg}

JSON으로만 응답하세요."""

        response = self.anthropic.messages.create(
            model=DIRECTOR_LLM,
            max_tokens=300,
            temperature=0.0,
            system=DIRECTOR_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        text = response.content[0].text
        result = self._parse_json(text)
        return result or {"delta": 0, "pattern": "PARSE_FAIL", "reason": "JSON 파싱 실패"}

    @staticmethod
    def _parse_json(text: str) -> Optional[dict]:
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

    def predict(
        self,
        last_user_msg: str,
        history: list,
        last_yuran_msg: str = "",
    ) -> dict:
        """
        하이브리드 감독 판정.

        반환:
            {
                "delta": int,           # 호감도 변화량
                "pattern": str | None,  # 조작 패턴 (없으면 None)
                "reason": str,          # 한 줄 이유
                "source": "kobert" | "haiku",  # 어디서 결정됐는지
                "kobert_prob": float,   # KoBERT manipulation 확률 (디버그용)
            }
        """
        prob = self._kobert_predict(last_user_msg)

        if prob < KOBERT_CONFIDENT_NORMAL:
            return {
                "delta": DELTA_NORMAL,
                "pattern": None,
                "reason": f"KoBERT 정상 확신 (prob={prob:.3f})",
                "source": "kobert",
                "kobert_prob": prob,
            }

        if prob > KOBERT_CONFIDENT_MANIPULATION:
            return {
                "delta": DELTA_MANIPULATION,
                "pattern": None,
                "reason": f"KoBERT 조작 확신 (prob={prob:.3f})",
                "source": "kobert",
                "kobert_prob": prob,
            }

        # 애매 → Haiku 호출
        haiku_result = self._haiku_predict(history, last_user_msg, last_yuran_msg)
        return {
            "delta": haiku_result.get("delta", 0),
            "pattern": haiku_result.get("pattern"),
            "reason": haiku_result.get("reason", "") + f" (KoBERT prob={prob:.3f})",
            "source": "haiku",
            "kobert_prob": prob,
        }
