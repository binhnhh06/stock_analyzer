import pandas as pd


def tim_cot(df, *tu_khoa):
    for c in df.columns:
        if all(k.lower() in str(c).lower() for k in tu_khoa):
            return c
    return None


def lay_dong(bang, *ten_chinh_xac):
    """Lấy 1 dòng (Series theo năm) theo tên chính xác, rồi theo từ khóa gần đúng."""
    if bang is None or bang.empty:
        return None
    for t in ten_chinh_xac:
        for idx in bang.index:
            if str(idx).strip().lower() == t.lower():
                return bang.loc[idx]
    for t in ten_chinh_xac:
        for idx in bang.index:
            if t.lower() in str(idx).lower():
                return bang.loc[idx]
    return None

def lay_dong_chinh_xac(bang, *ten):
    if bang is None or bang.empty:
        return None
    for t in ten:
        for idx in bang.index:
            if str(idx).strip().lower() == t.lower():
                return bang.loc[idx]
    return None


def tinh_ty_so(bctc):
    """Tự tính tỷ số từ BCTC. Trả về DataFrame (tỷ số x năm)."""
    bs, is_ = bctc.get("balance_sheet"), bctc.get("income_statement")
    cf = bctc.get("cash_flow")
    if bs is None or is_ is None:
        return pd.DataFrame()
    ta = lay_dong(bs, "TỔNG TÀI SẢN")
    eq = lay_dong(bs, "VỐN CHỦ SỞ HỮU")
    debt = lay_dong(bs, "NỢ PHẢI TRẢ")
    ca = lay_dong(bs, "TÀI SẢN NGẮN HẠN")
    cl = lay_dong(bs, "Nợ ngắn hạn")
    rev = lay_dong(is_, "Doanh số thuần")
    gp = lay_dong(is_, "Lãi gộp")
    npat = lay_dong(is_, "Lãi/(lỗ) thuần sau thuế", "Lợi nhuận sau thuế")

    kq = {}
    if npat is not None and eq is not None:
        kq["ROE (%)"] = npat / eq * 100
    if npat is not None and ta is not None:
        kq["ROA (%)"] = npat / ta * 100
    if npat is not None and rev is not None:
        kq["Biên LN ròng (%)"] = npat / rev * 100
    if gp is not None and rev is not None:
        kq["Biên LN gộp (%)"] = gp / rev * 100
    if debt is not None and eq is not None:
        kq["Nợ / VCSH (lần)"] = debt / eq
    if ca is not None and cl is not None:
        kq["Thanh toán hiện hành (lần)"] = ca / cl
    if rev is not None:
        kq["Tăng trưởng doanh thu (%)"] = rev.pct_change() * 100
    if npat is not None:
        kq["Tăng trưởng LNST (%)"] = npat.pct_change() * 100
        phan_vay = [x for x in (lay_dong_chinh_xac(bs, "Vay ngắn hạn"), lay_dong_chinh_xac(bs, "Vay dài hạn")) if x is not None]
    vay = pd.concat(phan_vay, axis=1).sum(axis=1, min_count=1) if phan_vay else None
    tien = lay_dong_chinh_xac(bs, "Tiền và tương đương tiền")
    ebit = lay_dong_chinh_xac(is_, "EBIT")
    lai_vay = lay_dong_chinh_xac(is_, "Trong đó: Chi phí lãi vay")
    cfo = lay_dong_chinh_xac(cf, "Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh")
    co_tuc = lay_dong_chinh_xac(cf, "Cổ tức đã trả")

    if vay is not None and eq is not None:
        kq["Nợ vay / VCSH (lần)"] = vay / eq
    if debt is not None and ta is not None:
        kq["Nợ / Tổng tài sản (%)"] = debt / ta * 100
    if rev is not None and ta is not None:
        kq["Vòng quay tài sản (lần)"] = rev / ta
    if tien is not None and ta is not None:
        kq["Tiền / Tổng tài sản (%)"] = tien / ta * 100
    if ta is not None:
        kq["Tăng trưởng tổng tài sản (%)"] = ta.pct_change() * 100
    if ebit is not None and lai_vay is not None:
        kq["EBIT / Lãi vay (lần)"] = ebit / lai_vay.abs().replace(0, float("nan"))
    if cfo is not None and npat is not None:
        kq["CFO / LNST (lần)"] = cfo / npat.where(npat > 0)
    if co_tuc is not None and npat is not None:
        kq["Chi trả cổ tức / LNST (%)"] = co_tuc.abs() / npat.where(npat > 0) * 100
    return pd.DataFrame(kq).T.sort_index(axis=1)


def phan_tich(gia, ratio, ty_so):
    gia = gia.copy()
    gia["MA20"] = gia["close"].rolling(20).mean()
    gia["MA50"] = gia["close"].rolling(50).mean()
    d = gia["close"].diff()
    rs = d.clip(lower=0).rolling(14).mean() / (-d.clip(upper=0)).rolling(14).mean()
    gia["RSI"] = 100 - 100 / (1 + rs)

    last = gia.iloc[-1]
    n = min(126, len(gia) - 1)
    kq = {
        "Giá đóng cửa": float(last["close"]),
        "MA20": float(last["MA20"]),
        "MA50": float(last["MA50"]),
        "RSI(14)": float(last["RSI"]),
        "Lợi suất 6 tháng (%)": float((gia["close"].iloc[-1] / gia["close"].iloc[-1 - n] - 1) * 100),
        "Biến động năm (%)": float(gia["close"].pct_change().std() * (252 ** 0.5) * 100),
    }

    pe = None
    c = tim_cot(ratio, "p/e") if not ratio.empty else None
    if c is not None:
        pe = float(ratio[c].iloc[0]); kq["P/E"] = pe
    c = tim_cot(ratio, "p/b") if not ratio.empty else None
    if c is not None:
        kq["P/B"] = float(ratio[c].iloc[0])

    roe = None
    if not ty_so.empty and "ROE (%)" in ty_so.index:
        roe = float(ty_so.loc["ROE (%)"].dropna().iloc[-1]); kq["ROE (%) (từ BCTC)"] = roe
    if not ty_so.empty and "Nợ / VCSH (lần)" in ty_so.index:
        kq["Nợ / VCSH (lần)"] = float(ty_so.loc["Nợ / VCSH (lần)"].dropna().iloc[-1])

    # Chấm điểm: 4 tiêu chí kỹ thuật + 4 tiêu chí cơ bản (tối đa 8)
    diem, ly_do, toi_da = 0, [], 4
    if kq["Giá đóng cửa"] > kq["MA50"]:
        diem += 1; ly_do.append("Giá trên MA50: xu hướng tăng")
    if kq["MA20"] > kq["MA50"]:
        diem += 1; ly_do.append("MA20 trên MA50: động lượng tích cực")
    if 30 < kq["RSI(14)"] < 70:
        diem += 1; ly_do.append("RSI trong vùng cân bằng (30-70)")
    if kq["Lợi suất 6 tháng (%)"] > 0:
        diem += 1; ly_do.append("Lợi suất 6 tháng dương")

    if roe is not None:
        toi_da += 1
        if roe >= 15:
            diem += 1; ly_do.append(f"ROE {roe:.1f}% (từ 15% trở lên)")
    if pe is not None:
        toi_da += 1
        if 0 < pe < 15:
            diem += 1; ly_do.append(f"P/E {pe:.1f} hấp dẫn (dưới 15)")
    if not ty_so.empty and "Nợ / VCSH (lần)" in ty_so.index:
        toi_da += 1
        if kq["Nợ / VCSH (lần)"] < 2:
            diem += 1; ly_do.append("Đòn bẩy an toàn (Nợ/VCSH dưới 2 lần)")
    if not ty_so.empty and "Tăng trưởng LNST (%)" in ty_so.index:
        toi_da += 1
        g = ty_so.loc["Tăng trưởng LNST (%)"].dropna()
        if len(g) and g.iloc[-1] > 0:
            diem += 1; ly_do.append(f"Lợi nhuận tăng trưởng {g.iloc[-1]:.1f}% so với năm trước")

    ti_le = diem / toi_da
    kn = "MUA / TÍCH LŨY" if ti_le >= 0.7 else "THEO DÕI" if ti_le >= 0.4 else "TRÁNH / CHỜ"
    return gia, kq, diem, toi_da, ly_do, kn