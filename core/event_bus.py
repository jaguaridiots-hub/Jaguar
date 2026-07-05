class EventBus:

    def __init__(self):
        self.listeners = {}

    def subscribe(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []

        self.listeners[event].append(callback)

    def publish(self, event, data=None):
        print(f"\n📢 Event : {event}")

        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(data)
