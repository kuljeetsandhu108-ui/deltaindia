
import sys
from app.database import SessionLocal
from app.models import Whitelist

def grant(email):
    db = SessionLocal()
    email = email.lower().strip()
    exists = db.query(Whitelist).filter(Whitelist.email == email).first()
    if exists:
        print(f"✅ {email} already has access.")
    else:
        new_user = Whitelist(email=email)
        db.add(new_user)
        db.commit()
        print(f"🚀 SUCCESS: Access granted to {email}!")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1: grant(sys.argv[1])
    else: print("Usage: python3 grant_access.py email@example.com")
