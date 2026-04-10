import os

print("🛡️ Injecting Auto-Pause Anti-Spam Protocol...")
os.system('docker cp app-backend-1:/app/app/engine.py ./engine.py')

with open('./engine.py', 'r') as f:
    e = f.read()

# 1. Smart Balance Fetcher (Checks both USDT and USD)
e = e.replace("return float(bal.get('USDT', {}).get('free', 0))", "return max(float(bal.get('USDT', {}).get('free', 0)), float(bal.get('USD', {}).get('free', 0)))")

# 2. Auto-Pause on 0 Balance
target_bal = 'crud.create_log(db, strat.id, f"❌ Insufficient Balance. Cannot execute.", "ERROR")\n                        continue'
repl_bal = 'crud.create_log(db, strat.id, f"❌ Insufficient Balance (Available: ${balance}). Auto-pausing strategy.", "ERROR")\n                        strat.is_running = False\n                        db.commit()\n                        continue'
e = e.replace(target_bal, repl_bal)

# 3. Block trades with a Quantity of 0 (e.g. trying to buy 10% of a $2 wallet)
target_qty = 'qty = round(trade_value / current_price, 4)\n\n                    crud.create_log(db, strat.id, f"🚀 ENTRY {side}'
repl_qty = 'qty = round(trade_value / current_price, 4)\n                    if qty <= 0:\n                        crud.create_log(db, strat.id, f"❌ Trade Qty is 0 (Balance too low). Auto-pausing.", "ERROR")\n                        strat.is_running = False\n                        db.commit()\n                        continue\n\n                    crud.create_log(db, strat.id, f"🚀 ENTRY {side}'
e = e.replace(target_qty, repl_qty)

# 4. Auto-Pause if the Exchange API explicitly rejects the order (Margin too low, etc.)
target_fail = 'flag_modified(strat, "logic_configuration")\n                        db.commit()'
repl_fail = 'flag_modified(strat, "logic_configuration")\n                        db.commit()\n                    else:\n                        strat.is_running = False\n                        db.commit()'
e = e.replace(target_fail, repl_fail)

with open('./engine.py', 'w') as f:
    f.write(e)

os.system('docker cp ./engine.py app-backend-1:/app/app/engine.py')
print("✅ Anti-Spam Protocol successfully injected!")
