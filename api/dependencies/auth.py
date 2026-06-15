from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.core.firebase import verify_id_token
from api.models.user import User
from api.core.database import db_cursor

bearer_scheme = HTTPBearer(auto_error=False)


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any] | None:
    if credentials is None:
        return None
    try:
        return verify_id_token(credentials.credentials)
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    try:
        firebase_claims = verify_id_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        ) from exc

    firebase_uid = firebase_claims.get("uid", "")
    email = firebase_claims.get("email", "")
    display_name = firebase_claims.get("name", "")
    photo_url = firebase_claims.get("picture", "")

    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE firebase_uid = %s",
            (firebase_uid,),
        )
        row = cur.fetchone()

        if row is None:
            cur.execute(
                """
                INSERT INTO users (firebase_uid, email, display_name, photo_url, role)
                VALUES (%s, %s, %s, %s, 'analyst')
                RETURNING *
                """,
                (firebase_uid, email, display_name, photo_url),
            )
            row = cur.fetchone()
            return User.from_row(row)

        return User.from_row(row)


def require_role(role: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {role}",
            )
        return current_user
    return checker
