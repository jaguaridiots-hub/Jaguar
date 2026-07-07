from market.adapter import detect_market

from market.crypto import get_crypto
from market.forex import get_forex
from market.nse import get_nse
from market.bse import get_bse
from market.us import get_us
from market.mcx import get_mcx


def load_market(symbol):

    market = detect_market(symbol)

    if market == "CRYPTO":
        return get_crypto(symbol)

    elif market == "FOREX":
        return get_forex(symbol)

    elif market == "NSE":
        return get_nse(symbol)

    elif market == "BSE":
        return get_bse(symbol)

    elif market == "US":
        return get_us(symbol)

    elif market == "MCX":
        return get_mcx(symbol)

    raise Exception(f"Unsupported market : {symbol}")
