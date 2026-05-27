from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Subscription, UserPreference
from src.api.schemas import UserCreate, UserLogin, UserResponse, Token
from src.utils.auth import verify_password, get_password_hash, create_access_token
from datetime import datetime
import os

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default subscription (free tier)
    subscription = Subscription(
        user_id=new_user.id,
        plan="free",
        status="active",
        current_period_start=datetime.utcnow(),
    )
    db.add(subscription)

    # Create default preferences
    preferences = UserPreference(
        user_id=new_user.id,
        arxiv_categories=["cs.AI", "cs.LG"],
        keywords=["machine learning", "deep learning"],
    )
    db.add(preferences)

    db.commit()

    # Create user data directory
    user_data_dir = f"/data/users/{new_user.id}"
    os.makedirs(f"{user_data_dir}/papers", exist_ok=True)
    os.makedirs(f"{user_data_dir}/summaries", exist_ok=True)
    os.makedirs(f"{user_data_dir}/analyses", exist_ok=True)
    os.makedirs(f"{user_data_dir}/experiments", exist_ok=True)

    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token."""
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create access token
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Successfully logged out"}
