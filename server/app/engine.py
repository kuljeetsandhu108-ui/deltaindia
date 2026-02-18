import asyncio
import json
import websockets
import ccxt.async_support as ccxt
from sqlalchemy.orm import Session
from . import models, database, security

class RealTimeEngine:
    def __init__(self):
        self.is_running = False
        self.delta_ws_url = "wss://socket.delta.exchange"
        self.active_symbols = set()

    async def get_active_symbols(self, db: Session):
        # Find all unique symbols that have running strategies
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        symbols = list(set([s.symbol for s in strategies]))
        # Default to BTCUSD if empty so the socket stays open
        return symbols if symbols else ["BTCUSD"]

    async def execute_trade(self, db: Session, symbol: str, current_price: float):
        # 1. Find strategies for this symbol
        strategies = db.query(models.Strategy).filter(
            models.Strategy.is_running == True,
            models.Strategy.symbol == symbol
        ).all()

        for strat in strategies:
            # 2. CHECK LOGIC (Instant Check)
            # For this MVP, we are still forcing a BUY for testing.
            # In Phase 2, we will put the 'If Price > EMA' logic here.
            print(f"⚡ [TICK] {symbol} @ {current_price} | Checking: {strat.name}")
            
            # --- EXECUTION ---
            user = strat.owner
            if not user.delta_api_key: continue

            try:
                # Decrypt keys
                api_key = security.decrypt_value(user.delta_api_key)
                secret = security.decrypt_value(user.delta_api_secret)
                
                # Auth & Trade
                exchange = ccxt.delta({
                    'apiKey': api_key,
                    'secret': secret,
                    'options': { 'defaultType': 'future', 'adjustForTimeDifference': True }
                })
                
                # SAFETY: 1 Contract Limit
                print(f"🚀 FIRING ORDER: {strat.name}")
                await exchange.create_order(symbol, 'market', 'buy', 1)
                await exchange.close()
                print("✅ ORDER SENT TO EXCHANGE")

            except Exception as e:
                print(f"❌ Execution Failed: {e}")

    async def start(self):
        self.is_running = True
        print("✅ REAL-TIME WEBSOCKET ENGINE STARTED")

        while self.is_running:
            try:
                # 1. Open Connection
                async with websockets.connect(self.delta_ws_url) as websocket:
                    print("🔗 Connected to Delta Exchange WebSocket")

                    # 2. Subscribe to Active Markets
                    db = database.SessionLocal()
                    symbols = await self.get_active_symbols(db)
                    db.close()
                    
                    # Delta Exchange Subscribe Message Format
                    payload = {
                        "type": "subscribe",
                        "payload": {
                            "channels": [
                                { "name": "v2/ticker", "symbols": symbols }
                            ]
                        }
                    }
                    await websocket.send(json.dumps(payload))
                    print(f"📡 Subscribed to: {symbols}")

                    # 3. Listen Loop
                    async for message in websocket:
                        if not self.is_running: break
                        
                        data = json.loads(message)
                        
                        # Handle Heartbeats (Keep-Alive)
                        if data.get('type') == 'enable_heartbeat':
                            continue

                        # Handle Price Updates
                        if data.get('type') == 'v2/ticker':
                            # Delta sends ticker updates here
                            # 'mark_price' or 'close'
                            try:
                                symbol = data['symbol']
                                price = float(data['mark_price'])
                                
                                # TRIGGER THE TRADES
                                db_tick = database.SessionLocal()
                                await self.execute_trade(db_tick, symbol, price)
                                db_tick.close()
                                
                            except:
                                pass # Ignore incomplete data packets

            except Exception as e:
                print(f"⚠️ WebSocket Error: {e}")
                print("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

engine = RealTimeEngine()
