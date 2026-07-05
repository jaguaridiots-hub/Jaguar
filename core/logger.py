from datetime import datetime

class JaguarLogger:

    @staticmethod
    def info(message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO  : {message}")

    @staticmethod
    def warning(message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARN  : {message}")

    @staticmethod
    def error(message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR : {message}")

    @staticmethod
    def success(message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS : {message}")
