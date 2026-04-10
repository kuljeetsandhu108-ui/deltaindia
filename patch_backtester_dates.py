import os, re
os.system('docker cp app-backend-1:/app/app/backtester.py ./backtester.py')
with open('./backtester.py', 'r') as f: b = f.read()

b = b.replace('"total_return_pct": round(((balance - 1000)/1000)*100, 2),', 
              '"total_return_pct": round(((balance - 1000)/1000)*100, 2),\n                    "start_date": str(df.iloc[0]["timestamp"]),\n                    "end_date": str(df.iloc[-1]["timestamp"]),')
with open('./backtester.py', 'w') as f: f.write(b)
os.system('docker cp ./backtester.py app-backend-1:/app/app/backtester.py')
