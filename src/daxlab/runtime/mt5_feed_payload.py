"""Strict closed-M5 feed payload validation for future read-only MT5 probes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from typing import Any, Mapping

from daxlab.runtime.mt5_readonly import Mt5Bar, closed_rates_start_pos

@dataclass(frozen=True, slots=True)
class ClosedM5Feed:
    observed_at: datetime
    requested_start_pos: int
    bars: tuple[Mt5Bar, ...]
    latest_closed_fingerprint: str
    age_seconds: float
    fresh: bool
    discontinuities: tuple[str, ...]

_REQUIRED={"observed_at","requested_start_pos","max_age_seconds","bars"}
_BAR_REQUIRED={"open_time","open","high","low","close"}

def parse_closed_m5_feed(payload: Mapping[str, Any]) -> ClosedM5Feed:
    missing=_REQUIRED-payload.keys(); unknown=payload.keys()-_REQUIRED
    if missing: raise ValueError(f"missing feed fields: {sorted(missing)}")
    if unknown: raise ValueError(f"unknown feed fields: {sorted(unknown)}")
    observed=_ts(payload["observed_at"],"observed_at")
    pos=payload["requested_start_pos"]
    if type(pos) is not int: raise ValueError("requested_start_pos must be integer")
    closed_rates_start_pos(pos)
    max_age=_number(payload["max_age_seconds"],"max_age_seconds", allow_zero=True)
    raw=payload["bars"]
    if not isinstance(raw,list) or not raw: raise ValueError("bars must be a non-empty list")
    bars=tuple(_bar(x) for x in raw)
    times=[b.open_time for b in bars]
    if times != sorted(times): raise ValueError("bars must be chronological")
    if len(set(times)) != len(times): raise ValueError("bar open_time values must be unique")
    for b in bars:
        if b.open_time+timedelta(minutes=5)>observed: raise ValueError("feed contains an unclosed M5 bar")
    latest=bars[-1]
    age=(observed-(latest.open_time+timedelta(minutes=5))).total_seconds()
    gaps=[]
    for a,b in zip(bars,bars[1:]):
        delta=(b.open_time-a.open_time).total_seconds()
        if delta != 300: gaps.append(f"{a.open_time.isoformat()}->{b.open_time.isoformat()}:{int(delta)}s")
    return ClosedM5Feed(observed,pos,bars,_fingerprint(latest),age,age<=max_age,tuple(gaps))

def feed_blocker(feed: ClosedM5Feed) -> str | None:
    if not feed.fresh: return "MARKET_DATA_STALE"
    if feed.discontinuities: return "MARKET_DATA_DISCONTINUITY"
    return None

def _bar(value: Any) -> Mt5Bar:
    if not isinstance(value,Mapping): raise ValueError("each bar must be an object")
    missing=_BAR_REQUIRED-value.keys(); unknown=value.keys()-_BAR_REQUIRED
    if missing: raise ValueError(f"missing bar fields: {sorted(missing)}")
    if unknown: raise ValueError(f"unknown bar fields: {sorted(unknown)}")
    t=_ts(value["open_time"],"open_time")
    o=_number(value["open"],"open"); h=_number(value["high"],"high"); l=_number(value["low"],"low"); c=_number(value["close"],"close")
    if h < max(o,c,l) or l > min(o,c,h): raise ValueError("OHLC invariant violated")
    return Mt5Bar(t,o,h,l,c)

def _ts(value: Any, field: str) -> datetime:
    if not isinstance(value,str): raise ValueError(f"{field} must be ISO-8601 string")
    try: out=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{field} must be valid ISO-8601") from exc
    if out.tzinfo is None: raise ValueError(f"{field} must be timezone-aware")
    return out

def _number(value: Any, field: str, allow_zero: bool=False) -> float:
    if not isinstance(value,(int,float)) or isinstance(value,bool): raise ValueError(f"{field} must be numeric")
    out=float(value)
    if field=="max_age_seconds" and (out<0 or (out==0 and not allow_zero)): raise ValueError("max_age_seconds must be non-negative")
    return out

def _fingerprint(bar: Mt5Bar) -> str:
    canonical=json.dumps({"open_time":bar.open_time.isoformat(),"open":bar.open,"high":bar.high,"low":bar.low,"close":bar.close},sort_keys=True,separators=(",",":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
