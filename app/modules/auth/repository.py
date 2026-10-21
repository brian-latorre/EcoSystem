from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User


class UserRepository:
    def __init__(self, db: Session):
        self._db = db

    def find_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def find_by_credentials(self, email: str, password_hash: str) -> User | None:
        return self._db.scalar(
            select(User).where(
                User.email == email,
                User.password_hash == password_hash,
            )
        )

    def save(self, user: User) -> User:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
