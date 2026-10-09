import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.data import lay_gia, lay_bctc, lay_ratio, lay_vnindex, STATEMENTS
from core.analysis import phan_tich, tinh_ty_so
from core.strategy import danh_gia_x10, dong_pdf
from core.report import xuat_pdf

st.set_page_config(page_title="Phân tích cơ hội đầu tư cổ phiếu", page_icon="📈", layout="wide")
st.markdown("<style>.block-container{padding-top:1.5rem} div[data-testid='stMetric']{background:#f4f6fa;"
            "padding:10px 14px;border-radius:10px}</style>", unsafe_allow_html=True)
st.title("📈 Hệ thống phân tích cơ hội đầu tư cổ phiếu")
st.caption("Dữ liệu: vnstock (giá, VN-Index) · vnfinancialdata (BCTC HSX/HNX) · Bộ lọc tham khảo X10 Investment Lab")


@st.cache_data(ttl=3600, show_spinner=False)
def tai(ma, so_ngay, so_nam):
    return lay_gia(ma, so_ngay), lay_ratio(ma), lay_bctc(ma, so_nam), lay_vnindex(so_ngay)


with st.sidebar:
    st.header("Bộ lọc")
    ma = st.text_input("Mã cổ phiếu", "FPT").upper().strip()
    so_ngay = st.slider("Khoảng thời gian giá (ngày)", 365, 1825, 730, step=30)
    so_nam = st.slider("Số năm BCTC", 3, 10, 6)
    st.subheader("Hiển thị biểu đồ")
    hien_ma = st.multiselect("Đường trung bình", ["MA20", "MA50"], default=["MA20", "MA50"])
    hien_rsi = st.checkbox("Hiện RSI", True)
    hien_vol = st.checkbox("Hiện khối lượng", True)
    chay = st.button("Phân tích", type="primary", use_container_width=True)

if chay:
    try:
        with st.spinner("Đang lấy dữ liệu giá, VN-Index và báo cáo tài chính..."):
            gia0, ratio, bctc, vni = tai(ma, so_ngay, so_nam)
            ty_so = tinh_ty_so(bctc)
            res = phan_tich(gia0, ratio, ty_so)
            xep = danh_gia_x10(res[0], res[1], ty_so, vni)
        st.session_state["res"] = (ma, bctc, ty_so, res[0], res[1], xep)
    except Exception as e:
        st.session_state.pop("res", None)
        st.error(f"Không lấy được dữ liệu cho mã {ma}: {e}")

if "res" not in st.session_state:
    st.info("Nhập mã cổ phiếu ở thanh bên trái rồi bấm **Phân tích**.")
else:
    ma, bctc, ty_so, gia, kq, xep = st.session_state["res"]
    if not bctc:
        st.warning("Chưa có dữ liệu báo cáo tài chính (vnfinancialdata). Điểm cơ bản dùng mức trung tính 50.")

    tab1, tab2, tab3, tab4 = st.tabs(["Tổng quan", "Kỹ thuật", "Báo cáo tài chính", "Tỷ số tài chính"])

    with tab1:
        tin_hieu = xep["tin_hieu"]
        hop = {"MUA": st.success, "THEO DÕI": st.warning, "BÁN / TRÁNH": st.error}
        hop[tin_hieu](f"Tín hiệu: {tin_hieu}  ·  Điểm thống nhất {xep['diem_tong']:.1f}/100")
        c = st.columns(4)
        c[0].metric("Điểm kỹ thuật (80%)", f"{xep['diem_ta']:.1f}")
        c[1].metric("Điểm cơ bản (20%)", f"{xep['diem_fa']:.1f}")
        c[2].metric("Điểm thống nhất", f"{xep['diem_tong']:.1f}")
        c[3].metric("GTGD 20 phiên", f"{xep['gtgd'] / 1e9:,.2f} tỷ")
        if not xep["co_fa"]:
            st.caption("Thiếu BCTC nên điểm cơ bản lấy mức trung tính 50.")

        icon = {"Đạt": "✅", "Không đạt": "❌", "Kích hoạt": "🚨", "Không": "✅", "N/A": "➖"}
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bộ lọc MUA (cần đạt hết)")
            for ten, tt, ct in xep["dk_mua"]:
                st.write(f"{icon[tt]} **{ten}**: {ct}")
        with c2:
            st.subheader("Bộ lọc BÁN (một điều kiện là đủ)")
            for ten, tt, ct in xep["dk_ban"]:
                st.write(f"{icon[tt]} **{ten}**: {ct}")

        st.subheader("Chỉ số chính")
        st.table({k: [f"{v:,.2f}"] for k, v in kq.items()})
        st.download_button("📄 Tải báo cáo PDF",
                           data=xuat_pdf(ma, gia, kq, round(xep["diem_tong"]), 100, dong_pdf(xep),
                                         tin_hieu, bctc, ty_so),
                           file_name=f"BaoCao_{ma}.pdf", mime="application/pdf", type="primary")
        st.caption("Tín hiệu định lượng phục vụ học tập, không phải khuyến nghị đầu tư.")

    with tab2:
        hang = 1 + hien_rsi + hien_vol
        fig = make_subplots(rows=hang, cols=1, shared_xaxes=True, row_heights=[0.6] + [0.2] * (hang - 1),
                            vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=gia["time"], open=gia["open"], high=gia["high"], low=gia["low"],
                                     close=gia["close"], name="Giá"), row=1, col=1)
        for m in hien_ma:
            fig.add_trace(go.Scatter(x=gia["time"], y=gia[m], name=m), row=1, col=1)
        r = 2
        if hien_rsi:
            fig.add_trace(go.Scatter(x=gia["time"], y=gia["RSI"], name="RSI"), row=r, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=r, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=r, col=1)
            r += 1
        if hien_vol and "volume" in gia:
            fig.add_trace(go.Bar(x=gia["time"], y=gia["volume"], name="Khối lượng"), row=r, col=1)
        fig.update_layout(height=700, xaxis_rangeslider_visible=False, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        if not bctc:
            st.info("Không có dữ liệu BCTC cho mã này.")
        for k, ten in STATEMENTS.items():
            if k in bctc:
                st.subheader(ten)
                tim = st.text_input(f"Lọc chỉ tiêu ({ten})", key=f"loc_{k}", placeholder="vd: lãi, tài sản, nợ...")
                df = bctc[k]
                if tim:
                    df = df[df.index.astype(str).str.contains(tim, case=False, na=False)]
                st.dataframe(df.style.format("{:,.0f}"), use_container_width=True, height=380)

    with tab4:
        if ty_so.empty:
            st.info("Chưa tính được tỷ số (thiếu BCTC).")
        else:
            st.dataframe(ty_so.style.format("{:,.2f}"), use_container_width=True)
            chon = st.selectbox("Xem biểu đồ tỷ số", list(ty_so.index))
            s = ty_so.loc[chon].dropna()
            f2 = go.Figure(go.Bar(x=[str(i) for i in s.index], y=s.values))
            f2.update_layout(height=350, title=chon)
            st.plotly_chart(f2, use_container_width=True)