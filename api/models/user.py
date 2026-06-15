from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    id: int
    firebase_uid: str
    email: str
    display_name: str | None
    photo_url: str | None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> "User":
        return cls(
            id=row[0],
            firebase_uid=row[1],
            email=row[2],
            display_name=row[3],
            photo_url=row[4],
            role=row[5],
            is_active=row[6],
            created_at=row[7],
            updated_at=row[8],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


ROLES = ["admin", "analyst", "viewer"]
