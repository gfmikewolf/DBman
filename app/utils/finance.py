from flask import session
from typing import cast
from datetime import date, timedelta
from yfinance import Ticker
from scipy.optimize import brentq
import requests, xml.etree.ElementTree as ET

def get_stock_price(code: str, target_date: date = date.today()) -> float | None:
    """
    Get the stock price for a given stock code.
    :param code: The stock code.
    :return: The stock price or None if not available.
    """    
    price_dict = session.get('CACHED_STOCK_PRICE', None)
    if price_dict and code in price_dict:
        price_list = price_dict[code]
        if price_list and price_list[1] == target_date and price_list[0] is not None:
            return price_list[0]
    ticker = Ticker(code)
    hist = ticker.history(
        start=target_date - timedelta(days=14),
        end = target_date + timedelta(days=1),
        auto_adjust=False
    )
    if hist.empty:
        return None
    closes = hist['Close'].dropna()
    closes = closes[
        closes.index.to_series().dt.date.le(target_date)
    ]
    if closes.empty:
        return None
    price = float(closes.iloc[-1])
    session['CACHED_STOCK_PRICE'] = dict()
    session['CACHED_STOCK_PRICE'][code] = [price, date.today()]
    return price
def xnpv(rate: float, flows: list[tuple[date, float]]) -> float:
    """
    Calculate the net present value (NPV) of a series of cash flows.
    :param rate: The discount rate.
    :param flows: A list of tuples containing the date and cash flow amount.
    :param initial_date: The initial date for the cash flows.
    :return: The NPV of the cash flows.
    """
    if not flows:
        return 0.0
    return sum(cf / (1 + rate) ** ((dt - flows[0][0]).days / 365.0) for dt, cf in flows)
def xirr(flows: list[tuple[date, float]]) -> float:
    """
    Calculate the internal rate of return (IRR) for a series of cash flows.
    :param flows: A list of tuples containing the date and cash flow amount.
    :return: The IRR of the cash flows.
    """
    if not flows or len(flows) < 2 or all(cf == 0 for _, cf in flows) or all(dt == flows[0][0] for dt, _ in flows):
        return 0.0
    return cast( 
        float,
        brentq(
            xnpv, 
            -0.9999+1e-6, 
            10000, 
            args=(flows)
        )
    )
