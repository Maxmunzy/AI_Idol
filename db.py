"""
DB 레이어 - SQLModel + PostgreSQL.

유저별 대화 영속화 + 향후 RAG 메모리 확장 대비.
모델: User, Message (현재 사용) / Memory (v2 RAG용 스키마만 정의)
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL이 .env에 설정되지 않음")


engine = create_engine(DATABASE_URL, echo=False)


class User(SQLModel, table=True):
    """사용자 (유란이 기억하는 대상)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    """대화 메시지 (user / assistant)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: str
    content: str
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Memory(SQLModel, table=True):
    """장기 메모리 - v2 RAG용. v1에선 스키마만 미리 정의.

    예: "사용자는 라면 좋아함", "사용자 이름 = 태수", "어제 시험 봤다고 함"
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    fact: str
    importance: int = Field(default=3)
    source_message_id: Optional[int] = Field(default=None, foreign_key="message.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


def init_db() -> None:
    """앱 시작 시 1회 호출. 테이블 없으면 생성."""
    SQLModel.metadata.create_all(engine)


def get_or_create_user(name: str) -> User:
    """이름으로 유저 조회, 없으면 생성. last_seen 갱신."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.name == name)).first()
        if user is None:
            user = User(name=name)
            session.add(user)
        else:
            user.last_seen = datetime.utcnow()
            session.add(user)
        session.commit()
        session.refresh(user)
        return user


def save_message(
    user_id: int,
    role: str,
    content: str,
    audio_path: Optional[str] = None,
) -> Message:
    """메시지 1건 저장."""
    with Session(engine) as session:
        msg = Message(
            user_id=user_id,
            role=role,
            content=content,
            audio_path=audio_path,
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg


def load_messages(user_id: int, limit: int = 60) -> list[Message]:
    """최근 N개 메시지를 시간순(오래된 → 최신)으로 반환."""
    with Session(engine) as session:
        result = session.exec(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).all()
        return list(reversed(result))


def clear_messages(user_id: int) -> int:
    """유저 메시지 전체 삭제. 반환값: 삭제된 개수."""
    with Session(engine) as session:
        msgs = session.exec(
            select(Message).where(Message.user_id == user_id)
        ).all()
        count = len(msgs)
        for msg in msgs:
            session.delete(msg)
        session.commit()
        return count


def count_messages(user_id: int) -> int:
    """유저 누적 메시지 수 조회."""
    with Session(engine) as session:
        return len(
            session.exec(
                select(Message).where(Message.user_id == user_id)
            ).all()
        )
