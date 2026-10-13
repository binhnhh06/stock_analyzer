"""Tab "Hiểu doanh nghiệp": phân loại, điểm mạnh/yếu, vị trí chu kỳ, dòng tiền cổ tức, so với thị trường và sổ tay luận điểm đầu tư."""

from urllib.parse import quote
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.analysis import lay_dong
from core.dinhdang import so_vn
from core.theme import MAU, PASTEL, theme_plotly
from core import industry
from core.data import lay_lich_su_co_tuc


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

    if tb_tt is not None:
        ly_do.append(f"Lợi nhuận sau thuế tăng trung bình {so_vn(tb_tt, 1)}%/năm trong 3 năm gần nhất")
    if dao_dong is not None:
        ly_do.append(f"Tăng trưởng lợi nhuận dao động khoảng ±{so_vn(dao_dong, 0)} điểm % giữa các năm")
    if co_lo:
        ly_do.append("Có năm lỗ hoặc lãi bằng 0 trong 6 năm gần nhất")
    if roe_tb is not None:
        ly_do.append(f"ROE trung bình 3 năm: {so_vn(roe_tb, 1)}%")
    if payout is not None:
        ly_do.append(f"Chi trả cổ tức tiền mặt khoảng {so_vn(payout, 0)}% lợi nhuận (trung bình 3 năm)")

    if co_lo or (dao_dong is not None and dao_dong > 50):
        return ("Chu kỳ", "Lợi nhuận lên xuống mạnh theo từng giai đoạn của ngành. Điều quan trọng là biết ngành đang ở đoạn nào của chu kỳ.", PASTEL["vang"], ly_do)
    if tb_tt is not None and tb_tt >= 15 and (roe_tb is None or roe_tb >= 12):
        return ("Tăng trưởng", "Lợi nhuận tăng nhanh và hiệu quả dùng vốn tốt. Thường định giá cao hơn, nên rủi ro nằm ở chỗ tăng trưởng chậm lại.", PASTEL["lime"], ly_do)
    if payout is not None and payout >= 40:
        return ("Cổ tức & Phòng thủ", "Chia phần lớn lợi nhuận cho cổ đông bằng tiền mặt. Hợp với người muốn dòng tiền đều đặn.", PASTEL["cyan"], ly_do)
    return ("Ổn định", "Lợi nhuận ít biến động, nợ vừa phải, thích hợp nắm giữ dài hạn.", PASTEL["hong"], ly_do)


# ---------------------------------------------------------------- 2. điểm mạnh / điểm yếu
def diem_manh_yeu(ty_so):
    kq = []

    def cuoi(ten):
        return _cuoi(ty_so, ten)

    v = cuoi("ROE (%)")
    if v is not None:
        if v >= 15:
            kq.append(("manh", f"ROE {so_vn(v, 1)}%: Dùng vốn của cổ đông hiệu quả"))
        elif v < 8:
            kq.append(("yeu", f"ROE {so_vn(v, 1)}% thấp: Hiệu quả sử dụng vốn chưa cao"))
    
    v = cuoi("CFO / LNST (lần)")
    if v is not None:
        if v >= 0.8:
            kq.append(("manh", f"Dòng tiền kinh doanh bằng {so_vn(v, 2)} lần lợi nhuận: Lợi nhuận có tiền mặt thật đi kèm"))
        elif v < 0.5:
            kq.append(("yeu", f"Dòng tiền kinh doanh chỉ bằng {so_vn(v, 2)} lần lợi nhuận: Lợi nhuận trên giấy, chưa chuyển thành tiền mặt"))

    v = cuoi("Nợ vay / VCSH (lần)")
    if v is not None and v > 1:
        kq.append(("yeu", f"Nợ vay gấp {so_vn(v, 2)} lần vốn chủ sở hữu: Áp lực trả lãi vay lớn"))
        
    return kq


# ---------------------------------------------------------------- 3. vị trí trong chu kỳ của chính doanh nghiệp
CHI_SO_CHU_KY = ("ROE (%)", "Biên LN ròng (%)", "Biên LN gộp (%)")


def chu_ky(ty_so):
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
        xu_huong = "Thị trường chung đang trong xu hướng tăng. Mã giữ được đà tăng vượt trội so với VN-Index thể hiện sức mạnh nội tại tốt."
    else:
        xu_huong = "Thị trường chung đang biến động/điều chỉnh. Các mã giữ giá tốt hơn thị trường thường là điểm sáng đáng nghiên cứu."
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


# ---------------------------------------------------------------- giao diện hiển thị
def _the(mau, tieu_de, noi_dung):
    st.markdown(f"<div class='x10-card' style='background:{mau}'><b style='font-size:18px'>{tieu_de}</b><br>"
                f"{noi_dung}</div>", unsafe_allow_html=True)


def ve_tab_hoso(r):
    if not r:
        st.info("Bấm **Phân tích** ở thanh bên trái để xem hồ sơ chuyên sâu doanh nghiệp.")
        return
        
    ma, ty_so, bctc, gia, vni = r["ma"], r["ty_so"], r["bctc"], r["gia"], r.get("vni")
    info = industry.thong_tin(ma)
    nganh = " › ".join(x for x in (info.get("icb1", ""), info.get("icb2", ""), info.get("icb3", "")) if x)

    # 1. Tuyên ngôn nghiên cứu thực chiến
    _the(PASTEL["vang"], "Tư duy Nghiên cứu Chuyên sâu & Bản chất Doanh nghiệp",
         "Báo cáo tài chính luôn có độ trễ và các chỉ số chỉ phản ánh quá khứ. Tab này giúp bạn thấu hiểu chuỗi giá trị, "
         "kiểm tra dòng tiền cổ tức thực tế, định vị chu kỳ kinh doanh và tự xây dựng sổ tay luận điểm đầu tư dài hạn thay vì mua bán theo cảm tính.")

    st.subheader(f"🏢 Ngành & Mô hình kinh doanh: {ma}")
    st.write((info.get("ten", "") + (f" · {info.get('san', '')}" if info.get("san") else "")) or ma)
    st.caption(f"Phân ngành ICB: {nganh}" if nganh else "Chưa có thông tin phân ngành.")

    # 2. Phân loại doanh nghiệp
    st.subheader("1. Doanh nghiệp thuộc nhóm nào?")
    nhom, mo_ta, mau, ly_do = phan_loai(ty_so, bctc)
    _the(mau, nhom, mo_ta)
    if ly_do:
        st.markdown("".join(f"<div class='x10-small' style='color:#3A3158;opacity:1'>• {x}</div>" for x in ly_do),
                    unsafe_allow_html=True)

    # 3. Trục Cổ tức tiền mặt & Dòng tiền thực tế (Trọng tâm phân bổ vốn)
    st.subheader("2. Dòng tiền thực tế & Cổ tức Tiền mặt (Trục phân bổ vốn)")
    st.caption("Doanh nghiệp tốt phải tạo ra tiền mặt thuần từ hoạt động kinh doanh (CFO) vượt trội so với lợi nhuận kế toán, đồng thời duy trì truyền thống chia cổ tức tiền mặt đều đặn.")
    
    col_cf1, col_cf2 = st.columns(2)
    with col_cf1:
        if ty_so is not None and "Chi trả cổ tức / LNST (%)" in ty_so.index:
            s_ct = ty_so.loc["Chi trả cổ tức / LNST (%)"].dropna()
            if not s_ct.empty:
                f_ct = go.Figure(go.Bar(x=[str(x) for x in s_ct.index], y=s_ct.values, marker_color=MAU["cyan"]))
                f_ct.update_layout(title="Tỷ lệ chi trả cổ tức / LNST (%)", yaxis_title="%", height=260)
                st.plotly_chart(theme_plotly(f_ct, 260), use_container_width=True)
    with col_cf2:
        if ty_so is not None and "CFO / LNST (lần)" in ty_so.index:
            s_cfo = ty_so.loc["CFO / LNST (lần)"].dropna()
            if not s_cfo.empty:
                f_cfo = go.Figure(go.Bar(x=[str(x) for x in s_cfo.index], y=s_cfo.values, marker_color=MAU["tim"]))
                f_cfo.update_layout(title="Chất lượng lợi nhuận (CFO / LNST - Lãi thật hay giả)", yaxis_title="Lần", height=260)
                st.plotly_chart(theme_plotly(f_cfo, 260), use_container_width=True)

  # 4. Đánh giá Dòng tiền Cổ tức & Hình thức chi trả (Tiền mặt hay Cổ phiếu)
    st.subheader("🗓️ Đánh giá Dòng tiền Cổ tức & Hình thức Chi trả")
    st.caption("Nhận diện chính sách phân phối lợi nhuận của doanh nghiệp: chia tiền mặt (dòng tiền thật) hay chia cổ phiếu (tăng vốn/pha loãng).")

    # Phân tích thông minh dựa trên dữ liệu tỷ số
    if ty_so is not None and "Chi trả cổ tức / LNST (%)" in ty_so.index:
        s_ct_nam = ty_so.loc["Chi trả cổ tức / LNST (%)"].dropna()
        if not s_ct_nam.empty:
            tb_payout = s_ct_nam.mean()
            
            # Đánh giá thông minh theo mức độ chi trả
            if tb_payout >= 50:
                nhan_xet_loai = f"Doanh nghiệp thuộc nhóm **chi trả cổ tức rất cao (trung bình {so_vn(tb_payout, 1)}% LNST)**. Thường là các doanh nghiệp đầu ngành, ít nhu cầu đầu tư mở rộng tài sản cố định lớn, dùng dòng tiền thặng dư để chia thưởng lớn cho cổ đông bằng tiền mặt."
                mau_card = PASTEL["cyan"]
            elif tb_payout > 0:
                nhan_xet_loai = f"Doanh nghiệp có tỷ lệ **chi trả cổ tức đều đặn (trung bình {so_vn(tb_payout, 1)}% LNST)**. Lợi nhuận được phân bổ hài hòa giữa việc giữ lại tái đầu tư cho tăng trưởng và chia một phần cho cổ đông."
                mau_card = PASTEL["lime"]
            else:
                nhan_xet_loai = "Doanh nghiệp **giữ lại gần như toàn bộ lợi nhuận** để tái đầu tư, mở rộng dự án hoặc ưu tiên chia cổ phiếu thưởng/phát hành thêm thay vì chia tiền mặt. Cần lưu ý rủi ro pha loãng cổ phiếu."
                mau_card = PASTEL["vang"]

            st.markdown(f"""
            <div class='x10-card' style='background:{mau_card}'>
                <b>🔍 Nhận định chuyên sâu về chính sách cổ tức của {ma}:</b><br>
                - {nhan_xet_loai}<br>
                - <i>Lời khuyên thực chiến:</i> Hãy kiểm tra kỹ xem doanh nghiệp chia bằng <b>tiền mặt</b> (tạo dòng tiền thụ động) hay chia bằng <b>cổ phiếu</b> (làm tăng số lượng lưu hành, đòi hỏi doanh nghiệp phải tăng trưởng lợi nhuận tương ứng nếu không muốn bị suy giảm EPS).
            </div>
            """, unsafe_allow_html=True)

    # 4. Điểm mạnh và điểm yếu cốt lõi
    st.subheader("3. Điểm mạnh & Điểm yếu từ số liệu")
    ds = diem_manh_yeu(ty_so)
    if not ds:
        st.info("Chưa đủ số liệu tài chính để nhận xét.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Điểm mạnh cốt lõi**")
            for loai, t in ds:
                if loai == "manh":
                    st.markdown(f"<div class='x10-row'><span class='x10-tag' style='background:{MAU['lime']}'>Mạnh</span>"
                                f"<div>{t}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("**Rủi ro / Điểm yếu cần lưu ý**")
            for loai, t in ds:
                if loai == "yeu":
                    st.markdown(f"<div class='x10-row'><span class='x10-tag' style='background:#FF8FA3'>Yếu</span>"
                                f"<div>{t}</div></div>", unsafe_allow_html=True)

    # 5. Vị trí trong chu kỳ của chính doanh nghiệp
    st.subheader("4. Vị trí trong chu kỳ của chính doanh nghiệp")
    ck = chu_ky(ty_so)
    if not ck:
        st.info("Cần ít nhất 4 năm báo cáo tài chính để so sánh chu kỳ.")
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

    # 6. So với thị trường chung
    st.subheader("5. Sức mạnh giá so với thị trường chung")
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

    # 7. Sổ tay Luận điểm Đầu tư Cá nhân (Investment Thesis Journal)
    st.subheader("📝 Sổ tay Luận điểm Đầu tư Cá nhân (Investment Thesis)")
    st.markdown("Thay vì mua bán theo bảng điện, hãy ghi lại luận điểm cốt lõi của bạn để kiểm chứng qua từng quý:")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f"""
        **Gợi ý cấu trúc luận điểm nắm giữ {ma}:**
        - *Động lực tăng trưởng:* Doanh nghiệp hưởng lợi từ chính sách, dự án hay xu hướng vĩ mô nào?
        - *Biên an toàn:* Định giá hiện tại và tỷ suất cổ tức tiền mặt đã đủ hấp dẫn để phòng thủ chưa?
        - *Điểm quản trị rủi ro:* Yếu tố nào xuất hiện sẽ buộc bạn phải bán ra cắt lỗ?
        """)
    with col_t2:
        st.text_area(
            f"Nhật ký luận điểm đầu tư cho {ma}",
            key=f"thesis_{ma}",
            height=150,
            placeholder="Ví dụ: Kỳ vọng phục hồi chu kỳ ngành, cổ tức tiền mặt đều đặn, rủi ro cần theo dõi là chi phí đầu vào..."
        )
        st.caption("Sổ tay tự động lưu trong phiên giúp duy trì kỷ luật nắm giữ dài hạn.")

    ten = info.get("ten") or ma
    link = [("Báo cáo thường niên / Cổ đông " + ma, "https://www.google.com/search?q=" + quote(f"{ten} báo cáo thường niên đại hội cổ đông")),
            ("Tin tức & Sự kiện mới nhất", "https://news.google.com/search?q=" + quote(f"{ma} cổ phiếu") + "&hl=vi&gl=VN&ceid=VN:vi"),
            ("Chính sách ảnh hưởng ngành", "https://news.google.com/search?q=" + quote(f"{info.get('icb2') or ten} chính sách vĩ mô") + "&hl=vi&gl=VN&ceid=VN:vi")]
    st.markdown(" · ".join(f"[{t}]({u})" for t, u in link)) 

# 6. Bổ sung: Phân tích so sánh cùng ngành (Sector Benchmark)
    st.subheader("🏭 So sánh vị thế cùng ngành")
    st.caption("Đánh giá nhanh doanh nghiệp có thực sự vượt trội hay đang thua kém các đối thủ lớn trong cùng nhóm ngành ICB.")
    
    thong_tin_nganh = industry.thong_tin(ma)
    icb2_nganh = thong_tin_nganh.get("icb2", "")
    
    if icb2_nganh:
        st.markdown(f"""
        <div class='x10-card' style='background:{PASTEL["tim"]}'>
            <b>Góc nhìn tương quan ngành ({icb2_nganh}):</b><br>
            - Để đánh giá chính xác sức mạnh của <b>{ma}</b>, hãy so sánh các chỉ số cốt lõi (như Biên lợi nhuận gộp, ROE, Tốc độ tăng trưởng) 
            với các doanh nghiệp đầu ngành khác cùng phân khúc.<br>
            - Tránh đánh giá một mã cổ phiếu đơn lẻ mà bỏ qua xu hướng chung của cả ngành (ví dụ: khi ngành đi xuống, các doanh nghiệp đều bị ảnh hưởng biên lợi nhuận).
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Chưa đủ thông tin phân ngành chi tiết để so sánh trực tiếp.")

    # 7. Bổ sung: Kho tài liệu chính thống (One-Click Documents)
    st.subheader("📚 Kho tài liệu chính thống (Tài tài liệu một-chạm)")
    st.caption("Tổng hợp sẵn các đường dẫn trực tiếp đến tài liệu quan trọng của doanh nghiệp. Bạn chỉ cần click là mở ngay, không cần tìm kiếm thủ công.")
    
    ten_dn = info.get("ten") or ma
    
    col_tl1, col_tl2 = st.columns(2)
    with col_tl1:
        st.markdown(f"- 📄 **[Báo cáo Tài chính Kiểm toán & Quý](https://s.cafef.vn/tra-cuu-chung-khoan-3-{ma.lower()}.chn)**")
        st.markdown(f"- 📋 **[Báo cáo Thường niên](https://www.google.com/search?q={quote(ten_dn + ' báo cáo thường niên file pdf site:cafef.vn OR site:vietstock.vn')})**")
    with col_tl2:
        st.markdown(f"- 🗳️ **[Tài liệu Đại hội Cổ Đông](https://www.google.com/search?q={quote(ten_dn + ' tài liệu đại hội đồng cổ đông site:cafef.vn OR site:vietstock.vn')})**")
        st.markdown(f"- 📜 **[Điều lệ & Bản cáo bạch](https://www.google.com/search?q={quote(ten_dn + ' điều lệ công ty bản cáo bạch')})**")