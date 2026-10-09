import pandas as pd
from functools import lru_cache
from datetime import datetime, timedelta
from vnstock import Vnstock

try:
    import vnfinancialdata as vnf
except Exception:
    vnf = None

STATEMENTS = {"balance_sheet": "Bảng cân đối kế toán",
              "income_statement": "Kết quả kinh doanh",
              "cash_flow": "Lưu chuyển tiền tệ"}


def lay_gia(ma, so_ngay=730):
    s = Vnstock().stock(symbol=ma, source="VCI")
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=so_ngay)).strftime("%Y-%m-%d")
    gia = s.quote.history(start=start, end=end, interval="1D")
    gia["time"] = pd.to_datetime(gia["time"])
    return gia


@lru_cache(maxsize=8)
def _nap_bang(san, st):
    return vnf.load(exchange=san, statement=st)


def lay_bctc(ma, so_nam=6):
    """Trả về dict {statement: bảng item_name x năm}. Rỗng nếu không có dữ liệu."""
    kq = {}
    if vnf is None:
        return kq
    for st in STATEMENTS:
        for san in ("HSX", "HNX"):
            try:
                df = _nap_bang(san, st)
            except Exception:
                continue
            d = df[df["ticker"].astype(str).str.upper() == ma]
            if d.empty:
                continue
            d = d.copy()
            d["year"] = pd.to_numeric(d["year"], errors="coerce")
            d = d.dropna(subset=["year", "value"])
            nam = sorted(d["year"].astype(int).unique())[-so_nam:]
            d = d[d["year"].isin(nam)]
            bang = d.pivot_table(index="item_name", columns="year", values="value", aggfunc="first")
            bang.columns = [int(c) for c in bang.columns]
            kq[st] = bang.dropna(how="all")
            break
    return kq


def lay_ratio(ma):
    try:
        s = Vnstock().stock(symbol=ma, source="VCI")
        ratio = s.finance.ratio(period="year", lang="vi")
        if isinstance(ratio.columns, pd.MultiIndex):
            ratio.columns = [" ".join(map(str, c)).strip() for c in ratio.columns]
        return ratio
    except Exception:
        return pd.DataFrame()


def lay_vnindex(so_ngay=730):
    try:
        s = Vnstock().stock(symbol="VNINDEX", source="VCI")
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=so_ngay)).strftime("%Y-%m-%d")
        d = s.quote.history(start=start, end=end, interval="1D")
        d["time"] = pd.to_datetime(d["time"])
        return d
    except Exception:
        return None