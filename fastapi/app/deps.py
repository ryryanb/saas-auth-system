from fastapi import Depends, HTTPException
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
import jwt
import os
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Your User model (SQLAlchemy ORM model)
from app.models import UserDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
JWT_SECRET = os.getenv("JWT_SECRET")

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



async def get_or_create_user_from_google(session: AsyncSession, google_user_info: dict):

    #google_user_info = await resp.json()  # ⬅️ this unpacks the JSON body

    email = google_user_info["email"]
    name = google_user_info.get("name", "")
    profile_picture = google_user_info.get("picture", "")

    # 1. Check if the user already exists
    result = await session.execute(select(UserDB).where(UserDB.email == email))
    user = result.scalar_one_or_none()

    if user:
        # User exists, return it
        return user

    # 2. User does not exist, create a new one
    new_user = UserDB(
        email=email,
        name=name,
        profile_picture=profile_picture,
        is_active=True,     # or whatever fields you have
        is_google_account=True  # maybe a flag if you need
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user

