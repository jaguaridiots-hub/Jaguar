from datetime import datetime


class EventBus:

    def __init__(self):
        self.events = []

    def publish(self, event, payload=None):

        item = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "event": event,
            "payload": payload
        }

        self.events.append(item)

        print(
            f"[{item['time']}] "
            f"{item['event']}"
        )

    def history(self):
        return self.events

    def clear(self):
        self.events.clear()

    def last(self):
        if self.events:
            return self.events[-1]
        return None
