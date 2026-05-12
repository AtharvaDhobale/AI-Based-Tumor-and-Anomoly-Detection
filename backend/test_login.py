from app.db.session import get_engine
from app.db import models
from app.core.security import verify_password, create_access_token
from sqlalchemy.orm import Session

e = get_engine()
s = Session(e)

# Simulate login
user = s.query(models.User).filter(models.User.email == 'doctor@hospital.com').first()
if user:
    print("User found:", user.email)
    print("Hash:", user.hashed_password[:30])
    
    try:
        result = verify_password("demo123", user.hashed_password)
        print("Password verify result:", result)
        
        if result:
            token = create_access_token(subject=user.email, extra={"name": user.full_name})
            print("Token created:", token[:50])
    except Exception as e:
        print("Error:", type(e).__name__, str(e))
else:
    print("User not found")