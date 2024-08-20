from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.schemas.user import TokenData


def get_current_user_optional(access_token: str, db: Session) -> Optional[User]:
    if access_token is None:
        return None

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = verify_access_token(access_token, credentials_exception)
    user = db.query(User).filter(User.id == token.id).first()
    if not user:
        raise credentials_exception

    user.update_last_login()
    return user


def verify_access_token(access_token: str, credentials_exception):
    """Funtcion to decode and verify access token"""

    try:
        payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type == "refresh":
            raise HTTPException(detail="Refresh token not allowed", status_code=400)

        token_data = TokenData(id=user_id)

    except JWTError as err:
        print(err)
        raise credentials_exception

    return token_data
