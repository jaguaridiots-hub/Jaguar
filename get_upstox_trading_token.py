import requests

client_id = "d4c5cedf-fbc5-415c-9194-974316edda38"
client_secret = "mnrheumzxm"
redirect_uri = "http://localhost:8080"
code = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1WkM1OEIiLCJqdGkiOiI2YTYwYzg3NzhkOTYyYzExOGE5Mjc2ODMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc4NDcyNzY3MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzg0NzU3NjAwfQ.phTzzO42f5fgB9lJA8SL2DToeUesTOJY89EpRSR1eHY"

url = "https://api.upstox.com/v2/login/authorization/token"
data = {
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

resp = requests.post(url, data=data, headers=headers)
print(resp.json())
