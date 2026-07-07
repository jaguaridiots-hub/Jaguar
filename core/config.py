import json


class Config:

    def __init__(self):

        with open("config/settings.json") as f:

            self.data = json.load(f)

    def get(self, key, default=None):

        return self.data.get(key, default)


config = Config()
