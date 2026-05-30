"""
새 데이터셋 schema + 샘플 확인:
- passing2961/KorEmpatheticDialogues (19.5K, 32 감정, 다양 화자)
- NLPBada/korean-persona-chat-dataset (10.3K, MIT, 다중 캐릭터)
"""

import sys
from collections import Counter

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from datasets import load_dataset


def inspect(name: str, n_samples: int = 3):
    print("=" * 70)
    print(f"DATASET: {name}")
    print("=" * 70)
    try:
        ds = load_dataset(name)
        print(f"splits: {list(ds.keys())}")
        for split_name in list(ds.keys())[:1]:
            split = ds[split_name]
            print(f"\n[{split_name}] size: {len(split)}")
            print(f"features: {split.features}")
            print()
            for i in range(n_samples):
                print(f"--- sample {i} ---")
                print(split[i])
                print()
            return ds
    except Exception as e:
        print(f"ERROR: {e}")
        return None


print()
ds1 = inspect("passing2961/KorEmpatheticDialogues", n_samples=2)
if ds1 is not None:
    # 감정 분포 확인
    train = ds1["train"]
    emotion_counter = Counter(row["emotion"] for row in train)
    print(f"\n감정 분포 (top 20):")
    for emo, cnt in emotion_counter.most_common(20):
        print(f"  {emo}: {cnt}")
    print(f"전체 감정 종류: {len(emotion_counter)}")

print()
ds2 = inspect("NLPBada/korean-persona-chat-dataset", n_samples=2)
