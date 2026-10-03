# paper_trading.py
import json
import os
from datetime import datetime

LEDGER_FILE = "paper_trading.json"

def load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "balance": 100000.0,
            "positions": [],
            "history": [],
            "total_trades": 0,
            "wins": 0,
            "losses": 0
        }

def save_ledger(ledger):
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2)

def add_trade(symbol, side, entry, quantity, stop, tp, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    ledger = load_ledger()
    position = {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "quantity": quantity,
        "stop": stop,
        "tp": tp,
        "entry_time": timestamp,
        "status": "OPEN",
        "exit": None,
        "exit_time": None,
        "pnl": 0.0
    }
    ledger["positions"].append(position)
    ledger["total_trades"] += 1
    save_ledger(ledger)
    return position

def close_position(symbol, exit_price, exit_time=None):
    if exit_time is None:
        exit_time = datetime.now().isoformat()
    ledger = load_ledger()
    for pos in ledger["positions"]:
        if pos["symbol"] == symbol and pos["status"] == "OPEN":
            pos["exit"] = exit_price
            pos["exit_time"] = exit_time
            pos["status"] = "CLOSED"
            if pos["side"] == "BUY":
                pnl = (exit_price - pos["entry"]) * pos["quantity"]
            else:
                pnl = (pos["entry"] - exit_price) * pos["quantity"]
            pos["pnl"] = pnl
            ledger["balance"] += pnl
            if pnl > 0:
                ledger["wins"] += 1
            else:
                ledger["losses"] += 1
            ledger["history"].append(pos)
            break
    save_ledger(ledger)
    return pos

def get_current_pnl(symbol, current_price):
    """Calculate unrealized P&L for open positions."""
    ledger = load_ledger()
    total_pnl = 0.0
    for pos in ledger["positions"]:
        if pos["symbol"] == symbol and pos["status"] == "OPEN":
            if pos["side"] == "BUY":
                pnl = (current_price - pos["entry"]) * pos["quantity"]
            else:
                pnl = (pos["entry"] - current_price) * pos["quantity"]
            total_pnl += pnl
    return total_pnl

def reset_ledger():
    if os.path.exists(LEDGER_FILE):
        os.remove(LEDGER_FILE)
    return load_ledger()
def get_open_trades():
    ledger = load_ledger()
    return [p for p in ledger["positions"] if p["status"] == "OPEN"]

def get_closed_trades():
    ledger = load_ledger()
    return [p for p in ledger["positions"] if p["status"] == "CLOSED"]
