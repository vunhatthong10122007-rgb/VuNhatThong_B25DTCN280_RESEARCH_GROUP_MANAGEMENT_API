from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    @staticmethod
    def register(db: Session, user_in: UserCreate) -> User:
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise ValueError("Email này đã được đăng ký.")

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def login(db: Session, user_login: UserLogin) -> Token:
        user = db.query(User).filter(User.email == user_login.email).first()
        if not user or not verify_password(user_login.password, user.password_hash):
            raise ValueError("Email hoặc mật khẩu không chính xác.")

        if not user.is_active:
            raise ValueError("Tài khoản hiện đang bị vô hiệu hóa.")

        access_token = create_access_token(subject=user.id, role=user.role.value)
        return Token(access_token=access_token, token_type="bearer")
