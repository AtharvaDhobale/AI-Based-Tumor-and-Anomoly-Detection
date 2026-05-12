from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import models


def ensure_admin(db: Session, email: str, password: str, full_name: str = "Admin Doctor") -> models.User:
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return existing
    user = models.User(email=email, full_name=full_name, hashed_password=hash_password(password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

