"""Tab "Hiểu doanh nghiệp": phân loại, điểm mạnh/yếu, vị trí chu kỳ, so với thị trường, câu hỏi tự nghiên cứu.

Dùng trong app.py:
    from core.hoso import ve_tab_hoso
    with tabs[6]:
        ve_tab_hoso(r)
"""
from urllib.parse import quote
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.analysis import lay_dong
from core.dinhdang import so_vn
from core.theme import MAU, PASTEL, theme_plotly
from core import industry


def _chuoi(ty_so, ten):
    """Chuỗi giá trị theo năm của 1 tỷ số, bỏ ô trống và vô cực."""
    if ty_so is None or ty_so.empty or ten not in ty_so.index:
        return None
    s = pd.to_numeric(ty_so.loc[ten], errors="coerce").dropna()
    s = s[~s.isin([float("inf"), float("-inf")])]
    return s if len(s) else None


def _cuoi(ty_so, ten):
    s = _chuoi(ty_so, ten)
    return float(s.iloc[-1]) if s is not None else None


# ---------------------------------------------------------------- 1. phân loại doanh nghiệp
def phan_loai(ty_so, bctc):
    """Trả về (nhóm, mô tả, màu, danh sách lý do). Quy ước tham khảo, không phải kết luận."""
    roe, tt = _chuoi(ty_so, "ROE (%)"), _chuoi(ty_so, "Tăng trưởng LNST (%)")
    cotuc, no = _chuoi(ty_so, "Chi trả cổ tức / LNST (%)"), _chuoi(ty_so, "Nợ / VCSH (lần)")
    lnst = lay_dong((bctc or {}).get("income_statement"), "Lãi/(lỗ) thuần sau thuế", "Lợi nhuận sau thuế")
    if roe is None and tt is None:
        return "Chưa đủ dữ liệu", "Chưa có đủ báo cáo tài chính để phân loại. Bạn có thể tải BCTC của mình ở thanh bên.", \
            PASTEL["tim"], []

    ly_do = []
    tb_tt = float(tt.tail(3).mean()) if tt is not None else None
    dao_dong = float(tt.tail(6).std()) if tt is not None and len(tt.tail(6)) >= 4 else None
    co_lo = lnst is not None and bool((pd.to_numeric(lnst, errors="coerce").tail(6) <= 0).any())
    roe_tb = float(roe.tail(3).mean()) if roe is not None else None
    payout = float(cotuc.tail(3).mean()) if cotuc is not None else None
    no_gan = float(no.iloc[-1]) if no is not None else None

    if tb_tt is not None:
        ly_do.append(f"Lợi nhuận sau thuế tăng trung bình {so_vn(tb_tt, 1)}%/năm trong 3 năm gần nhất")
    if dao_dong is not None:
        ly_do.append(f"Tăng trưởng lợi nhuận dao động khoảng ±{so_vn(dao_dong, 0)} điểm % giữa các năm")
    if co_lo:
        ly_do.append("Có năm lỗ hoặc lãi bằng 0 trong 6 năm gần nhất")
    if roe_tb is not None:
        ly_do.append(f"ROE trung bình 3 năm: {so_vn(roe_tb, 1)}%")
    if payout is not None:
        ly_do.append(f"Chi trả cổ tức tiền mặt khoảng {so_vn(payout, 0)}% lợi nhuận (ước tính, trung bình 3 năm)")

    if co_lo or (dao_dong is not None and dao_dong > 50):
        return ("Chu kỳ", "Lợi nhuận lên xuống mạnh theo từng giai đoạn của ngành. Điều quan trọng là biết ngành đang ở "
                          "đoạn nào của chu kỳ.", PASTEL["vang"], ly_do)
    if tb_tt is not None and tb_tt >= 15 and (roe_tb is None or roe_tb >= 12):
        return ("Tăng trưởng", "Lợi nhuận tăng nhanh và hiệu quả dùng vốn tốt. Thường định giá cao hơn, nên rủi ro nằm "
                               "ở chỗ tăng trưởng chậm lại.", PASTEL["lime"], ly_do)
    if payout is not None and payout >= 40:
        return ("Cổ tức", "Chia phần lớn lợi nhuận cho cổ đông bằng tiền mặt. Hợp với người muốn dòng tiền đều, "
                          "thường tăng giá chậm hơn.", PASTEL["cyan"], ly_do)
    if (dao_dong is None or dao_dong < 25) and (no_gan is None or no_gan < 1.5):
        return ("Ổn định / phòng thủ", "Lợi nhuận ít biến động, nợ vừa phải. Thường ít bị ảnh hưởng khi thị trường "
                                       "xấu, nhưng cũng ít bứt phá.", PASTEL["hong"], ly_do)
    return ("Hỗn hợp", "Chưa nghiêng rõ về nhóm nào. Cần đọc thêm về hoạt động kinh doanh để hiểu rõ hơn.",
            PASTEL["tim"], ly_do)


# ---------------------------------------------------------------- 2. điểm mạnh / điểm yếu
def diem_manh_yeu(ty_so):
    """Danh sách (loại, câu), loại là 'manh' hoặc 'yeu'. Chỉ tạo câu khi có số liệu."""
    kq = []

    def cuoi(ten):
        return _cuoi(ty_so, ten)

    v = cuoi("ROE (%)")
    if v is not None:
        if v >= 15:
            kq.append(("manh", f"ROE {so_vn(v, 1)}%: dùng vốn của cổ đông hiệu quả"))
        elif v < 8:
            kq.append(("yeu", f"ROE {so_vn(v, 1)}% thấp: hiệu quả sử dụng vốn chưa cao"))
    s = _chuoi(ty_so, "Biên LN gộp (%)")
    if s is not None and len(s) >= 3:
        d = float(s.iloc[-1] - s.iloc[:-1].mean())
        if d >= 2:
            kq.append(("manh", f"Biên lợi nhuận gộp {so_vn(s.iloc[-1], 1)}%, cao hơn trung bình các năm trước: "
                               "dấu hiệu sức mạnh định giá hoặc kiểm soát chi phí tốt"))
        elif d <= -2:
            kq.append(("yeu", f"Biên lợi nhuận gộp {so_vn(s.iloc[-1], 1)}%, thấp hơn trung bình các năm trước: "
                              "biên đang bị thu hẹp"))
    v = cuoi("Biên LN ròng (%)")
    if v is not None:
        if v >= 10:
            kq.append(("manh", f"Biên lợi nhuận ròng {so_vn(v, 1)}%: giữ lại được nhiều lợi nhuận trên mỗi đồng doanh thu"))
        elif v < 3:
            kq.append(("yeu", f"Biên lợi nhuận ròng chỉ {so_vn(v, 1)}%: chi phí tăng nhẹ là lợi nhuận giảm mạnh"))
    v = cuoi("Nợ / VCSH (lần)")
    if v is not None:
        if v < 1:
            kq.append(("manh", f"Nợ / vốn chủ sở hữu {so_vn(v, 2)} lần: đòn bẩy thấp"))
        elif v > 2.5:
            kq.append(("yeu", f"Nợ / vốn chủ sở hữu {so_vn(v, 2)} lần: đòn bẩy cao, nhạy cảm với lãi suất"))
    v = cuoi("Nợ vay / VCSH (lần)")
    if v is not None and v > 1:
        kq.append(("yeu", f"Nợ vay gấp {so_vn(v, 2)} lần vốn chủ sở hữu: gánh lãi vay nặng"))
    v = cuoi("EBIT / Lãi vay (lần)")
    if v is not None:
        if v >= 5:
            kq.append(("manh", f"Lợi nhuận trước lãi vay gấp {so_vn(v, 1)} lần tiền lãi: trả lãi thoải mái"))
        elif v < 2:
            kq.append(("yeu", f"Lợi nhuận trước lãi vay chỉ gấp {so_vn(v, 1)} lần tiền lãi: áp lực trả lãi lớn"))
    v = cuoi("Thanh toán hiện hành (lần)")
    if v is not None:
        if v >= 1.5:
            kq.append(("manh", f"Thanh toán hiện hành {so_vn(v, 2)} lần: đủ tài sản ngắn hạn trả nợ ngắn hạn"))
        elif v < 1:
            kq.append(("yeu", f"Thanh toán hiện hành {so_vn(v, 2)} lần: tài sản ngắn hạn không đủ trả nợ ngắn hạn"))
    v = cuoi("CFO / LNST (lần)")
    if v is not None:
        if v >= 0.8:
            kq.append(("manh", f"Dòng tiền kinh doanh bằng {so_vn(v, 2)} lần lợi nhuận: lợi nhuận có tiền thật đi kèm"))
        elif v < 0.5:
            kq.append(("yeu", f"Dòng tiền kinh doanh chỉ bằng {so_vn(v, 2)} lần lợi nhuận: lãi chưa chuyển thành tiền"))
    v = cuoi("Tăng trưởng doanh thu (%)")
    if v is not None:
        if v >= 10:
            kq.append(("manh", f"Doanh thu tăng {so_vn(v, 1)}% so với năm trước"))
        elif v < 0:
            kq.append(("yeu", f"Doanh thu giảm {so_vn(abs(v), 1)}% so với năm trước"))
    return kq


# ---------------------------------------------------------------- 3. vị trí trong chu kỳ của chính doanh nghiệp
CHI_SO_CHU_KY = ("ROE (%)", "Biên LN ròng (%)", "Biên LN gộp (%)")


def chu_ky(ty_so):
    """Với mỗi chỉ số: giá trị hiện tại so với trung bình, thấp nhất, cao nhất của chính doanh nghiệp."""
    kq = []
    for ten in CHI_SO_CHU_KY:
        s = _chuoi(ty_so, ten)
        if s is None or len(s) < 4:
            continue
        hien, tb, lo, hi = float(s.iloc[-1]), float(s.mean()), float(s.min()), float(s.max())
        vt = (hien - lo) / (hi - lo) if hi > lo else 0.5
        nhan = "gần mức cao nhất" if vt >= 0.8 else "gần mức thấp nhất" if vt <= 0.2 else "ở khoảng giữa"
        kq.append({"ten": ten, "chuoi": s, "hien": hien, "tb": tb, "lo": lo, "hi": hi, "nhan": nhan})
    return kq


# ---------------------------------------------------------------- 4. so với thị trường
def _loi_suat(df, n):
    c = df["close"].dropna()
    return float((c.iloc[-1] / c.iloc[-1 - n] - 1) * 100) if len(c) > n else None


def so_voi_thi_truong(gia, vni):
    """Bảng lợi suất mã và VN-Index, nhận định xu hướng thị trường chung. vni có thể là None."""
    if vni is None or len(vni) < 60:
        return None, None
    hang = []
    for n, nhan in ((63, "3 tháng"), (126, "6 tháng"), (252, "12 tháng")):
        a, b = _loi_suat(gia, n), _loi_suat(vni, n)
        if a is not None and b is not None:
            hang.append({"Giai đoạn": nhan, "Mã (%)": a, "VN-Index (%)": b, "Chênh lệch (điểm %)": a - b})
    v = vni["close"]
    ma50 = v.rolling(50).mean().iloc[-1]
    ma200 = v.rolling(200).mean().iloc[-1] if len(v) >= 200 else None
    if ma200 is not None and v.iloc[-1] > ma50 and v.iloc[-1] > ma200:
        xu_huong = "Thị trường chung đang trong xu hướng tăng (VN-Index trên MA50 và MA200). Khi cả thị trường tăng, " \
                   "nhiều mã tăng theo nên cần so với VN-Index mới biết mã có thật sự mạnh."
    elif v.iloc[-1] < ma50 and (ma200 is None or v.iloc[-1] < ma200):
        xu_huong = "Thị trường chung đang yếu (VN-Index dưới MA50" + (" và MA200" if ma200 is not None else "") + \
                   "). Mã giữ được giá tốt hơn thị trường trong giai đoạn này thường đáng chú ý."
    else:
        xu_huong = "Thị trường chung đang đi ngang hoặc chưa rõ xu hướng."
    return pd.DataFrame(hang), xu_huong


def _bieu_do_so_sanh(ma, gia, vni):
    a = gia[["time", "close"]].copy()
    b = vni[["time", "close"]].copy()
    a["time"], b["time"] = pd.to_datetime(a["time"]).dt.normalize(), pd.to_datetime(b["time"]).dt.normalize()
    m = a.merge(b, on="time", suffixes=("_ma", "_vni")).dropna()
    if len(m) < 30:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["time"], y=m["close_ma"] / m["close_ma"].iloc[0] * 100, name=ma,
                             line=dict(color=MAU["tim"], width=3)))
    fig.add_trace(go.Scatter(x=m["time"], y=m["close_vni"] / m["close_vni"].iloc[0] * 100, name="VN-Index",
                             line=dict(color=MAU["hong"], width=2, dash="dot")))
    fig.update_yaxes(title="Quy về 100 ở đầu kỳ")
    return theme_plotly(fig, 320)


# ---------------------------------------------------------------- giao diện
CAU_HOI = [
    "Doanh nghiệp kiếm tiền từ đâu? Sản phẩm hoặc mảng nào chiếm phần lớn doanh thu và lợi nhuận?",
    "Đối thủ chính là ai? Doanh nghiệp hơn họ ở điểm nào, kém ở điểm nào?",
    "Doanh thu phụ thuộc vào ít khách hàng, ít nhà cung cấp hay một thị trường duy nhất không?",
    "Chính sách, lãi suất, giá hàng hoá hoặc tỷ giá nào tác động mạnh nhất tới ngành này?",
    "Ngành đang ở đoạn nào của chu kỳ (đang hồi phục, đang nóng, đang chậm lại)?",
    "Sắp tới có sự kiện nào đáng chú ý: kết quả kinh doanh quý, đại hội cổ đông, chia cổ tức, phát hành thêm, dự án lớn?",
    "Ban lãnh đạo và cổ đông lớn có đang mua hay bán cổ phiếu?",
]


def _the(mau, tieu_de, noi_dung):
    st.markdown(f"<div class='x10-card' style='background:{mau}'><b style='font-size:18px'>{tieu_de}</b><br>"
                f"{noi_dung}</div>", unsafe_allow_html=True)


def ve_tab_hoso(r):
    if not r:
        st.info("Bấm **Phân tích** ở thanh bên trái để xem hồ sơ doanh nghiệp.")
        return
    ma, ty_so, bctc, gia, vni = r["ma"], r["ty_so"], r["bctc"], r["gia"], r.get("vni")
    info = industry.thong_tin(ma)
    nganh = " › ".join(x for x in (info.get("icb1", ""), info.get("icb2", ""), info.get("icb3", "")) if x)

    _the(PASTEL["vang"], "Cách dùng tab này",
         "Bộ lọc khẩu vị chỉ giúp tìm <b>ứng viên để nghiên cứu</b>. Tab này giúp bạn hiểu doanh nghiệp trước khi quyết định. "
         "Lưu ý: các chỉ số lấy từ báo cáo tài chính theo năm, tức là <b>số đã xảy ra</b>. "
         "Tin tức và chính sách vĩ mô thì bạn cần tự tìm hiểu thêm (xem phần cuối).")

    st.subheader(f"{ma} làm trong ngành nào?")
    st.write((info.get("ten", "") + (f" · {info.get('san', '')}" if info.get("san") else "")) or ma)
    st.caption(f"Phân ngành ICB: {nganh}" if nganh else "Chưa có thông tin phân ngành cho mã này.")

    st.subheader("1. Doanh nghiệp thuộc nhóm nào?")
    nhom, mo_ta, mau, ly_do = phan_loai(ty_so, bctc)
    _the(mau, nhom, mo_ta)
    if ly_do:
        st.markdown("".join(f"<div class='x10-small' style='color:#3A3158;opacity:1'>• {x}</div>" for x in ly_do),
                    unsafe_allow_html=True)
    st.caption("Phân loại tự động theo quy ước tham khảo từ dữ liệu vài năm gần nhất, không phải kết luận. "
               "Bạn nên đối chiếu với hiểu biết của mình về doanh nghiệp.")

    st.subheader("2. Điểm mạnh và điểm yếu theo số liệu")
    ds = diem_manh_yeu(ty_so)
    if not ds:
        st.info("Chưa đủ số liệu tài chính để nhận xét.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Điểm mạnh**")
            if not any(l == "manh" for l, _ in ds):
                st.caption("Chưa thấy điểm mạnh nổi bật trong các chỉ số này.")
            for loai, t in ds:
                if loai == "manh":
                    st.markdown(f"<div class='x10-row'><span class='x10-tag' style='background:{MAU['lime']}'>Mạnh</span>"
                                f"<div>{t}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("**Điểm yếu cần để ý**")
            if not any(l == "yeu" for l, _ in ds):
                st.caption("Chưa thấy điểm yếu rõ trong các chỉ số này. Điều đó không có nghĩa là không có rủi ro.")
            for loai, t in ds:
                if loai == "yeu":
                    st.markdown(f"<div class='x10-row'><span class='x10-tag' style='background:#FF8FA3'>Yếu</span>"
                                f"<div>{t}</div></div>", unsafe_allow_html=True)

    st.subheader("3. Đang ở đâu trong chu kỳ của chính doanh nghiệp?")
    ck = chu_ky(ty_so)
    if not ck:
        st.info("Cần ít nhất 4 năm báo cáo tài chính để so sánh chu kỳ. Tăng 'Số năm BCTC' ở thanh bên nếu có.")
    else:
        cot = st.columns(len(ck))
        for c, m in zip(cot, ck):
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[str(x) for x in m["chuoi"].index], y=m["chuoi"].values, marker_color=MAU["tim"],
                                 name=m["ten"]))
            fig.add_hline(y=m["tb"], line_dash="dash", line_color=MAU["hong"],
                          annotation_text=f"TB {so_vn(m['tb'], 1)}", annotation_position="top left")
            c.markdown(f"**{m['ten']}**: hiện {so_vn(m['hien'], 1)}, {m['nhan']} "
                       f"(thấp nhất {so_vn(m['lo'], 1)}, cao nhất {so_vn(m['hi'], 1)})")
            c.plotly_chart(theme_plotly(fig, 240), use_container_width=True)
        st.caption("Chỉ số đang gần mức cao nhất của chính nó là lúc nên hỏi: điều gì giúp duy trì mức này, "
                   "và nếu ngành đổi chiều thì sao? Ngược lại, gần mức thấp nhất có thể là đáy chu kỳ hoặc dấu hiệu "
                   "doanh nghiệp yếu đi thật sự. Số liệu một mình không phân biệt được hai trường hợp này.")

    st.subheader("4. Mạnh hơn hay yếu hơn thị trường chung?")
    bang, xu_huong = so_voi_thi_truong(gia, vni)
    if bang is None or bang.empty:
        st.info("Chưa lấy được dữ liệu VN-Index nên chưa so sánh được với thị trường.")
    else:
        st.write(xu_huong)
        hien = bang.copy()
        for c in ("Mã (%)", "VN-Index (%)", "Chênh lệch (điểm %)"):
            hien[c] = hien[c].map(lambda x: so_vn(x, 1))
        st.dataframe(hien, hide_index=True, use_container_width=True)
        fig = _bieu_do_so_sanh(ma, gia, vni)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("5. Những câu bạn nên tự trả lời trước khi quyết định")
    st.markdown("".join(f"<div class='x10-row'><span class='x10-tag' style='background:{PASTEL['tim']}'>{i}</span>"
                        f"<div>{q}</div></div>" for i, q in enumerate(CAU_HOI, 1)), unsafe_allow_html=True)
    ten = info.get("ten") or ma
    link = [("Tin tức về " + ma, "https://news.google.com/search?q=" + quote(f"{ma} cổ phiếu") + "&hl=vi&gl=VN&ceid=VN:vi"),
            ("Báo cáo thường niên", "https://www.google.com/search?q=" + quote(f"{ten} báo cáo thường niên")),
            ("Chính sách ảnh hưởng ngành", "https://news.google.com/search?q=" + quote(f"{info.get('icb2') or ten} chính sách") +
             "&hl=vi&gl=VN&ceid=VN:vi")]
    st.markdown(" · ".join(f"[{t}]({u})" for t, u in link))
    st.text_area("Ghi chú của bạn về doanh nghiệp này", key=f"ghichu_{ma}", height=140,
                 placeholder="Ví dụ: mảng nào đang lớn nhanh, tin sắp tới, lý do bạn quan tâm...")
    st.caption("Ghi chú chỉ lưu trong lúc bạn mở trang, tải lại là mất. Hãy tự sao chép nếu cần giữ.")
    st.caption("Nội dung trong tab này chỉ để học và tham khảo, không phải khuyến nghị đầu tư.")