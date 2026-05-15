from datetime import datetime, timedelta

from jose import jwt


SECRET_KEY = "super_secret_ai_helper_key"
ALGORITHM = "HS256"


def create_access_token(user_data: dict):

    payload = user_data.copy()

    payload["exp"] = (
        datetime.utcnow() + timedelta(days=7)
    )

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token