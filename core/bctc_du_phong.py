import pandas as pd

_META = {"cp", "ticker", "symbol", "mã", "ma", "kỳ", "ky", "quý", "quy", "kỳ báo cáo", "lengthreport",
         "năm", "nam", "yearreport", "year", "fiscal_year", "period"}
_COT_NAM = ("năm", "nam", "yearreport", "year", "fiscal_year")


def _sang_bang(df, so_nam):
    """Bảng vnstock (mỗi dòng một năm, mỗi cột một chỉ tiêu) -> bảng chỉ tiêu x năm."""
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in c if "Unnamed" not in str(x)).strip() for c in df.columns]
    df.columns = [str(c).strip() for c in df.columns]

    cot_nam = next((c for c in df.columns if c.lower() in _COT_NAM), None)
    if cot_nam is not None:
        df[cot_nam] = pd.to_numeric(df[cot_nam], errors="coerce")
        df = df.dropna(subset=[cot_nam]).drop_duplicates(subset=[cot_nam], keep="last")
        df = df.set_index(cot_nam)
        df.index = df.index.astype(int)
        df = df[[c for c in df.columns if c.lower() not in _META]]
        bang = df.apply(pd.to_numeric, errors="coerce").T
    else:
        nam = [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]
        if not nam:
            return None
        bang = df[nam].apply(pd.to_numeric, errors="coerce")
        bang.columns = [int(c) for c in nam]
        for ten in ("item_name", "Chỉ tiêu", "item"):
            if ten in df.columns:
                bang.index = df[ten].astype(str)
                break
    bang = bang.dropna(how="all")
    bang = bang[~bang.index.duplicated(keep="first")]
    bang.columns = [int(c) for c in bang.columns]
    return bang[sorted(bang.columns)[-so_nam:]]


def lay_bctc_du_phong(ma, so_nam=6):
    """Lấy BCTC từ vnstock khi vnfinancialdata không có mã. Cùng định dạng với lay_bctc."""
    from core import data as d
    if d.Vnstock is None:
        return {}
    kq = {}
    try:
        fin = d.Vnstock().stock(symbol=ma, source="VCI").finance
    except Exception as e:
        d.LOI["bctc_du_phong"] = f"vnstock lỗi khi mở {ma}: {type(e).__name__}: {e}"
        return kq
    for k in ("balance_sheet", "income_statement", "cash_flow"):
        for kw in ({"period": "year", "lang": "vi"}, {"period": "year"}):
            try:
                bang = _sang_bang(getattr(fin, k)(**kw), so_nam)
            except Exception as e:
                d.LOI["bctc_du_phong"] = f"{k}: {type(e).__name__}: {e}"
                continue
            if bang is not None and not bang.empty:
                kq[k] = bang
                break
    return kq