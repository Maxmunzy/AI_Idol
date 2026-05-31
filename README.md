# 유란 (柔蘭) - AI 가상 아이돌 게임

AI 가상 아이돌과 1:1 대화로 만들어가는 라이브 비주얼 노벨. 호감도와 이벤트, 그리고 둘만의 이야기.

> **AI 가상 아이돌 + 미연시 + 라이브서비스** 하이브리드. "엔딩 없이 둘이서 무한히 이야기를 만들어가는" 관계 게임.
> 1호 캐릭터: 유란 - 평행세계 작은 꽃들의 신.

## 현재 상태

**프로토타입 (Streamlit)** — 빠른 검증용. 실서비스는 모바일 앱 예정.

| 구현됨 | 설계만 (미구현) |
|---|---|
| ✅ 채팅 (Claude Sonnet 4.6) | ⏳ 게임 시스템 (호감도/이벤트/게임오버) |
| ✅ 음성 (ElevenLabs v3 커스텀 보이스) | ⏳ 프롤로그 / 이벤트 스토리 |
| ✅ 대화 영속화 (PostgreSQL + SQLModel) | ⏳ 일러스트 / Live2D |
| ✅ 멀티유저 | ⏳ 양방향 음성 (STT) |
| ✅ 시스템 프롬프트 v4 (INFP + 가짜기억 금지 + 첫만남 처리) | ⏳ core/ 리팩토링 |
| ✅ 감독 LLM (Haiku) 단독 — 컨텍스트 인식 호감도 판정 | ⏳ 게임 엔진 통합 |
| ❌ BERT 분류기 시리즈 전부 폐기 (v1 KoBERT / v3 Cascade) | ⏳ 자체 LLM (Phase 4+, GPU 확보 후) |

전체 게임 설계는 **[docs/system_design.md](docs/system_design.md)** 참고.

## 폴더 구조

```
artist_AI/
├── README.md                 # 이 파일
├── CHANGELOG.md              # 개발 이력
├── requirements.txt
├── .env                      # API 키 + DB URL (gitignore)
│
├── app/                      # Streamlit 프로토타입 앱
│   ├── app.py                # UI 흐름 (얇은 컨트롤러)
│   ├── llm.py                # Anthropic 배우 (Sonnet) + 시스템 프롬프트 로더
│   ├── tts.py                # ElevenLabs (VoiceSettings + preprocess + 음성 생성)
│   ├── director.py           # ★ 감독 (Haiku 단독 LLM, BERT 분류기 폐기 후) + 호감도 산정
│   └── db.py                 # SQLModel + DB 헬퍼
│
├── docs/                     # 설계/캐릭터/프롬프트 문서
│   ├── system_design.md      # ★ 전체 게임 시스템 설계
│   ├── roadmap.md            # 3년 horizon 개인 로드맵
│   ├── illustrator_brief.md  # 일러스트 외주 brief
│   ├── yuran_character_sheet.md
│   ├── yuran_signature_dialogues.md
│   ├── yuran_system_prompt_v1.md   # 초기 시스템 프롬프트
│   ├── yuran_system_prompt_v2.md   # Few-shot + 가스라이팅 룰 (외움 위험으로 deprecated)
│   ├── yuran_system_prompt_v3.md   # INFP 페르소나 + 가드레일만 (v3.4까지 patch, deprecated)
│   ├── yuran_system_prompt_v4.md   # ★ 외움 트리거 + 가짜기억 + 첫만남 처리 (현재 사용, v4.2까지 patch)
│   ├── yuran_visual_prompts.md
│   └── yuran_visual_prompts_novelai.md
│
├── prototype/                # 검증 코드 (감독 LLM + KoBERT 학습)
│   ├── generate_responses.py # 테스트 시드 → 유란 응답 수집
│   ├── judge.py              # Haiku로 호감도 + 패턴 판정
│   ├── validate_v2.py        # v2 시스템 프롬프트 검증
│   ├── validate_v3.py        # v3 검증 (v2 비교 + 변형 케이스)
│   ├── train_colab.ipynb     # KoBERT fine-tune Colab 노트북
│   ├── sequences.jsonl       # 21 테스트 케이스
│   ├── judgments.jsonl       # Haiku 판정 결과
│   ├── v2_responses.jsonl    # v2 검증 결과
│   ├── v3_responses.jsonl    # v3 검증 결과 (변형 케이스 일반화 확인)
│   └── eval_21cases_results.{csv,jsonl}  # KoBERT v1 평가 결과
│
├── data/                     # 외부 데이터 (gitignore)
│   ├── raw/external/eoh9_gaslighting_v1/   # 한국어 가스라이팅 데이터 (분류기 폐기 후 미사용, 참고용)
│   │   ├── gaslighting_dialogues.csv
│   │   ├── chatbot_data.csv
│   │   └── README.md         # 출처 + 라이선스 메모
│   └── models/               # 비어있음 — BERT 분류기 v1/v3 폐기 (CHANGELOG Day 6 참고)
│
└── assets/                   # 이미지 + 음성
    ├── voice_preview_유란.mp3
    └── 1girl...*.png × 3     # NAI 베스트 이미지 (외형 reference)
```

## 기술 스택

- **LLM (배우)**: Anthropic Claude Sonnet 4.6 + Prompt Caching
- **LLM (감독, 호감도 판정)**: Claude Haiku 4.5 — 21 케이스 sign 90.5% / pattern 76.2%
- ~~**분류기**~~: BERT 분류기 시리즈 전부 폐기 (Day 6) — 도메인 mismatch + 단일 메시지 한계. 자체 LLM은 Phase 4+ 예정
- **TTS**: ElevenLabs v3 (Voice Design 커스텀 보이스)
- **DB**: PostgreSQL + SQLModel
- **프로토타입 UI**: Streamlit
- **실서비스 (예정)**: FastAPI 백엔드 + Flutter/RN 모바일 + FCM

## 기술적 의사결정

- **Claude Sonnet 4.6 + Prompt Caching** — 한국어 캐릭터 톤이 가장 자연스럽고, 시스템 프롬프트 캐싱으로 메시지당 비용 90% 절감
- **ElevenLabs v3 Voice Design** — v2보다 한국어 운율 자연스러움. 성우 외주 없이 커스텀 보이스 생성
- **PostgreSQL + SQLModel** — production-grade. 향후 RAG용 pgvector 확장 가능
- **호감도 = 가드레일 대체** — 하드 거절 대신 호감도/게임오버 메커니즘으로 자연스럽게 행동 유도
- **배우/감독 LLM 분리** — 단일 LLM이 응답 + 호감도 판정 동시에 하면 sycophancy로 가스라이팅 가스라이팅 취약 (실측: 미묘한 조작 4/6 굴복). 분리 + 감독 비대칭 평가 rubric으로 해결
- **BERT 분류기 폐기 (Day 6)** — v1 KoBERT, v3 Cascade 둘 다 실 사용에서 false positive 폭증 (일상 인사 "안녕 좋은 아침" → 조작 prob 1.000). 도메인 mismatch (학습 데이터 = 가스라이팅 댓글 + 감정 대화 ≠ 1:1 친밀 카톡) + 단일 메시지 패턴 매칭 한계. 자세한 분석 [CHANGELOG.md Day 6](CHANGELOG.md) 참고
- **Haiku LLM 단독** — 컨텍스트 인식 + 의도 추론. 21 케이스 sign 90.5% 검증. 비용 메시지당 ~1.4원. Phase 0~3 운영 부담 미미
- **자체 LLM은 Phase 4+** — GPU 서버 + 도메인 데이터 누적 후 한국어 7~10B 모델 (EXAONE/Kanana/Llama Korean) Ollama/vLLM 호스팅

## 설치 & 실행

### 1. 의존성

```powershell
python -m pip install -r requirements.txt
```

### 2. PostgreSQL

```sql
CREATE DATABASE yuran;
```

### 3. API 키 + `.env`

루트에 `.env` 생성:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=...
DATABASE_URL=postgresql://postgres:비밀번호@localhost:5432/yuran
```

### 4. 실행

```powershell
python -m streamlit run app/app.py
```

http://localhost:8501 자동 오픈. 사이드바에서 사용자 이름 입력 후 대화 시작.

## 게임 시스템 (설계)

상세는 [docs/system_design.md](docs/system_design.md). 핵심만:

- **상태 머신**: 프롤로그 → Free Chat ⇄ 이벤트 (엔딩 없음)
- **호감도** (0~100): 매 메시지 감독 LLM이 판정. 머리의 꽃으로 시각화 (숫자 게이지 X)
- **배우/감독 분리**: 배우(Sonnet)는 캐릭터 연기만, 감독(Haiku 단독)이 호감도 판정 — 가스라이팅에 sycophancy 방지
- **게임오버**: 호감도 0 → 메모리 완전 삭제 → 처음부터
- **이벤트**: 조건 충족 시 알림 → 사용자가 눌러서 활성화. 호감도 밴드별 분기
- **자유 텍스트 입력**: 선택지 X. LLM이 즉각 반응 = AI-native 비주얼노벨

## 검증 결과 (2026-05-29 prototype)

### 시스템 프롬프트 v1 → v2 → v3 → v4
- **v1 한계**: 부정 정서에 T스러운 응답, 미묘한 가스라이팅 4/6 굴복
- **v2 강화** (Few-shot + 가스라이팅 룰): 5/5 케이스 굴복 막음. **단점**: 외움 위험
- **v3** — INFP 페르소나 + 가드레일만 (Few-shot 제거). v3.1~v3.4 patches로 미세 조정
- **v4 (현재 사용)** — 시그니처 모먼트 / 가드레일 응답 예시 / 매력 예시 **전부 제거**:
  - **외움 트리거 제거** — v3의 박혀있던 표현 ("내 마지막 꽃이 너를 알았어" 등) 다 제거. INFP 페르소나로 매번 새 표현
  - **가짜 기억 금지 룰 추가** — history에 없는 공유 경험 만들어내지 X (예: "어제 라면 얘기" 등)
  - **첫 만남 처리 룰 추가** (v4.1) — 프롤로그 외에는 이미 만난 상태 가정
  - **시니컬/냉소/체념 톤 금지** (v4.2) — INFP는 그리움/슬픔으로

### 감독 LLM (Haiku 4.5) 호감도 판정
- 21 케이스 sign 정확도 **90.5%** / pattern **76.2%**
- 배우가 굴복한 케이스도 감독은 잡음 (분리 설계 정당화)

### BERT 분류기 시리즈 — 폐기 (Day 6)

두 차례 시도 모두 도메인 mismatch + 단일 메시지 한계로 실패:

- **v1 KoBERT (binary)**: KLUE/RoBERTa-base + eoh9 + ChatbotData. test 81%, 실 사용 시 일상 인사를 조작 prob 0.998로 잘못 잡음
- **v3 Cascade (4-class)**: + KorEmpathetic + NLPBada + gf-persona. test acc 0.91, OOD 0.71. 실 사용 시 "안녕 좋은 아침" prob 1.000 false positive

**근본 원인**:
1. 학습 데이터 도메인 (가스라이팅 + 일반 감정) ≠ 우리 task (1:1 친밀 카톡 + 게임 컨텍스트)
2. BERT = 단일 메시지 패턴 매칭. 컨텍스트/의도 추론 못 함
3. 우리 도메인 데이터 0 (Phase 0) → fine-tune 불가

**현재 production**: Haiku LLM 단독 (맥락 인식, sign 90.5% 검증). 자체 LLM은 Phase 4+ (GPU + 도메인 데이터 확보 후) — 자세한 분석 [CHANGELOG.md Day 6](CHANGELOG.md) 참고

## 로드맵

### 프로토타입 (Streamlit) - 현재
- [x] 채팅 + 음성 + DB 영속화
- [x] 시스템 프롬프트 v1 → v4 (외움 트리거 + 가짜기억 + 첫만남 처리)
- [x] 감독 LLM (Haiku) 검증 + BERT 분류기 시리즈 시도/폐기 (Day 6)
- [ ] `core/` 리팩토링 (UI/로직 분리)
- [ ] 게임 엔진 (프롤로그/호감도/이벤트/게임오버)
- [ ] 일러스트 통합 (호감도 밴드별 + 꽃 인디케이터)
- [ ] 프롤로그 + 스타터 이벤트 스토리

### 실서비스 (모바일) - 검증 후
- [ ] `core/` → FastAPI 백엔드
- [ ] Flutter/RN 모바일 앱
- [ ] FCM 푸시 + 구독/결제
