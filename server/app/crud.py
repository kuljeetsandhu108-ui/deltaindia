from sqlalchemy.orm import Session
from . import models, schemas, security
from datetime import datetime

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, full_name=user.full_name, picture=user.picture)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_broker_keys(db: Session, keys: schemas.BrokerKeys):
    user = get_user_by_email(db, keys.email)
    if not user: return None
    user.delta_api_key = security.encrypt_value(keys.api_key)
    user.delta_api_secret = security.encrypt_value(keys.api_secret)
    db.commit()
    return user

def create_strategy(db: Session, strategy: schemas.StrategyInput):
    user = get_user_by_email(db, strategy.email)
    if not user: return None
    db_strat = models.Strategy(
        name=strategy.name, symbol=strategy.symbol, broker="DELTA",
        logic_configuration=strategy.logic, is_running=True, owner_id=user.id
    )
    db.add(db_strat)
    db.commit()
    db.refresh(db_strat)
    # Log creation
    create_log(db, db_strat.id, f"Strategy Created: {strategy.name}", "INFO")
    return db_strat

# --- NEW LOGGING FUNCTION ---
def create_log(db: Session, strategy_id: int, message: str, level: str = "INFO"):
    # Keep log history small (delete old logs if > 100)
    # For MVP we just add.
    new_log = models.StrategyLog(strategy_id=strategy_id, message=message, level=level)
    db.add(new_log)
    db.commit()

def get_strategy_logs(db: Session, strategy_id: int):
    # Get last 50 logs, newest first
    return db.query(models.StrategyLog).filter(
        models.StrategyLog.strategy_id == strategy_id
    ).order_by(models.StrategyLog.timestamp.desc()).limit(50).all()
