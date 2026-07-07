import json
import os

FILE = "trade_state.json"


def save(position):
    data = {
        "position": position.position,
        "entry": position.entry,
        "stop_loss": position.stop_loss,
        "take_profit": position.take_profit,
        "pnl": position.pnl,
    }

    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)


def load(position):
    if not os.path.exists(FILE):
        return False

    with open(FILE, "r") as f:
        data = json.load(f)

    position.position = data["position"]
    position.entry = data["entry"]
    position.stop_loss = data["stop_loss"]
    position.take_profit = data["take_profit"]
    position.pnl = data["pnl"]

    return True


def clear():
    if os.path.exists(FILE):
        os.remove(FILE)
