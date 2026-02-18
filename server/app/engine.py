import asyncio
import ccxt.async_support as ccxt
from sqlalchemy.orm import Session
from . import models, crud, database, security

class TradingEngine:
    def __init__(self):
        self.is_running = False
        # Public instance for fetching prices
        self.public_exchange = ccxt.delta() 

    async def fetch_price(self, symbol):
        try:
            ticker = await self.public_exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            print(f"Error fetching price: {e}")
            return 0.0

    async def evaluate_strategies(self, db: Session):
        strategies = db.query(models.Strategy).filter(models.Strategy.is_running == True).all()
        
        if not strategies:
            print("--- No active strategies ---")
            return

        print(f"--- Processing {len(strategies)} Strategies ---")

        for strat in strategies:
            # 1. Get Price
            current_price = await self.fetch_price(strat.symbol)
            print(f"Strategy: {strat.name} | {strat.symbol}: ")

            # 2. TRIGGER LIVE TRADE
            # For testing, we are forcing a BUY.
            await self.execute_live_trade(db, strat, "BUY", current_price)

    async def execute_live_trade(self, db, strategy, side, price):
        user = strategy.owner
        
        # 2. Decrypt keys
        if not user.delta_api_key or not user.delta_api_secret:
            print(f"❌ [SKIPPING] No API Keys for {user.email}")
            return

        try:
            api_key = security.decrypt_value(user.delta_api_key)
            secret = security.decrypt_value(user.delta_api_secret)
        except Exception as e:
            print(f"❌ Decryption Failed: {e}")
            return

        print(f"🔐 Authenticating for {user.email}...")

        # 3. Initialize Exchange with TIME SYNC FIX
        user_exchange = ccxt.delta({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': { 
                'defaultType': 'future',
                'adjustForTimeDifference': True,  # <--- THE FIX
                'recvWindow': 10000              # Allow 10s leeway
            } 
        })

        try:
            # 4. PLACE THE ORDER (Safety: 1 Contract)
            amount = 1 
            print(f"🚀 SENDING LIVE {side} ORDER: {amount} contracts of {strategy.symbol}")
            
            # Load markets first to ensure sync
            await user_exchange.load_markets()
            
            order = await user_exchange.create_order(
                symbol=strategy.symbol,
                type='market',
                side=side.lower(),
                amount=amount
            )
            
            print(f"✅ ORDER SUCCESS! ID: {order['id']}")
            
        except Exception as e:
            print(f"❌ ORDER FAILED: {e}")
        finally:
            await user_exchange.close()

    async def start(self):
        self.is_running = True
        print("✅ LIVE TRADING ENGINE STARTED (With Time Sync)")
        
        while self.is_running:
            db = database.SessionLocal()
            try:
                await self.evaluate_strategies(db)
            finally:
                db.close()
            
            # Wait 15 seconds
            await asyncio.sleep(15)

engine = TradingEngine()
