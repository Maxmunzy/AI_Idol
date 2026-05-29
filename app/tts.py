"""
TTS (ElevenLabs v3) — 음성 합성 관련 전부

- VoiceSettings 튜닝
- 텍스트 전처리 (괄호 stage direction 제거, 시작/끝 padding 등)
- ElevenLabs client + 음성 생성
"""

import os
import re

from elevenlabs import ElevenLabs, VoiceSettings


TTS_MODEL = "eleven_v3"

VOICE_SETTINGS = VoiceSettings(
    stability=0.75,
    similarity_boost=0.85,
    style=0.15,
    use_speaker_boost=True,
    speed=0.85,
)


def get_elevenlabs_client() -> ElevenLabs:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY 누락 - .env 확인")
    return ElevenLabs(api_key=api_key)


def preprocess_for_tts(text: str) -> str:
    """TTS용 텍스트 전처리.

    - 괄호 안 stage direction 제거: "(작게) 안녕" → " 안녕"
    - 시작 "..." → 머뭇거림 padding ("...... ... ")
    - 시작/끝 짧림 방지 padding 추가
    """
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


def generate_speech(client: ElevenLabs, voice_id: str, text: str) -> bytes:
    """텍스트를 음성으로 변환. 빈 결과는 b"" 반환."""
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
