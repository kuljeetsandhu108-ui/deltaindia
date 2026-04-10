import os

print("🛡️ Installing AlgoEase Gatekeeper Security...")

# --- A. Update Models to include the Whitelist ---
os.system('docker cp app-backend-1:/app/app/models.py ./models.py')
with open('./models.py', 'r') as f: m = f.read()

if 'class Whitelist' not in m:
    whitelist_model = """
class Whitelist(Base):
    __tablename__ = "whitelist"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)
"""
    m += whitelist_model
    with open('./models.py', 'w') as f: f.write(m)
    os.system('docker cp ./models.py app-backend-1:/app/app/models.py')

# --- B. Create the 'grant_access.py' Admin Tool ---
admin_tool = """
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
"""
with open('./grant_access.py', 'w') as f: f.write(admin_tool)
os.system('docker cp ./grant_access.py app-backend-1:/app/grant_access.py')

# --- C. Create the 'check_access' API Endpoint ---
os.system('docker cp app-backend-1:/app/main.py ./main.py')
with open('./main.py', 'r') as f: main_content = f.read()

access_endpoint = """
@app.get("/auth/check-access/{email}")
def check_access(email: str, db: Session = Depends(database.get_db)):
    from app.models import Whitelist
    user = db.query(Whitelist).filter(Whitelist.email == email.lower()).first()
    return {"authorized": True if user else False}
"""
if '/auth/check-access' not in main_content:
    main_content += access_endpoint
    with open('./main.py', 'w') as f: f.write(main_content)
    os.system('docker cp ./main.py app-backend-1:/app/main.py')

print("✅ Backend Security Wall Installed!")
