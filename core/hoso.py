"""Tab "Hiểu doanh nghiệp": suất cổ tức, so sánh ngành bằng dữ liệu thật, tin tức và sổ tay luận điểm."""

from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.analysis import lay_dong, tinh_ty_so
from core.dinhdang import so_vn
from core.theme import MAU, PASTEL, theme_plotly
from core import industry
from core.pipeline import phan_tich_ma
from core.data import lay_so_cp, LOI

HIEN_DEBUG = False  # đổi thành True khi cần kiểm tra dữ liệu

def _chuoi(ty_so, ten):
    if ty_so is None or ty_so.empty or ten not in ty_so.index:
        return None
    s = pd.to_numeric(ty_so.loc[ten], errors="coerce").dropna()
    s = s[~s.isin([float("inf"), float("-inf")])]
    return s if len(s) else None


def _cuoi(ty_so, ten):
    s = _chuoi(ty_so, ten)
    return float(s.iloc[-1]) if s is not None else None


def _f(v, n=1, hau_to=""):
    return f"{so_vn(v, n)}{hau_to}" if v is not None else "N/A"


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _so_cp(ma):
    return lay_so_cp(ma)


def _gia_tri_cuoi(s):
    if s is None:
        return None, None
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return None, None
    return float(s.iloc[-1]), s.index[-1]


def dinh_gia_tu_bctc(ma, bctc, gia):
    """P/E, P/B tự tính từ giá hiện tại và BCTC. Trả (pe, pb, ghi_chu).
    Ưu tiên EPS, BVPS (đồng/cp) trong BCTC; thiếu thì tính qua số cp lưu hành từ vnstock."""
    if gia is None or gia.empty:
        return None, None, "Thiếu dữ liệu giá."
    px = float(gia["close"].iloc[-1])
    if 0 < px < 1000:  # vnstock trả giá theo nghìn đồng
        px *= 1000

    pe = pb = None
    ghi = []

    # Cách 1: EPS, BVPS trong BCTC
    try:
        ts = tinh_ty_so(bctc) if bctc else pd.DataFrame()
    except Exception:
        ts = pd.DataFrame()
    if ts is not None and not ts.empty:
        if "EPS (đồng)" in ts.index:
            eps, nam = _gia_tri_cuoi(ts.loc["EPS (đồng)"])
            if eps and eps > 0:
                pe = px / eps
                ghi.append(f"P/E theo EPS năm {nam}")
        if "BVPS (đồng)" in ts.index:
            bv, nam = _gia_tri_cuoi(ts.loc["BVPS (đồng)"])
            if bv and bv > 0:
                pb_thu = px / bv
                if 0.05 <= pb_thu <= 100:
                    pb = pb_thu
                    ghi.append(f"P/B theo giá trị sổ sách năm {nam}")

    # Cách 2: dự phòng qua số cổ phiếu lưu hành (vnstock)
    if pe is None or pb is None:
        so_cp = _so_cp(ma)
        bctc = bctc or {}
        lnst, nam = _gia_tri_cuoi(lay_dong(bctc.get("income_statement"), "Lãi/(lỗ) thuần sau thuế", "Lợi nhuận sau thuế"))
        vcsh, _ = _gia_tri_cuoi(lay_dong(bctc.get("balance_sheet"), "Vốn chủ sở hữu", "VỐN CHỦ SỞ HỮU"))
        if so_cp and lnst is not None and vcsh and vcsh > 0:
            k = 1.0 if vcsh >= 1e10 else 1e6 if vcsh >= 1e4 else 1e9  # đoán đơn vị BCTC
            if pe is None and lnst > 0:
                pe = px / (lnst * k / so_cp)
                ghi.append(f"P/E theo LNST năm {nam} và số cp lưu hành")
            if pb is None:
                pb_thu = px / (vcsh * k / so_cp)
                if 0.05 <= pb_thu <= 100:
                    pb = pb_thu
                    ghi.append("P/B theo VCSH và số cp lưu hành")

    if pe is None and pb is None:
        return None, None, "Chưa tính được P/E, P/B (thiếu EPS/BVPS trong BCTC và số cổ phiếu lưu hành)."
    return pe, pb, "; ".join(ghi) + f". Giá {so_vn(px, 0)} đ."
def uoc_suat_co_tuc(ty_so, pe):
    """Suất cổ tức ước tính = tỷ lệ chi trả (TB 3 năm) / P/E. Không dùng số giả định."""
    payout = _chuoi(ty_so, "Chi trả cổ tức / LNST (%)")
    if payout is None or not pe or pe <= 0:
        return None
    return float(payout.tail(3).mean()) / pe


def _hang_ma(m, ty_so, bctc, gia):
    pe, pb, _ = dinh_gia_tu_bctc(m, bctc, gia)
    return {
        "Doanh nghiệp": m,
        "ROE (%)": _cuoi(ty_so, "ROE (%)"),
        "Biên LN gộp (%)": _cuoi(ty_so, "Biên LN gộp (%)"),
        "P/E (lần)": pe,
        "P/B (lần)": pb,
    }


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def _chi_so_ma(m, _vni):
    r = phan_tich_ma(m, 365, 6, _vni)
    return _hang_ma(m, r["ty_so"], r["bctc"], r["gia"])


def _ma_cung_nganh(ma, info, toi_da=5):
    """Ưu tiên mã cùng ICB cấp 3, thiếu thì bổ sung mã cùng ICB cấp 2."""
    icb1, icb2, icb3 = info.get("icb1"), info.get("icb2"), info.get("icb3")
    ung_vien = industry.loc_ma([icb1] if icb1 else None, None, None, 500)
    ds = [m for m in ung_vien if m != ma]
    tt = {m: industry.thong_tin(m) for m in ds}
    cung3 = [m for m in ds if icb3 and tt[m].get("icb3") == icb3]
    cung2 = [m for m in ds if m not in cung3 and tt[m].get("icb2") == icb2]
    return (cung3 + cung2)[:toi_da]


def phan_loai(ty_so, bctc):
    roe, tt = _chuoi(ty_so, "ROE (%)"), _chuoi(ty_so, "Tăng trưởng LNST (%)")
    cotuc, no = _chuoi(ty_so, "Chi trả cổ tức / LNST (%)"), _chuoi(ty_so, "Nợ / VCSH (lần)")
    lnst = lay_dong((bctc or {}).get("income_statement"), "Lãi/(lỗ) thuần sau thuế", "Lợi nhuận sau thuế")
    if roe is None and tt is None:
        return "Chưa đủ dữ liệu", "Chưa có đủ báo cáo tài chính để phân loại.", PASTEL["tim"], []

    ly_do = []
    tb_tt = float(tt.tail(3).mean()) if tt is not None else None
    dao_dong = float(tt.tail(6).std()) if tt is not None and len(tt.tail(6)) >= 4 else None
    co_lo = lnst is not None and bool((pd.to_numeric(lnst, errors="coerce").tail(6) <= 0).any())
    roe_tb = float(roe.tail(3).mean()) if roe is not None else None
    payout = float(cotuc.tail(3).mean()) if cotuc is not None else None

    if tb_tt is not None:
        ly_do.append(f"LNST {'tăng' if tb_tt >= 0 else 'giảm'} trung bình {so_vn(abs(tb_tt), 1)}%/năm (3 năm)")
    if roe_tb is not None:
        ly_do.append(f"ROE trung bình 3 năm: {so_vn(roe_tb, 1)}%")
    if payout is not None:
        ly_do.append(f"Chi trả cổ tức khoảng {so_vn(payout, 0)}% LNST")

    if co_lo or (dao_dong is not None and dao_dong > 50):
        return ("Chu kỳ", "Lợi nhuận biến động mạnh theo ngành.", PASTEL["vang"], ly_do)
    if tb_tt is not None and tb_tt >= 15 and (roe_tb is None or roe_tb >= 12):
        return ("Tăng trưởng", "Lợi nhuận tăng nhanh, hiệu quả vốn tốt.", PASTEL["lime"], ly_do)
    if payout is not None and payout >= 40:
        return ("Cổ tức & Phòng thủ", "Chia phần lớn lợi nhuận bằng tiền mặt, dòng tiền đều đặn.", PASTEL["cyan"], ly_do)
    return ("Ổn định", "Ít biến động, đòn bẩy vừa phải.", PASTEL["hong"], ly_do)


def diem_manh_yeu(ty_so):
    kq = []
    cuoi = lambda ten: _cuoi(ty_so, ten)

    v = cuoi("ROE (%)")
    if v is not None:
        if v >= 15:
            kq.append(("manh", f"ROE {so_vn(v, 1)}%: Dùng vốn hiệu quả"))
        elif v < 8:
            kq.append(("yeu", f"ROE {so_vn(v, 1)}% thấp: Hiệu quả sử dụng vốn kém"))

    v = cuoi("CFO / LNST (lần)")
    if v is not None:
        if v >= 1:
            kq.append(("manh", f"CFO/LNST = {so_vn(v, 2)}: Lợi nhuận được hậu thuẫn bằng tiền thật"))
        elif v < 0.8:
            kq.append(("yeu", f"CFO/LNST = {so_vn(v, 2)}: Lợi nhuận chưa chuyển hết thành tiền"))

    tt = _chuoi(ty_so, "Tăng trưởng LNST (%)")
    if tt is not None:
        tb = float(tt.tail(3).mean())
        if tb < 0:
            kq.append(("yeu", f"LNST giảm trung bình {so_vn(abs(tb), 1)}%/năm (3 năm gần nhất)"))
        elif tb >= 10:
            kq.append(("manh", f"LNST tăng trung bình {so_vn(tb, 1)}%/năm (3 năm gần nhất)"))

    cp = _chuoi(ty_so, "Chi trả cổ tức / LNST (%)")
    if cp is not None and float(cp.tail(3).mean()) > 100:
        kq.append(("yeu", f"Chi trả cổ tức TB {so_vn(float(cp.tail(3).mean()), 0)}% LNST: vượt lợi nhuận, khó duy trì lâu dài"))

    v = cuoi("Nợ vay / VCSH (lần)")
    if v is not None and v > 1:
        kq.append(("yeu", f"Nợ vay gấp {so_vn(v, 2)} lần VCSH: Áp lực lãi vay lớn"))
    return kq


CHI_SO_CHU_KY = ("ROE (%)", "Biên LN ròng (%)", "Biên LN gộp (%)")


def chu_ky(ty_so):
    kq = []
    for ten in CHI_SO_CHU_KY:
        s = _chuoi(ty_so, ten)
        if s is None or len(s) < 4:
            continue
        hien, tb, lo, hi = float(s.iloc[-1]), float(s.mean()), float(s.min()), float(s.max())
        vt = (hien - lo) / (hi - lo) if hi > lo else 0.5
        nhan = "gần đỉnh" if vt >= 0.8 else "gần đáy" if vt <= 0.2 else "ở giữa"
        kq.append({"ten": ten, "chuoi": s, "hien": hien, "tb": tb, "lo": lo, "hi": hi, "nhan": nhan})
    return kq


def _loi_suat(df, n):
    c = df["close"].dropna()
    return float((c.iloc[-1] / c.iloc[-1 - n] - 1) * 100) if len(c) > n else None


def so_voi_thi_truong(gia, vni):
    if vni is None or len(vni) < 60:
        return None, None
    hang = []
    for n, nhan in ((63, "3 tháng"), (126, "6 tháng"), (252, "12 tháng")):
        a, b = _loi_suat(gia, n), _loi_suat(vni, n)
        if a is not None and b is not None:
            hang.append({"Giai đoạn": nhan, "Mã (%)": a, "VN-Index (%)": b, "Chênh lệch (%)": a - b})
    v = vni["close"]
    ma50 = v.rolling(50).mean().iloc[-1]
    ma200 = v.rolling(200).mean().iloc[-1] if len(v) >= 200 else None
    xu_huong = "Thị trường tăng mạnh." if (ma200 is not None and v.iloc[-1] > ma50 and v.iloc[-1] > ma200) else "Thị trường biến động/điều chỉnh."
    return pd.DataFrame(hang), xu_huong


def _bieu_do_so_sanh(ma, gia, vni):
    a = gia[["time", "close"]].copy()
    b = vni[["time", "close"]].copy()
    a["time"], b["time"] = pd.to_datetime(a["time"]).dt.normalize(), pd.to_datetime(b["time"]).dt.normalize()
    m = a.merge(b, on="time", suffixes=("_ma", "_vni")).dropna()
    if len(m) < 30:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["time"], y=m["close_ma"] / m["close_ma"].iloc[0] * 100, name=ma, line=dict(color=MAU["tim"], width=3)))
    fig.add_trace(go.Scatter(x=m["time"], y=m["close_vni"] / m["close_vni"].iloc[0] * 100, name="VN-Index", line=dict(color=MAU["hong"], width=2, dash="dot")))
    fig.update_yaxes(title="Quy về 100")
    return theme_plotly(fig, 300)


def ve_tab_hoso(r):
    if not r:
        st.info("Bấm **Phân tích** ở thanh bên trái để xem hồ sơ chuyên sâu.")
        return

    ma, ty_so, bctc, gia, vni = r["ma"], r["ty_so"], r["bctc"], r["gia"], r.get("vni")
    info = industry.thong_tin(ma)
    nganh = " › ".join(x for x in (info.get("icb1", ""), info.get("icb2", ""), info.get("icb3", "")) if x)
    gia_hien_tai = float(gia["close"].iloc[-1]) if gia is not None and not gia.empty else 0
    if 0 < gia_hien_tai < 1000:  # vnstock trả giá theo nghìn đồng
        gia_hien_tai *= 1000

    st.markdown(f"### Hồ sơ chuyên sâu & Định giá: **{ma}** - {info.get('ten', '')}")
    st.caption(f"Ngành ICB: {nganh if nganh else 'Chưa cập nhật'} | Giá hiện tại: **{so_vn(gia_hien_tai, 0)} VND**")

    # 1. Suất cổ tức & Định giá (tự tính từ giá hiện tại + BCTC)
    st.subheader("1. Suất Cổ tức & Định giá")
    pe, pb, ghi_chu = dinh_gia_tu_bctc(ma, bctc, gia)
    suat = uoc_suat_co_tuc(ty_so, pe)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Suất cổ tức (ước tính)", _f(suat, 1, "%"),
              help="= Tỷ lệ chi trả cổ tức/LNST (TB 3 năm) ÷ P/E. Đây là ước tính, không phải cổ tức thực nhận.")
    c2.metric("P/E", _f(pe, 1, " lần"))
    c3.metric("P/B", _f(pb, 2, " lần"))
    c4.metric("Giá hiện tại", _f(gia_hien_tai or None, 0))
    st.caption(f"P/E, P/B tự tính từ giá hiện tại và BCTC (gần đúng, nên đối chiếu CafeF/Vietstock). {ghi_chu}")
    if HIEN_DEBUG:
        with st.expander("Kiểm tra dữ liệu (debug)"):
            st.write({"Số cổ phiếu lưu hành": _so_cp(ma), "Lỗi nguồn dữ liệu": {k: v for k, v in LOI.items() if "so_cp" in k}})
            pay = _chuoi(ty_so, "Chi trả cổ tức / LNST (%)")
            st.write("Chi trả cổ tức / LNST (%):", pay.to_dict() if pay is not None else "không có chuỗi này")
            cf = (bctc or {}).get("cash_flow")
            if cf is not None and not cf.empty:
                loc = cf[cf.index.astype(str).str.contains("cổ tức|lợi nhuận đã trả|dividend", case=False, na=False)]
                if loc.empty:
                    st.write("Báo cáo lưu chuyển tiền tệ không có dòng nào chứa 'cổ tức'.")
                else:
                    st.dataframe(loc, use_container_width=True)
            else:
                st.write("Không có báo cáo lưu chuyển tiền tệ.")

    # 2. Phân loại doanh nghiệp
    st.subheader("2. Phân loại & Chất lượng Dòng tiền")
    nhom, mo_ta, mau, ly_do = phan_loai(ty_so, bctc)
    st.markdown(f"<div class='x10-card' style='background:{mau}'><b>Nhóm: {nhom}</b><br>{mo_ta}</div>", unsafe_allow_html=True)
    if ly_do:
        st.markdown("".join(f"<div class='x10-small'>• {x}</div>" for x in ly_do), unsafe_allow_html=True)

    col_cf1, col_cf2 = st.columns(2)
    with col_cf1:
        if ty_so is not None and "Chi trả cổ tức / LNST (%)" in ty_so.index:
            s_ct = ty_so.loc["Chi trả cổ tức / LNST (%)"].dropna()
            if not s_ct.empty:
                f_ct = go.Figure(go.Bar(x=[str(x) for x in s_ct.index], y=s_ct.values, marker_color=MAU["cyan"]))
                f_ct.update_layout(title="Tỷ lệ chi trả cổ tức / LNST (%)", height=240, margin=dict(t=30, b=20))
                st.plotly_chart(theme_plotly(f_ct, 240), use_container_width=True)
    with col_cf2:
        if ty_so is not None and "CFO / LNST (lần)" in ty_so.index:
            s_cfo = ty_so.loc["CFO / LNST (lần)"].dropna()
            if not s_cfo.empty:
                f_cfo = go.Figure(go.Bar(x=[str(x) for x in s_cfo.index], y=s_cfo.values, marker_color=MAU["tim"]))
                f_cfo.update_layout(title="Chất lượng dòng tiền (CFO / LNST)", height=240, margin=dict(t=30, b=20))
                st.plotly_chart(theme_plotly(f_cfo, 240), use_container_width=True)

    # 3. So sánh cùng ngành (dữ liệu thật, tính từ BCTC và giá hiện tại)
    st.subheader("3. So sánh vị thế cùng ngành")
    nhap = st.text_input("Mã so sánh (cách nhau bằng dấu phẩy; để trống = tự chọn cùng ngành ICB)",
                         key=f"peer_{ma}", placeholder="vd: VNM, MSN, MCH")
    if st.button("Tải bảng so sánh ngành", key=f"btn_peer_{ma}"):
        ds_peer = [m.strip().upper() for m in nhap.split(",") if m.strip()] or _ma_cung_nganh(ma, info)
        hang, loi = [_hang_ma(ma, ty_so, bctc, gia)], []
        with st.spinner("Đang tính chỉ số các mã cùng ngành (mất vài chục giây)..."):
            for m in ds_peer[:5]:
                try:
                    hang.append(_chi_so_ma(m, vni))
                except Exception as e:
                    loi.append(f"{m}: {str(e)[:80]}")
        df_ss = pd.DataFrame(hang)
        for c in df_ss.columns[1:]:
            df_ss[c] = pd.to_numeric(df_ss[c], errors="coerce")
        st.session_state[f"bang_{ma}"] = df_ss
        st.session_state[f"loi_{ma}"] = loi

    bang_nganh = st.session_state.get(f"bang_{ma}")
    if bang_nganh is not None and len(bang_nganh) > 1:
        peers = bang_nganh.iloc[1:]
        tv = {"Doanh nghiệp": "Trung vị nhóm so sánh"}
        tv.update({c: peers[c].median() for c in bang_nganh.columns[1:]})
        hien = pd.concat([bang_nganh, pd.DataFrame([tv])], ignore_index=True)
        st.dataframe(hien.style.format({c: "{:,.1f}" for c in hien.columns[1:]}, na_rep="N/A"),
                     use_container_width=True, hide_index=True)
        st.caption("ROE, biên gộp lấy từ BCTC năm gần nhất; P/E, P/B tính từ giá hiện tại. "
                   "Trung vị tính trên các mã trong bảng này, không phải toàn ngành.")
        for dong in st.session_state.get(f"loi_{ma}", []):
            st.caption(f"⚠️ Bỏ qua {dong}")
    else:
        st.info("Bấm nút trên để tải bảng so sánh.")

    # 4. Điểm mạnh & Điểm yếu
    st.subheader("4. Điểm mạnh & Điểm yếu cốt lõi")
    ds = diem_manh_yeu(ty_so)
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Điểm mạnh**")
        for loai, t in ds:
            if loai == "manh":
                st.markdown(f"- ✅ {t}")
        if not any(l == "manh" for l, _ in ds):
            st.caption("Chưa có tiêu chí nào đạt mức mạnh.")
    with d2:
        st.markdown("**Rủi ro / Điểm yếu**")
        for loai, t in ds:
            if loai == "yeu":
                st.markdown(f"- ⚠️ {t}")
        if not any(l == "yeu" for l, _ in ds):
            st.caption("Chưa phát hiện điểm yếu theo các tiêu chí đã kiểm tra.")

    # 5. So với thị trường chung
    st.subheader("5. Sức mạnh giá so với VN-Index")
    bang, xu_huong = so_voi_thi_truong(gia, vni)
    if bang is not None and not bang.empty:
        st.write(xu_huong)
        st.dataframe(bang, hide_index=True, use_container_width=True)
        fig = _bieu_do_so_sanh(ma, gia, vni)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    # 6. Tin tức & Kho tài liệu
    st.subheader("6. Tin tức Trọng yếu & Kho Tài liệu Chính thống")
    col_tin1, col_tin2 = st.columns(2)
    with col_tin1:
        st.markdown("**📰 Tin tức:**")
        st.markdown(f"- [Tin mới nhất về {ma}](https://news.google.com/search?q={quote(ma + ' cổ phiếu')})")
        st.markdown(f"- [Xu hướng ngành {nganh}](https://news.google.com/search?q={quote(nganh + ' chứng khoán')})")
    with col_tin2:
        st.markdown("**📚 Tài liệu doanh nghiệp:**")
        st.markdown(f"- 📄 [Báo cáo tài chính & Kiểm toán {ma}](https://s.cafef.vn/tra-cuu-chung-khoan-3-{ma.lower()}.chn)")
        st.markdown(f"- 🗳️ [Tài liệu Đại hội Cổ đông & Thường niên](https://www.google.com/search?q={quote(info.get('ten', ma) + ' báo cáo thường niên đại hội đồng cổ đông site:cafef.vn')})")

    # 7. Sổ tay Luận điểm Đầu tư
    st.subheader("7. Sổ tay Luận điểm Đầu tư Cá nhân")
    st.text_area(f"Ghi chú luận điểm nắm giữ {ma}", key=f"thesis_{ma}", height=120,
                 placeholder="Ghi lại lý do mua, mức suất cổ tức kỳ vọng và rủi ro cần theo dõi...")