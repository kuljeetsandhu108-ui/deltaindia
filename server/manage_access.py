import sys
from app.database import SessionLocal
from app.models import Whitelist
from datetime import datetime

MASTER_EMAIL = "kuljeetsandhu108@gmail.com"

def grant_single(email):
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

def grant_bulk(email_string):
    # This splits by commas, spaces, or newlines
    emails = email_string.replace(',', ' ').replace(';', ' ').split()
    count = 0
    db = SessionLocal()
    for email in emails:
        email = email.lower().strip()
        if not email: continue
        exists = db.query(Whitelist).filter(Whitelist.email == email).first()
        if not exists:
            db.add(Whitelist(email=email))
            count += 1
    db.commit()
    db.close()
    print(f"💥 BULK SUCCESS: Added {count} new users to the whitelist!")

def list_users():
    db = SessionLocal()
    users = db.query(Whitelist).all()
    print("\n========= 🔐 ALGOEASE AUTHORIZED USERS =========")
    for u in users:
        status = "⭐ MASTER" if u.email == MASTER_EMAIL else "👤 USER"
        print(f"{status} | Email: {u.email}")
    print(f"TOTAL: {len(users)} users")
    print("================================================\n")
    db.close()

def revoke_access(email):
    db = SessionLocal()
    email = email.lower().strip()
    if email == MASTER_EMAIL:
        print("❌ ERROR: Cannot revoke Master Admin.")
        return
    user = db.query(Whitelist).filter(Whitelist.email == email).first()
    if user:
        db.delete(user)
        db.commit()
        print(f"🚫 REVOKED: {email} is now blocked.")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  --list")
        print("  --grant [email]")
        print("  --bulk [email1,email2,email3]")
        print("  --revoke [email]")
    else:
        cmd = sys.argv[1]
        if cmd == "--list": list_users()
        elif cmd == "--grant": grant_single(sys.argv[2])
        elif cmd == "--bulk": grant_bulk(sys.argv[2])
        elif cmd == "--revoke": revoke_access(sys.argv[2])
