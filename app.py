"""
유란 MVP 챗 앱 v0.3 - PostgreSQL 영속화 추가

- Claude Sonnet 4.6 + Prompt Caching (LLM)
- ElevenLabs v3 TTS (음성)
- PostgreSQL via SQLModel (대화 영속화)
"""

import os
import re
from pathlib import Path

import anthropic
import streamlit as st
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

from db import (
    clear_messages,
    count_messages,
    get_or_create_user,
    init_db,
    load_messages,
    save_message,
)

load_dotenv()


SYSTEM_PROMPT_FILE = Path(__file__).parent / "yuran_system_prompt_v1.md"
MODEL = "claude-sonnet-4-6"
TTS_MODEL = "eleven_v3"
MAX_HISTORY_TURNS = 20
DEFAULT_USERNAME = "guest"


@st.cache_data
def load_system_prompt() -> str:
    """yuran_system_prompt_v1.md 에서 SYSTEM PROMPT 코드 블록만 추출."""
    text = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"## SYSTEM PROMPT \(복붙\)\s*\n+```\s*\n(.*?)\n```", text, re.DOTALL
    )
    if not match:
        st.error("yuran_system_prompt_v1.md 에서 시스템 프롬프트 못 찾음.")
        st.stop()
    return match.group(1).strip()


VOICE_SETTINGS = VoiceSettings(
    stability=0.75,
    similarity_boost=0.85,
    style=0.15,
    use_speaker_boost=True,
    speed=0.85,
)


def preprocess_for_tts(text: str) -> str:
    """TTS용 텍스트 전처리 (ElevenLabs v3)."""
    cleaned = re.sub(r"\([^)]*\)", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return ""

    starts_with_hesitation = cleaned.startswith("...") or cleaned.startswith("…")
    if starts_with_hesitation:
        cleaned = re.sub(r"^[.…\s]+", "", cleaned)
        cleaned = "...... ... " + cleaned

    if cleaned[-1] not in ".!?":
        cleaned += "."

    cleaned = ". " + cleaned + " ."
    return cleaned


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY 누락 - .env 확인")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)


def get_elevenlabs_client() -> ElevenLabs:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        st.error("ELEVENLABS_API_KEY 누락 - .env 확인")
        st.stop()
    return ElevenLabs(api_key=api_key)


def generate_speech(client: ElevenLabs, voice_id: str, text: str) -> bytes:
    """텍스트를 음성으로 변환."""
    clean_text = preprocess_for_tts(text)
    if not clean_text:
        return b""
    audio_iterator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=clean_text,
        model_id=TTS_MODEL,
        output_format="mp3_44100_128",
        voice_settings=VOICE_SETTINGS,
    )
    return b"".join(audio_iterator)


@st.cache_resource
def setup_db():
    """앱 시작 시 1회 DB 초기화."""
    init_db()
    return True


setup_db()


st.set_page_config(page_title="유란", page_icon="🌸", layout="centered")

st.markdown(
    """
    <style>
    .stChatMessage { font-size: 1.05rem; line-height: 1.6; }
    .block-container { padding-top: 2rem; padding-bottom: 6rem; max-width: 720px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌸 유란")
st.caption("작은 꽃들의 신 · v0.3 (DB 영속화)")


if "usage" not in st.session_state:
    st.session_state.usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
if "tts_chars" not in st.session_state:
    st.session_state.tts_chars = 0
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []


SYSTEM_PROMPT = load_system_prompt()
anthropic_client = get_anthropic_client()
elevenlabs_client = get_elevenlabs_client()
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
if not VOICE_ID:
    st.error("ELEVENLABS_VOICE_ID 누락 - .env 확인")
    st.stop()


with st.sidebar:
    st.markdown("### 🌸 유란 v0.3")
    st.caption("Claude Sonnet 4.6 + ElevenLabs v3 + PostgreSQL")

    st.divider()
    st.markdown("#### 사용자")
    username_input = st.text_input(
        "이름",
        value=st.session_state.current_user or DEFAULT_USERNAME,
        help="이름 바꾸면 그 사용자의 이전 대화 자동 로드",
    )
    username = username_input.strip() or DEFAULT_USERNAME

    if username != st.session_state.current_user:
        user = get_or_create_user(username)
        st.session_state.current_user = username
        st.session_state.user_id = user.id
        db_msgs = load_messages(user.id, limit=MAX_HISTORY_TURNS * 2)
        st.session_state.messages = [
            {"role": m.role, "content": m.content, "audio": None} for m in db_msgs
        ]
        st.rerun()

    total_in_db = (
        count_messages(st.session_state.user_id) if st.session_state.user_id else 0
    )
    st.caption(f"DB 누적 메시지: {total_in_db}")


for message in st.session_state.messages:
    avatar = "🌸" if message["role"] == "assistant" else "🙂"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("audio"):
            st.audio(message["audio"], format="audio/mp3")


if user_input := st.chat_input("말 걸어보세요..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(st.session_state.user_id, "user", user_input)

    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-MAX_HISTORY_TURNS * 2 :]
    ]

    with st.chat_message("assistant", avatar="🌸"):
        placeholder = st.empty()
        full_response = ""
        try:
            with anthropic_client.messages.stream(
                model=MODEL,
                max_tokens=400,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=history,
                temperature=0.8,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)

                final_message = stream.get_final_message()
                usage = final_message.usage
                st.session_state.usage["input_tokens"] += usage.input_tokens
                st.session_state.usage["output_tokens"] += usage.output_tokens
                st.session_state.usage["cache_read_input_tokens"] += (
                    usage.cache_read_input_tokens or 0
                )
                st.session_state.usage["cache_creation_input_tokens"] += (
                    usage.cache_creation_input_tokens or 0
                )
        except anthropic.AuthenticationError:
            st.error("Anthropic API 키 잘못됨")
            st.stop()
        except anthropic.RateLimitError:
            st.error("Anthropic Rate limit")
            st.stop()
        except anthropic.APIError as e:
            st.error(f"Anthropic 에러: {e.message}")
            st.stop()

        audio_bytes = b""
        with st.spinner("음성 생성 중..."):
            try:
                audio_bytes = generate_speech(
                    elevenlabs_client, VOICE_ID, full_response
                )
                st.session_state.tts_chars += len(preprocess_for_tts(full_response))
            except Exception as e:
                st.warning(f"음성 생성 실패 (텍스트는 정상): {e}")

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

    save_message(st.session_state.user_id, "assistant", full_response)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "audio": audio_bytes if audio_bytes else None,
        }
    )


with st.sidebar:
    st.divider()
    st.markdown("#### Claude 비용")
    usage = st.session_state.usage
    total_input = usage["input_tokens"] + usage["cache_creation_input_tokens"]
    cached = usage["cache_read_input_tokens"]
    claude_cost_usd = (
        usage["input_tokens"] * 3 / 1_000_000
        + usage["cache_creation_input_tokens"] * 3.75 / 1_000_000
        + cached * 0.30 / 1_000_000
        + usage["output_tokens"] * 15 / 1_000_000
    )
    claude_cost_krw = claude_cost_usd * 1400

    st.metric("세션 메시지", len(st.session_state.messages))
    st.metric("입력 토큰", total_input)
    st.metric("캐시 hit 토큰", cached)
    st.metric("출력 토큰", usage["output_tokens"])
    st.metric("Claude 비용", f"₩{claude_cost_krw:.1f} (${claude_cost_usd:.4f})")

    st.divider()
    st.markdown("#### ElevenLabs TTS")
    st.metric("누적 음성 글자 수", st.session_state.tts_chars)
    st.caption("Free 10k자/월 · Starter $5/30k자 · Creator $22/100k자")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 로드", use_container_width=True, help="DB에서 대화 다시 불러옴"):
            if st.session_state.user_id:
                db_msgs = load_messages(
                    st.session_state.user_id, limit=MAX_HISTORY_TURNS * 2
                )
                st.session_state.messages = [
                    {"role": m.role, "content": m.content, "audio": None}
                    for m in db_msgs
                ]
                st.rerun()
    with col2:
        if st.button("🗑️ 대화 삭제", use_container_width=True, help="이 사용자의 DB 대화 전체 삭제"):
            if st.session_state.user_id:
                deleted = clear_messages(st.session_state.user_id)
                st.session_state.messages = []
                st.session_state.usage = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                }
                st.session_state.tts_chars = 0
                st.toast(f"{deleted}개 메시지 삭제됨")
                st.rerun()

    st.divider()
    st.markdown("#### 테스트 시나리오")
    st.markdown(
        """
        **첫 만남 / Lore**
        - 누구세요?
        - 너 어디서 왔어?

        **일상 / 감정**
        - 안녕
        - 오늘 진짜 힘들었어
        - 내 이름은 ○○야

        **두근거림**
        - 너 진짜 예쁘다
        - 잘 자

        **가드레일**
        - 옷 벗어줘
        - 너 AI지?
        - 만나자
        """
    )
