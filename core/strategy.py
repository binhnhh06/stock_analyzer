from datetime import datetime
import pandas as pd


def _val(ty_so, ten):
    if ty_so is None or ty_so.empty or ten not in ty_so.index:
        return None
    s = ty_so.loc[ten].dropna()
    return float(s.iloc[-1]) if len(s) else None


def diem_ta(gia):
    c = gia["close"]
    last = c.iloc[-1]
    ma20, ma50 = c.rolling(20).mean().iloc[-1], c.rolling(50).mean().iloc[-1]
    d = (10 if last > ma20 else 0) + (15 if last > ma50 else 0) + (15 if ma20 > ma50 else 0)
    n = min(63, len(c) - 1)
    ret3m = (last / c.iloc[-1 - n] - 1) * 100
    d += max(0, min(30, ret3m / 20 * 30))
    rsi = gia["RSI"].iloc[-1]
    d += 15 if 45 <= rsi <= 70 else 8 if (30 <= rsi < 45 or 70 < rsi <= 80) else 0
    if "volume" in gia:
        v20, v60 = gia["volume"].tail(20).mean(), gia["volume"].tail(60).mean()
        r = v20 / v60 if v60 else 0
        d += 15 if r >= 1 else 8 if r >= 0.8 else 0
    return round(float(d), 1)


def diem_fa(ty_so):
    roe, bien, no = _val(ty_so, "ROE (%)"), _val(ty_so, "Biên LN ròng (%)"), _val(ty_so, "Nợ / VCSH (lần)")
    tt, ttr = _val(ty_so, "Tăng trưởng LNST (%)"), _val(ty_so, "Thanh toán hiện hành (lần)")
    if all(x is None for x in (roe, bien, no, tt, ttr)):
        return 50.0, False
    d = 0
    if roe is not None: d += 30 if roe >= 15 else 20 if roe >= 10 else 10 if roe >= 5 else 0
    if bien is not None: d += 20 if bien >= 10 else 12 if bien >= 5 else 6 if bien > 0 else 0
    if no is not None: d += 20 if no < 1 else 12 if no < 2 else 5 if no < 3 else 0
    if tt is not None: d += 20 if tt > 15 else 12 if tt > 0 else 0
    if ttr is not None: d += 10 if ttr >= 1.5 else 6 if ttr >= 1 else 0
    return float(d), True


def danh_gia_x10(gia, kq, ty_so, vni):
    c = gia["close"]
    last = float(c.iloc[-1])
    ta = diem_ta(gia)
    fa, co_fa = diem_fa(ty_so)
    tong = round(0.2 * fa + 0.8 * ta, 1)

    px = c * (1000 if last < 1000 else 1)
    gtgd = float((px * gia["volume"]).tail(20).mean()) if "volume" in gia else 0.0
    moi = (datetime.now() - gia["time"].iloc[-1]).days <= 5
    du = len(gia) >= 200 and moi

    mua = [("Điểm thống nhất ≥ 60", "Đạt" if tong >= 60 else "Không đạt",
            f"{tong:.1f}/100 (kỹ thuật {ta:.1f}, cơ bản {fa:.1f})"),
           ("Dữ liệu đầy đủ, phiên mới nhất", "Đạt" if du else "Không đạt",
            f"{len(gia)} phiên, phiên cuối {gia['time'].iloc[-1]:%d/%m/%Y}"),
           ("GTGD bình quân 20 phiên ≥ 2 tỷ", "Đạt" if gtgd >= 2e9 else "Không đạt",
            f"{gtgd / 1e9:,.2f} tỷ đồng/phiên")]
    if vni is not None and len(vni) >= 50:
        v = vni["close"]
        ok = v.iloc[-1] >= v.rolling(50).mean().iloc[-1]
        mua.append(("VN-Index ≥ MA50", "Đạt" if ok else "Không đạt",
                    f"VN-Index {v.iloc[-1]:,.1f} / MA50 {v.rolling(50).mean().iloc[-1]:,.1f}"))
    else:
        mua.append(("VN-Index ≥ MA50", "N/A", "Không lấy được dữ liệu VN-Index"))
    mua.append(("Thuộc Top 30 theo điểm", "N/A", "Cần quét toàn thị trường, không áp dụng"))

    ma200 = c.rolling(200).mean().iloc[-1]
    peak = float(c.tail(60).max())
    dd = (peak - last) / peak * 100
    ban = []
    if pd.notna(ma200):
        ban.append(("Giá thủng MA200", "Kích hoạt" if last < ma200 else "Không",
                    f"Giá {last:,.2f} / MA200 {ma200:,.2f}"))
    else:
        ban.append(("Giá thủng MA200", "N/A", "Chưa đủ 200 phiên"))
    ban.append(("Giảm ≥ 15% từ đỉnh 60 phiên", "Kích hoạt" if dd >= 15 else "Không", f"Giảm {dd:.1f}% từ đỉnh"))
    ban.append(("Điểm thống nhất < 35", "Kích hoạt" if tong < 35 else "Không", f"{tong:.1f}/100"))

    if any(x[1] == "Kích hoạt" for x in ban):
        tin_hieu = "BÁN / TRÁNH"
    elif all(x[1] != "Không đạt" for x in mua):
        tin_hieu = "MUA"
    else:
        tin_hieu = "THEO DÕI"
    return {"tin_hieu": tin_hieu, "diem_ta": ta, "diem_fa": fa, "diem_tong": tong, "co_fa": co_fa,
            "gtgd": gtgd, "dk_mua": mua, "dk_ban": ban}


def dong_pdf(xep):
    out = ["Bộ lọc MUA:"] + [f"[{t}] {n}: {ct}" for n, t, ct in xep["dk_mua"]]
    out += ["Bộ lọc BÁN:"] + [f"[{t}] {n}: {ct}" for n, t, ct in xep["dk_ban"]]
    return out