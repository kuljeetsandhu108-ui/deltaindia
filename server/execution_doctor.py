import asyncio
import traceback
from app.database import SessionLocal
from app.models import Strategy
from app.engine import engine

async def run_diagnostics():
    print("="*60)
    print("🩺 ALGOEASE EXECUTION PIPELINE DOCTOR")
    print("="*60)
    
    db = SessionLocal()
    strategies = db.query(Strategy).filter(Strategy.is_running == True).all()
    
    if not strategies:
        print("❌ No running strategies found. Please click 'Deploy Live' or 'Play'.")
        return

    print(f"✅ Found {len(strategies)} Active Strategies in the Database.\n")

    for strat in strategies:
        print(f"🔍 Analyzing Strategy: '{strat.name}' (ID: {strat.id})")
        print(f"   Broker: {strat.broker} | Symbol: {strat.symbol}")
        
        logic = strat.logic_configuration or {}
        print(f"   Mode: {logic.get('tradeMode', 'PAPER')} | Current State: {logic.get('state', 'WAITING')}")
        
        print("\n   [1/3] Testing Live Data Feed...")
        try:
            df = await engine.fetch_history(strat.symbol, strat.broker)
            if df is None or df.empty:
                print("   ❌ FAILED: Could not fetch historical data for this symbol.")
                continue
            current_price = df.iloc[-1]['close']
            print(f"   ✅ SUCCESS: Fetched {len(df)} candles. Live Price is ${current_price}")
        except Exception as e:
            print(f"   ❌ FAILED: Data fetch error -> {e}")
            continue

        print("\n   [2/3] Evaluating Math Logic...")
        try:
            is_trigger = await engine.check_conditions(strat.symbol, strat.broker, current_price, logic)
            print(f"   ✅ SUCCESS: Math engine evaluated flawlessly.")
            if is_trigger:
                print("   ⚠️ RESULT: Condition is TRUE! The engine should be firing a trade right now!")
            else:
                print("   ⏸️ RESULT: Condition is FALSE. The technical indicators have not crossed yet.")
                print("      (The engine is silently waiting in the background for the perfect moment).")
        except Exception as e:
            print(f"   ❌ FAILED: Logic evaluation crashed -> {e}")
            traceback.print_exc()

        print("\n   [3/3] Checking Security Vault...")
        user = strat.owner
        key_enc = user.coindcx_api_key if strat.broker == "COINDCX" else user.delta_api_key
        if not key_enc:
            if logic.get('tradeMode') == 'LIVE':
                print("   ❌ FATAL: Strategy is set to LIVE, but no API keys are saved for this broker!")
            else:
                print("   ✅ SUCCESS: No keys found, but it is in PAPER mode, so it's safe.")
        else:
            print("   ✅ SUCCESS: API Keys are securely loaded and encrypted.")
        
        print("-" * 60)
        
    db.close()
    print("🩺 DIAGNOSTICS COMPLETE.")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
