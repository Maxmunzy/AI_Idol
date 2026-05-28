# Changelog

artist_AI 개발 이력.

---

## 2026-05-26 — Day 1 / v0.1: 캐릭터 + 챗 MVP

### Added
- 캐릭터 시트 v1.2 (`yuran_character_sheet.md`)
  - lore (평행세계 작은 꽃들의 신)
  - 톤 (조용함, 부드러움, 짧은 문장, 말줄임표)
  - "나 너 없으면 안돼" 의존성 정서 (트라우마 기반, dignity 유지)
  - 외형 spec (NAI 12회 검증 후 락)
  - 가드레일 (성적/만남/AI 정체/다른 캐릭터 흉내)
- 시그니처 대사 30개 (`yuran_signature_dialogues.md`) — 6 카테고리 (첫만남/일상/감정/의존성/플러팅/매력)
- 시스템 프롬프트 v1 (`yuran_system_prompt_v1.md`)
- NAI 비주얼 reference 3장 (외형 락 / 의상 미정 — 일러스트레이터 영역)
- Streamlit 챗 앱 (`app.py`) — Claude Sonnet 4.6 + Prompt Caching
- 사이드바 비용 모니터링 (실시간 토큰 + KRW 환산)

### 검증
- 12턴 자체 대화 → 시그니처 모먼트 정확히 트리거
- 가드레일 응답이 캐릭터 톤 유지 확인 (메타 발언 X)

### 의사결정
- Claude Sonnet 4.6 (한국어 캐릭터 톤 가장 강함)
- Prompt Caching (시스템 프롬프트 ~3.5K 토큰 → 메시지당 비용 90% 절감)
- Streamlit (빠른 프로토타입, throwaway 전제 — 실서비스는 모바일)

---

## 2026-05-26 — Day 1 / v0.2: 음성 통합

### Added
- ElevenLabs v3 커스텀 보이스 통합 (TTS)
- 음성 자동 재생 (`st.audio` autoplay)
- VoiceSettings 튜닝 (stability=0.75, similarity_boost=0.85, style=0.15, speed=0.85)
- 텍스트 전처리 (괄호 stage direction 제거, "..." 처리, 시작/끝 짤림 방지 padding)
- 사이드바 TTS 사용량 모니터링
- `elevenlabs` 의존성

### Changed
- 모델: `eleven_multilingual_v2` → `eleven_v3` (한국어 운율 자연스러움)

### 의사결정
- ElevenLabs Voice Design (성우 외주 없이 커스텀 보이스)
- v3 alpha 한계 수용 (시작 머뭇거림 약함, 한국어 도치문 톤 한계) → 향후 Supertone 검토

---

## 2026-05-27 — Day 2 / v0.3: PostgreSQL 영속화

### Added
- `db.py` — SQLModel ORM (User / Message / Memory 모델)
- 사이드바 "사용자 이름" 입력 → 사용자별 대화 자동 로드/저장
- 앱 재시작 후 이전 대화 복원
- `psycopg2-binary`, `sqlmodel` 의존성

### Changed
- `app.py` — DB 연동 + 멀티유저 지원
- 사이드바: DB 누적 메시지 수, "다시 로드" / "대화 삭제" 버튼

### 의사결정
- PostgreSQL (SQLite 대신 production-grade, 향후 pgvector 확장)
- SQLModel (Pydantic + SQLAlchemy 모던 ORM, type-safe)
- Memory 테이블 — v2 RAG용 스키마 미리 정의 (현재 미사용)

---

## 2026-05-28 — Day 3: 게임 시스템 설계 전환

방향 전환: 챗봇 → **AI 가상 아이돌 + 미연시 + 라이브서비스** 하이브리드.
"엔딩 없이 둘이서 무한히 이야기 만들어가는" 관계 게임.

### Added
- `system_design.md` 신규 — 전체 게임 시스템 설계 문서 (이후 §4.5 콘텐츠 파이프라인, §5.5 LLM 배우/감독 분리 추가)
- `illustrator_brief.md` 신규 — 일러스트레이터 외주용 1페이지 brief (자금 마련 후 즉시 투입 대비)
- `roadmap.md` 신규 — 3년 horizon 개인 로드맵 (Phase 0~5, 마인드셋용)
- README — "기술적 의사결정" / "개발 과정" 섹션 추가
- `CHANGELOG.md` 신규 (이 파일)

### Changed
- README — 챗봇 정체성 → 게임 정체성으로 갱신
- README — "현재 상태" 표 (구현됨 vs 설계만 명확히 구분)

### Removed (README)
- 옛 "톤 튜닝 50회 자체 대화" 워크플로우
- 옛 v0.1→v0.2 체크리스트 로드맵
- 장황한 비용 디테일 표

### 설계 결정 (system_design.md)
- 상태 머신: 프롤로그 → Free Chat ⇄ 이벤트 (엔딩 없음, 무한 반복)
- 호감도 (0~100, 시작 40, 머리 꽃으로 시각화)
- 게임오버 (호감도 0 → 메모리 완전 삭제, 차갑게 떠남)
- 이벤트 토글/알림 발동, 5종 트리거
- 호감도 밴드 5종 + 스토리 분기
- 모바일 우선 아키텍처 (core/ 로직 분리 → FastAPI → Flutter + FCM)
- UI 하이브리드 (캐릭터 상단 고정 + 채팅, 2모드 자동 전환)
- 자유 텍스트 입력 (선택지 X, LLM 즉각 반응 = AI-native VN)

### 설계 보강 (system_design.md §4.5, §5.5 추가)
- **LLM 배우/감독 분리** (§5.5) — 단일 LLM이 응답 + 호감도 판정 동시에 하면 sycophancy로 가스라이팅에 취약. 배우(Sonnet) / 감독(Haiku) 분리.
- **감독 평가 rubric** — 가스라이팅/네깅/가치폄하/죄책감/책임전가/농담reframe/점수조작 패턴 명시. 비대칭 평가 (긍정 신중, 부정 보수적).
- **진화 경로** — v1 Haiku 판정 → v2 KoBERT 파인튜닝 분류기. 분류 작업은 범용 LLM보다 파인튜닝이 빠르고 싸고 어뷰징에 강함.
- **콘텐츠 파이프라인** (§4.5) — 구독 게이팅 (무료 월 1개 + 유료 추가) + 이벤트별 일러스트 컬렉터블 + 시즌/절차적 이벤트로 솔로 founder 부담 분산.

### 의사결정
- 일러스트레이터 brief 사전 작성 — 자금 마련 후 즉시 외주 투입 가능하도록 머릿속에 있을 때 정리
- 감독 LLM 분리 비용 (+30%) 수용 — 게임오버 메커니즘 무력화되면 product 본질 실패하므로
