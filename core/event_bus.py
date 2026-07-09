class EventBus:

    def __init__(self):
        self._events = []

    def publish(self, name, payload=None):

        self._events.append({

            "event": name,

            "payload": payload

        })

    def history(self):

        return self._events

    def clear(self):

        self._events.clear()
