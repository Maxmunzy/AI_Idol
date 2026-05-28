# 유란 (柔蘭) - AI 가상 아이돌 게임

자유 텍스트로 대화하는 1:1 관계 시뮬레이션. 짧은 프롤로그로 만나고, 호감도를 쌓으며 이벤트로 관계가 깊어진다. 함부로 대하면 그녀는 떠난다 (영구).

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

전체 게임 설계는 **[system_design.md](system_design.md)** 참고.

## 기술 스택

- **LLM**: Anthropic Claude Sonnet 4.6 (Prompt Caching)
- **TTS**: ElevenLabs v3 (Voice Design 커스텀 보이스)
- **DB**: PostgreSQL + SQLModel
- **프로토타입 UI**: Streamlit
- **실서비스 (예정)**: FastAPI 백엔드 + Flutter/RN 모바일 + FCM

## 기술적 의사결정

- **Claude Sonnet 4.6 + Prompt Caching** — 한국어 캐릭터 톤이 가장 자연스럽고, 시스템 프롬프트(~3.5K토큰) 캐싱으로 메시지당 비용 90% 절감
- **ElevenLabs v3 Voice Design** — v2보다 한국어 운율 자연스러움. 성우 외주 없이 커스텀 보이스 생성
- **PostgreSQL + SQLModel** — SQLite 대신 production-grade. 향후 RAG용 pgvector 확장 가능. SQLModel은 type-safe 모던 ORM
- **로직/UI 분리 (`core/`)** — 게임 로직을 프론트 무관 모듈로. Streamlit → FastAPI/모바일 전환 시 재작성 없이 재사용
- **호감도 = 가드레일 대체** — 하드 거절("그건 안 됩니다") 대신 호감도/게임오버 메커니즘으로 자연스럽게 행동 유도
- **자유 텍스트 입력** — 선택지 대신 LLM 즉각 반응. 기존 미연시가 못 한 AI-native 비주얼노벨
- **모바일 우선** — FCM 푸시로 "24시간 함께" 가치 극대화 (유란이 먼저 연락)

## 설치 & 실행

### 1. 의존성

```powershell
python -m pip install -r requirements.txt
```

### 2. PostgreSQL

PostgreSQL 설치 후 DB 생성:

```sql
CREATE DATABASE yuran;
```

### 3. API 키 발급

- **Anthropic**: [console.anthropic.com](https://console.anthropic.com) → API Keys
- **ElevenLabs**: [elevenlabs.io](https://elevenlabs.io) → Voice Design으로 보이스 생성 → API Keys (Text to Speech 권한) + Voice ID 복사

### 4. `.env` 생성

```
ANTHROPIC_API_KEY=sk-ant-api03-...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=...
DATABASE_URL=postgresql://postgres:비밀번호@localhost:5432/yuran
```

### 5. 실행

```powershell
python -m streamlit run app.py
```

http://localhost:8501 자동 오픈. 사이드바에서 사용자 이름 입력 후 대화 시작.

## 게임 시스템 (설계)

상세는 [system_design.md](system_design.md). 핵심만:

- **상태 머신**: 프롤로그 → Free Chat ⇄ 이벤트 (엔딩 없음)
- **호감도** (0~100): 매 메시지 LLM이 판정. 머리의 꽃으로 시각화 (숫자 게이지 X)
- **게임오버**: 호감도 0 → 메모리 완전 삭제 → 처음부터 (유란 기억 못 함). 하드 가드레일 대신 이 메커니즘으로 행동 유도
- **이벤트**: 조건 충족 시 알림 → 사용자가 눌러서 활성화. 호감도 밴드별 스토리 분기
- **자유 텍스트 입력**: 선택지 X. LLM이 즉각 반응 = AI-native 비주얼노벨

## 아키텍처 원칙

`core/` Python 로직 = 프론트 무관 → 미래 FastAPI 백엔드로 그대로 재사용.
**Streamlit만 throwaway**, 나머지 로직은 모바일 전환 시 전부 재사용.

## 파일 구조

```
artist_AI/
├── app.py                          # Streamlit 챗 앱 (프로토타입 UI)
├── db.py                           # SQLModel 모델 + DB 헬퍼
├── requirements.txt
├── .env                            # API 키 + DB URL (gitignore됨)
│
├── system_design.md                # ★ 전체 게임 시스템 설계
├── yuran_character_sheet.md        # 캐릭터 시트 (lore/톤/외형)
├── yuran_signature_dialogues.md    # 시그니처 대사 30개
├── yuran_system_prompt_v1.md       # LLM 시스템 프롬프트 (app.py 자동 로드)
├── yuran_visual_prompts.md         # 미드저니 비주얼 프롬프트
├── yuran_visual_prompts_novelai.md # NAI 비주얼 프롬프트
│
├── voice_preview_유란.mp3            # ElevenLabs 보이스 샘플
└── 1girl...*.png (3개)             # NAI 베스트 이미지 (외형 reference)
```

## 개발 과정

- **v0.1** 캐릭터 시스템 + 시스템 프롬프트 (Claude Sonnet 4.6)
- **v0.2** 음성 통합 (ElevenLabs v3 커스텀 보이스)
- **v0.3** PostgreSQL 영속화 (SQLModel, 멀티유저)
- **설계** 게임 시스템 전환 — 미연시 하이브리드 (→ [system_design.md](system_design.md))

(상세 이력은 git log)

## 로드맵

### 프로토타입 (Streamlit) - 현재
- [x] 채팅 + 음성 + DB 영속화
- [ ] `core/` 리팩토링 (UI/로직 분리)
- [ ] 게임 엔진 (프롤로그/호감도/이벤트/게임오버)
- [ ] 일러스트 통합 (호감도 밴드별 + 꽃 인디케이터)
- [ ] 프롤로그 + 스타터 이벤트 스토리

### 실서비스 (모바일) - 검증 후
- [ ] `core/` → FastAPI 백엔드
- [ ] Flutter/RN 모바일 앱
- [ ] FCM 푸시 + 구독/결제

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| `ModuleNotFoundError` | `python -m pip install ...` / `python -m streamlit run app.py` (환경 통일) |
| `AuthenticationError` | `.env` 키 확인 (Anthropic `sk-ant-`, ElevenLabs `sk_`) |
| DB `connection failed` | `DATABASE_URL` 비밀번호 + PostgreSQL 서비스 Running 확인 |
| 음성 생성 실패 | ElevenLabs API 키 권한 (Text to Speech) + 무료 한도 확인 |
| 자동 재생 안 됨 | 브라우저 자동재생 정책 - 한 번 클릭하면 이후 자동 |
