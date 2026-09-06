def _get_instrument_token(self, symbol):
    if symbol in self.instrument_cache:
        return self.instrument_cache[symbol]

    mapping = {
        "GC=F": "GOLD",
        "SI=F": "SILVER",
        "RELIANCE.NS": "RELIANCE",
        "TCS.NS": "TCS",
        "HDFCBANK.NS": "HDFCBANK",
        "NIFTY": "NIFTY",
        "BANKNIFTY": "BANKNIFTY",
    }
    search_key = mapping.get(symbol, symbol)

    # Use the search API – returns JSON
    url = "https://api.upstox.com/v2/instruments/search"
    params = {"q": search_key}
    headers = {"Authorization": f"Bearer {self.access_token}"}
    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        raise Exception(f"Search API failed: {resp.status_code} - {resp.text[:200]}")

    data = resp.json()
    # The response structure: {"status":"success","data":{"instruments":[...]}}
    instruments = data.get("data", {}).get("instruments", [])
    if not instruments:
        raise ValueError(f"No instrument found for search key: {search_key}")

    # Take the first match (you can refine later)
    first = instruments[0]
    token = first["instrument_token"]
    self.instrument_cache[symbol] = token
    print(f"✅ Found instrument: {first['tradingsymbol']} (token: {token})")
    return token
