from dataclasses import dataclass
from enum import Enum
import pandas as pd
from typing import Optional

class EventType(Enum):
    MARKET = 'MARKET'
    SIGNAL = 'SIGNAL'
    ORDER = 'ORDER'
    FILL = 'FILL'

class OrderType(Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP = 'STOP'
    TRAILING_STOP = 'TRAILING_STOP'

class Event:
    pass

@dataclass
class MarketEvent(Event):
    type: EventType = EventType.MARKET

@dataclass
class SignalEvent(Event):
    ticker: str
    target_weight: float
    timestamp: pd.Timestamp
    type: EventType = EventType.SIGNAL

@dataclass
class OrderEvent(Event):
    ticker: str
    quantity: float
    order_type: OrderType
    timestamp: pd.Timestamp
    price: Optional[float] = None
    type: EventType = EventType.ORDER

@dataclass
class FillEvent(Event):
    ticker: str
    quantity: float
    fill_price: float
    commission: float
    timestamp: pd.Timestamp
    exchange: str = "SIM"
    type: EventType = EventType.FILL
