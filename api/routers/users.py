from fastapi import APIRouter, Depends, HTTPException

from api.dependencies.auth import get_current_user, require_role
from api.core.database import db_cursor
from api.models.user import ROLES, User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def list_users(
    current_user: User = Depends(require_role("admin")),
) -> dict:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users ORDER BY email")
        users = [User.from_row(row).to_dict() for row in cur.fetchall()]
    return {"count": len(users), "users": users}


@router.put("/{user_id}/role")
def update_role(
    user_id: int,
    role: str,
    current_user: User = Depends(require_role("admin")),
) -> dict:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Rol invalido: {role}")

    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET role = %s, updated_at = NOW() WHERE id = %s RETURNING *",
            (role, user_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"user": User.from_row(row).to_dict()}
