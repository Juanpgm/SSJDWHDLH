import json

import firebase_admin
from firebase_admin import auth, credentials

from .config import settings

_firebase_app = None


def init_firebase() -> None:
    global _firebase_app
    if _firebase_app is not None:
        return

    if settings.firebase_service_account_json:
        cred_dict = json.loads(settings.firebase_service_account_json)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
    else:
        _firebase_app = firebase_admin.initialize_app()


def verify_id_token(token: str) -> dict:
    if _firebase_app is None:
        init_firebase()
    return auth.verify_id_token(token)
