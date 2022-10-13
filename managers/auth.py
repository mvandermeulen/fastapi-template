"""Define the Autorization Manager."""
from datetime import datetime, timedelta
from typing import Optional

import jwt
from decouple import config
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from db import database
from models import user
from models.enums import RoleType


class AuthManager:
    """Handle the JWT Auth."""

    @staticmethod
    def encode_token(user):
        """Create and return a JTW token."""
        try:
            payload = {
                "sub": user["id"],
                "exp": datetime.utcnow() + timedelta(minutes=120),
            }
            return jwt.encode(payload, config("SECRET_KEY"), algorithm="HS256")
        except Exception as ex:
            # log the exception
            raise ex


class CustomHTTPBearer(HTTPBearer):
    """Our own custom HTTPBearer class."""

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        res = await super().__call__(request)

        try:
            payload = jwt.decode(
                res.credentials, config("SECRET_KEY"), algorithms=["HS256"]
            )
            user_data = await database.fetch_one(
                user.select().where(user.c.id == payload["sub"])
            )
            request.state.user = user_data
            return user_data
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(401, "That token is Expired") from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(401, "That token is Invalid") from exc


oauth2_schema = CustomHTTPBearer()


def is_admin(request: Request):
    """Return true if the user is an Admin."""
    if request.state.user["role"] != RoleType.admin:
        raise HTTPException(403, "Forbidden")