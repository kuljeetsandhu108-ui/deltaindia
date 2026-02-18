import asyncio
import json
import websockets
import ccxt.async_support as ccxt
from sqlalchemy.orm import Session
from . import models, database, security, crud

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        # 🇮🇳 INDIA SPECIFIC WEBSOCKET URL
        self.delta_ws_url = "wss://socket.india.delta.exchange"

    async def get_active_symbols(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        return symbols if symbols else ["BTCUSD"]

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True,
            models.Strategy.symbol == symbol
        ).all()

        for strat in strategies:
            # OPTIONAL: Log every tick (Can be noisy, uncomment if needed)
            # crud.create_log(db, strat.id, f"Checking: {symbol} @ {current_price}", "INFO")
            
            user = strat.owner
            if not user.delta_api_key: continue

            logic = strat.logic_configuration
            qty = logic.get('quantity', 1)
            sl_pct = logic.get('sl', 0)
            tp_pct = logic.get('tp', 0)
            
            params = {}
            if sl_pct > 0: params['stop_loss_price'] = current_price * (1 - (sl_pct / 100))
            if tp_pct > 0: params['take_profit_price'] = current_price * (1 + (tp_pct / 100))

            exchange = None
            try:
                api_key = security.decrypt_value(user.delta_api_key)
                secret = security.decrypt_value(user.delta_api_secret)
                
                # 🇮🇳 INDIA SPECIFIC CONFIGURATION
                exchange = ccxt.delta({
                    'apiKey': api_key,
                    'secret': secret,
                    'options': { 'defaultType': 'future', 'adjustForTimeDifference': True },
                    'urls': {
                        'api': {
                            'public': 'https://api.india.delta.exchange',
                            'private': 'https://api.india.delta.exchange',
                        },
                        'www': 'https://india.delta.exchange',
                    }
                })
                
                crud.create_log(db, strat.id, f"🚀 Firing Order: Buy {qty} {symbol}", "INFO")
                
                # Execute Market Order
                await exchange.create_order(symbol, 'market', 'buy', qty, params=params)
                
                crud.create_log(db, strat.id, f"✅ India Order Filled!", "SUCCESS")

            except Exception as e:
                msg = str(e)
                if "invalid_api_key" in msg:
                    crud.create_log(db, strat.id, "❌ Auth Failed: Check India Keys", "ERROR")
                elif "insufficient_balance" in msg:
                    crud.create_log(db, strat.id, "❌ Failed: No Money in Wallet", "ERROR")
                else:
                    crud.create_log(db, strat.id, f"❌ Trade Failed: {msg[:50]}...", "ERROR")
            finally:
                if exchange: await exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ INDIA TRADING ENGINE STARTED")

        while self.is_running:
            try:
                # 🇮🇳 Connecting to India Socket
                async with websockets.connect(self.delta_ws_url) as websocket:
                    print("🔗 Connected to Delta India WebSocket")
                    db = database.SessionLocal()
                    symbols = await self.get_active_symbols(db)
                    db.close()
                    
                    payload = { "type": "subscribe", "payload": { "channels": [{ "name": "v2/ticker", "symbols": symbols }] } }
                    await websocket.send(json.dumps(payload))

                    async for message in websocket:
                        if not self.is_running: break
                        data = json.loads(message)
                        if data.get('type') == 'v2/ticker':
                            try:
                                symbol = data['symbol']
                                price = float(data['mark_price'])
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, symbol, price)
                                db_tick.close()
                            except: pass
            except Exception as e:
                print(f"WS Error: {e}")
                await asyncio.sleep(5)

engine = RealTimeEngine()
