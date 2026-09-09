"""Signup, login, and whoami."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth import create_token, current_user, hash_password, verify_password
from ..db import get_session
from ..models import User
from ..ratelimit import login_limit, signup_limit
from ..schemas import LoginIn, SignupIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response(user: User) -> TokenOut:
    return TokenOut(
        access_token=create_token(user.id),
        user=UserOut(
            id=user.id, name=user.name, email=user.email,
            lang=user.lang, created_at=user.created_at,
        ),
    )


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(signup_limit)])
def signup(body: SignupIn, session: Session = Depends(get_session)) -> TokenOut:
    email = body.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try logging in.",
        )
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        name=body.name,
        lang=body.lang,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _token_response(user)


# A real bcrypt hash of a value nobody can log in with. Verifying against it
# when the email is unknown keeps the response time the same as a wrong
# password, so the endpoint does not leak which emails are registered.
_DUMMY_HASH = hash_password("unusable-placeholder-for-timing-parity")


@router.post("/login", response_model=TokenOut,
             dependencies=[Depends(login_limit)])
def login(body: LoginIn, session: Session = Depends(get_session)) -> TokenOut:
    user = session.exec(select(User).where(User.email == body.email.lower())).first()
    valid = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut(
        id=user.id, name=user.name, email=user.email,
        lang=user.lang, created_at=user.created_at,
    )
