from functools import lru_cache
from pathlib import Path
import pandas as pd

_DUONG_DAN = Path(__file__).resolve().parent.parent / "data" / "icb_companies.csv"


@lru_cache(maxsize=1)
def danh_sach_cong_ty():
    try:
        return pd.read_csv(_DUONG_DAN, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.DataFrame(columns=["ma", "ten", "san", "icb1", "icb2", "icb3"])


def thong_tin(ma):
    d = danh_sach_cong_ty()
    if d.empty:
        return {}
    r = d[d["ma"] == str(ma).upper().strip()]
    return {} if r.empty else r.iloc[0].to_dict()


def nganh_cap1():
    d = danh_sach_cong_ty()
    return sorted(x for x in d["icb1"].unique() if x)


def loc_ma(icb1=None, icb2=None, san=None, toi_da=None):
    d = danh_sach_cong_ty()
    if d.empty:
        return []
    if icb1:
        d = d[d["icb1"].isin(icb1)]
    if icb2:
        d = d[d["icb2"].isin(icb2)]
    if san:
        d = d[d["san"].isin(san)]
    ma = list(d["ma"])
    return ma[:toi_da] if toi_da else ma