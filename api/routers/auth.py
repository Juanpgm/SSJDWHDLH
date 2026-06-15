from fastapi import APIRouter, Depends

from api.dependencies.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    return {"user": current_user.to_dict()}
