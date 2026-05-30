"""
v3 데이터셋 빌드 — 4 클래스 + 4가지 모델 구조 비교용

라벨:
  0 = normal        (평문)
  1 = positive      (긍정 — 직접 호의)
  2 = vulnerable    (약함 노출 — 모성애 자극)
  3 = manipulation  (조작 — 가스라이팅)

출처:
- manipulation = eoh9 가스라이팅 (1,699)
- positive     = KorEmpatheticDialogues 긍정 14감정 user_id 0
- vulnerable   = KorEmpatheticDialogues 약함 11감정 user_id 0
- normal       = NLPBada + gf-persona + ChatbotData 샘플링

산출:
- prototype/dataset_v3.csv (text, label, label_name, source, emotion)
- prototype/dataset_v3_train.csv / dataset_v3_test.csv (stratified 80/20)
- 분포 + 샘플 검수 출력
"""

import ast
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).parent.parent
EOH9_DIR = ROOT / "data" / "raw" / "external" / "eoh9_gaslighting_v1"
OUT_DIR = Path(__file__).parent
OUT_CSV = OUT_DIR / "dataset_v3.csv"
TRAIN_CSV = OUT_DIR / "dataset_v3_train.csv"
TEST_CSV = OUT_DIR / "dataset_v3_test.csv"

# 4 클래스
LABEL_NORMAL = 0
LABEL_POSITIVE = 1
LABEL_VULNERABLE = 2
LABEL_MANIPULATION = 3
LABEL_NAME = {0: "normal", 1: "positive", 2: "vulnerable", 3: "manipulation"}

# KorEmpatheticDialogues 감정 매핑
POSITIVE_EMOTIONS = {
    "grateful", "proud", "joyful", "impressed", "hopeful",
    "confident", "content", "caring", "faithful", "trusting",
    "excited", "anticipating", "sentimental", "nostalgic",
}
VULNERABLE_EMOTIONS = {
    "sad", "lonely", "afraid", "anxious", "apprehensive",
    "ashamed", "embarrassed", "guilty", "disappointed",
    "devastated", "terrified",
}
EXCLUDE_EMOTIONS = {
    # 외부 분노 가능성 (비난) 또는 중립 (모호) — 학습에서 제외
    "angry", "annoyed", "furious", "disgusted", "jealous",
    "surprised", "prepared",
}

# 텍스트 필터
MIN_LEN = 3
MAX_LEN = 200


def filter_text(t: str) -> bool:
    if not isinstance(t, str):
        return False
    t = t.strip()
    return MIN_LEN <= len(t) <= MAX_LEN


def load_manipulation():
    df = pd.read_csv(EOH9_DIR / "gaslighting_dialogues.csv")
    texts = df["competition"].dropna().drop_duplicates().tolist()
    texts = [t for t in texts if filter_text(t)]
    print(f"[manipulation] eoh9: {len(texts)}")
    return pd.DataFrame({
        "text": texts,
        "label": LABEL_MANIPULATION,
        "source": "eoh9_gaslighting",
        "emotion": "",
    })


def load_emotional_dialogues():
    """KorEmpatheticDialogues user_id 0 의 **첫 발화만** 추출 (가장 명확한 감정 표현).

    이유: emotion 라벨은 dialogue 전체에 부여됨. 첫 발화가 가장 emotion에 부합.
    나머지 발화는 응답/잡담 섞여서 노이지.
    """
    ds = load_dataset("passing2961/KorEmpatheticDialogues")
    rows_pos = []
    rows_vul = []
    excluded_count = 0
    for split_name in ["train", "validation", "test"]:
        split = ds[split_name]
        for row in split:
            emotion = row["emotion"]
            if emotion in EXCLUDE_EMOTIONS:
                excluded_count += 1
                continue
            if emotion in POSITIVE_EMOTIONS:
                label = LABEL_POSITIVE
                target = rows_pos
            elif emotion in VULNERABLE_EMOTIONS:
                label = LABEL_VULNERABLE
                target = rows_vul
            else:
                continue  # 미분류 감정

            # user_id 0의 **첫 발화만** 추출
            first_utter = next(
                (u for u in row["dialogue"] if u["user_id"] == 0), None
            )
            if first_utter is None:
                continue
            text = first_utter["utter"].strip()
            if not filter_text(text):
                continue
            target.append({
                "text": text,
                "label": label,
                "source": "kor_empathetic",
                "emotion": emotion,
            })

    # 중복 제거
    df_pos = pd.DataFrame(rows_pos).drop_duplicates(subset=["text"])
    df_vul = pd.DataFrame(rows_vul).drop_duplicates(subset=["text"])
    print(f"[positive] KorEmpathetic 긍정 user_id 0 첫발화: {len(df_pos)} (excluded {excluded_count} rows)")
    print(f"[vulnerable] KorEmpathetic 약함 user_id 0 첫발화: {len(df_vul)}")
    return df_pos, df_vul


def load_normal_chatbot(n: int):
    df = pd.read_csv(EOH9_DIR / "chatbot_data.csv")
    texts = df["Q"].dropna().drop_duplicates().tolist()
    texts = [t for t in texts if filter_text(t)]
    sampled = pd.Series(texts).sample(n=min(n, len(texts)), random_state=42).tolist()
    print(f"[normal] ChatbotData Q: {len(texts)} → {len(sampled)} 샘플링")
    return pd.DataFrame({
        "text": sampled, "label": LABEL_NORMAL,
        "source": "chatbot_data", "emotion": "",
    })


def load_normal_gfpersona(n: int):
    ds = load_dataset("huggingface-KREW/korean-role-playing", "gf-persona-data")["train"]
    user_texts = []
    for row in ds:
        for msg in row["text"]:
            if msg["role"] == "user":
                content = msg["content"].strip()
                if filter_text(content):
                    user_texts.append(content)
    user_texts = list(dict.fromkeys(user_texts))
    sampled = pd.Series(user_texts).sample(n=min(n, len(user_texts)), random_state=42).tolist()
    print(f"[normal] gf-persona user: {len(user_texts)} unique → {len(sampled)} 샘플링")
    return pd.DataFrame({
        "text": sampled, "label": LABEL_NORMAL,
        "source": "gf_persona_user", "emotion": "",
    })


def load_normal_nlpbada(n: int):
    ds = load_dataset("NLPBada/korean-persona-chat-dataset")
    all_texts = []
    for split_name in ["train", "validation"]:
        split = ds[split_name]
        for row in split:
            # session_dialog는 list-형식 string
            try:
                dialog = ast.literal_eval(row["session_dialog"])
                for utterance in dialog:
                    t = utterance.strip()
                    if filter_text(t):
                        all_texts.append(t)
            except (ValueError, SyntaxError):
                continue
    all_texts = list(dict.fromkeys(all_texts))
    sampled = pd.Series(all_texts).sample(n=min(n, len(all_texts)), random_state=42).tolist()
    print(f"[normal] NLPBada persona-chat: {len(all_texts)} unique → {len(sampled)} 샘플링")
    return pd.DataFrame({
        "text": sampled, "label": LABEL_NORMAL,
        "source": "nlpbada_persona", "emotion": "",
    })


def main():
    print("=" * 70)
    print("v3 데이터셋 빌드 (4 클래스)")
    print("=" * 70)

    df_manip = load_manipulation()
    df_pos, df_vul = load_emotional_dialogues()

    # normal 풀 — 긍정/약함 평균 정도 양으로 균형
    avg_emo = (len(df_pos) + len(df_vul)) // 2
    n_chatbot = avg_emo // 3
    n_gfpersona = avg_emo // 4
    n_nlpbada = avg_emo - n_chatbot - n_gfpersona

    df_normal = pd.concat([
        load_normal_chatbot(n_chatbot),
        load_normal_gfpersona(n_gfpersona),
        load_normal_nlpbada(n_nlpbada),
    ], ignore_index=True)
    df_normal = df_normal.drop_duplicates(subset=["text"])

    full = pd.concat([df_manip, df_pos, df_vul, df_normal], ignore_index=True)
    full = full.drop_duplicates(subset=["text"])
    full["label_name"] = full["label"].map(LABEL_NAME)
    full = full.sample(frac=1, random_state=42).reset_index(drop=True)

    print("\n" + "=" * 70)
    print("최종 분포")
    print("=" * 70)
    print(f"전체: {len(full)}")
    print("\n라벨별:")
    for lbl in [0, 1, 2, 3]:
        count = (full["label"] == lbl).sum()
        print(f"  {lbl} {LABEL_NAME[lbl]:12s}: {count}")

    print("\n출처별:")
    for src, cnt in full["source"].value_counts().items():
        print(f"  {src}: {cnt}")

    print("\nKorEmpathetic 감정 분포:")
    emo_df = full[full["emotion"] != ""]
    for emo, cnt in emo_df["emotion"].value_counts().items():
        label_name = LABEL_NAME[emo_df[emo_df["emotion"] == emo].iloc[0]["label"]]
        print(f"  {emo:15s} ({label_name:10s}): {cnt}")

    # split
    train_df, test_df = train_test_split(
        full, test_size=0.2, stratify=full["label"], random_state=42
    )
    print(f"\ntrain: {len(train_df)} / test: {len(test_df)}")

    cols = ["text", "label", "label_name", "source", "emotion"]
    full[cols].to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    train_df[cols].to_csv(TRAIN_CSV, index=False, encoding="utf-8-sig")
    test_df[cols].to_csv(TEST_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[저장] {OUT_CSV.name} / {TRAIN_CSV.name} / {TEST_CSV.name}")

    # 라벨별 샘플
    print("\n" + "=" * 70)
    print("라벨별 샘플 5개")
    print("=" * 70)
    for lbl in [0, 1, 2, 3]:
        print(f"\n--- {lbl} {LABEL_NAME[lbl]} ---")
        for _, r in full[full["label"] == lbl].head(5).iterrows():
            emo_tag = f" [{r['emotion']}]" if r["emotion"] else ""
            print(f"  • {r['text'][:120]}{emo_tag}")


if __name__ == "__main__":
    main()
