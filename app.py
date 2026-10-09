import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.data import lay_vnindex, STATEMENTS, LOI
from core.pipeline import phan_tich_ma, ngu_canh_tu_ket_qua, quet_nhieu_ma
from core.strategy import dong_pdf
from core.report import xuat_pdf
from core.profiles import TIEU_CHI, NHOM, KHAU_VI, cau_hinh_khau_vi, danh_gia, tom_tat
from core import industry
from core.dinhdang import so_vn
from core.theme import (ap_dung_theme, theme_plotly, tieu_de_trang, huong_dan_3_buoc, the_tin_hieu,
                        dong_tieu_chi, tag_trang_thai, thanh_phan_tram, MAU)

st.set_page_config(page_title="X10 Investment Lab", page_icon="📈", layout="wide")
ap_dung_theme()
tieu_de_trang()
st.caption("Dữ liệu: vnstock (giá, VN-Index) · vnfinancialdata (BCTC) · Phân ngành ICB từ vn-annual-report-miner")


@st.cache_data(ttl=3600, show_spinner=False)
def vni_cache(so_ngay):
    return lay_vnindex(so_ngay)


@st.cache_data(ttl=3600, show_spinner=False)
def ma_cache(ma, so_ngay, so_nam):
    return phan_tich_ma(ma, so_ngay, so_nam, vni_cache(so_ngay))


def dat_khau_vi(ma_kv):
    cfg = cau_hinh_khau_vi(ma_kv)
    for t in TIEU_CHI:
        k = t["key"]
        st.session_state[f"on_{k}"] = k in cfg
        if t["loai"] != "bool":
            st.session_state[f"val_{k}"] = float(cfg.get(k, t["mac_dinh"]))


def cau_hinh_hien_tai():
    cfg = {}
    for t in TIEU_CHI:
        k = t["key"]
        if st.session_state.get(f"on_{k}"):
            cfg[k] = True if t["loai"] == "bool" else float(st.session_state.get(f"val_{k}", t["mac_dinh"]))
    return cfg


if "kv" not in st.session_state:
    st.session_state["kv"] = "can_bang"
    dat_khau_vi("can_bang")

with st.sidebar:
    st.header("1. Khẩu vị đầu tư")
    st.selectbox("Bạn thuộc nhóm nào?", list(KHAU_VI), key="kv", format_func=lambda k: KHAU_VI[k]["ten"],
                 on_change=lambda: dat_khau_vi(st.session_state["kv"]))
    kv_info = KHAU_VI[st.session_state["kv"]]
    st.markdown(f"<div class='x10-card' style='background:{kv_info['mau']}55;padding:10px 14px'>"
                f"<b>{kv_info['mo_ta']}</b><br><span class='x10-small' style='color:#3A3158'>Phù hợp: {kv_info['phu_hop']}</span></div>",
                unsafe_allow_html=True)
    with st.expander("Tuỳ chỉnh tiêu chí lọc", expanded=st.session_state["kv"] == "tuy_chinh"):
        st.caption("Bật tiêu chí nào thì mã phải đạt tiêu chí đó. Sửa ngưỡng theo ý bạn.")
        for nhom in NHOM:
            st.markdown(f"**{nhom}**")
            for t in [x for x in TIEU_CHI if x["nhom"] == nhom]:
                k = t["key"]
                st.checkbox(t["nhan"], key=f"on_{k}", help=t["mo_ta"] or None)
                if t["loai"] != "bool":
                    st.number_input(f"Ngưỡng {t['nhan']}", key=f"val_{k}", min_value=float(t["toi_thieu"]),
                                    max_value=float(t["toi_da"]), step=float(t["buoc"]), format=f"%.{t['thap_phan']}f",
                                    disabled=not st.session_state.get(f"on_{k}"), label_visibility="collapsed")
                    st.caption(f"Đơn vị: {t['don_vi']}" if t["don_vi"] else " ")

    st.header("2. Chọn mã")
    ma = st.text_input("Mã cổ phiếu", "FPT").upper().strip()
    so_ngay = st.slider("Khoảng thời gian giá (ngày)", 365, 1825, 730, step=30)
    so_nam = st.slider("Số năm BCTC", 3, 10, 6)
    st.subheader("Hiển thị biểu đồ")
    hien_ma = st.multiselect("Đường trung bình", ["MA20", "MA50"], default=["MA20", "MA50"])
    hien_rsi = st.checkbox("Hiện RSI", True)
    hien_vol = st.checkbox("Hiện khối lượng", True)
    chay = st.button("Phân tích", type="primary", use_container_width=True)

huong_dan_3_buoc()

if chay:
    try:
        with st.spinner("Đang lấy dữ liệu giá, VN-Index và báo cáo tài chính..."):
            st.session_state["r"] = ma_cache(ma, so_ngay, so_nam)
            st.session_state.pop("pdf", None)
    except Exception as e:
        st.session_state.pop("r", None)
        st.error(f"Không lấy được dữ liệu cho mã {ma}: {e}")

r = st.session_state.get("r")
cfg = cau_hinh_hien_tai()
ten_kv = KHAU_VI[st.session_state["kv"]]["ten"]
tabs = st.tabs(["Tổng quan", "Hợp khẩu vị", "Kỹ thuật", "Báo cáo tài chính", "Tỷ số tài chính", "Quét thị trường"])

if r:
    ma, bctc, ty_so, gia, kq, xep = r["ma"], r["bctc"], r["ty_so"], r["gia"], r["kq"], r["xep"]
    thong_tin = industry.thong_tin(ma)
    ten_nganh = " · ".join(x for x in (thong_tin.get("ten", ""), thong_tin.get("icb2", "")) if x)
    kv = danh_gia(ngu_canh_tu_ket_qua(r), cfg)
    if not bctc:
        st.warning("Chưa có dữ liệu báo cáo tài chính. Điểm cơ bản dùng mức trung tính 50 và các tiêu chí cơ bản bị bỏ qua.")
        for k, v in LOI.items():
            st.caption(f"⚠ {v}")
with tabs[0]:
    if not r:
        st.info("Chọn khẩu vị và nhập mã ở thanh bên trái, rồi bấm **Phân tích**.")
    else:
        gia_dc = kq["Giá đóng cửa"]
        the_tin_hieu(ma, xep["tin_hieu"], xep["diem_tong"], xep["diem_ta"], xep["diem_fa"],
                     gia=f"{so_vn(gia_dc * 1000 if gia_dc < 1000 else gia_dc, 0)} đ", ten_nganh=ten_nganh)
        st.markdown(f"<div class='x10-card' style='background:{kv['mau']}'><b style='font-size:18px'>{kv['hang']}</b> "
                    f"· khẩu vị {ten_kv}<br>{tom_tat(ma, ten_kv, kv)}</div>", unsafe_allow_html=True)
        c = st.columns(4)
        c[0].metric("Điểm kỹ thuật (80%)", f"{xep['diem_ta']:.1f}")
        c[1].metric("Điểm cơ bản (20%)", f"{xep['diem_fa']:.1f}")
        c[2].metric("Điểm thống nhất", f"{xep['diem_tong']:.1f}")
        c[3].metric("GTGD 20 phiên", f"{so_vn(xep['gtgd'] / 1e9, 2)} tỷ")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bộ lọc MUA (cần đạt hết)")
            st.markdown("".join(dong_tieu_chi(n, t, ct) for n, t, ct in xep["dk_mua"]), unsafe_allow_html=True)
        with c2:
            st.subheader("Bộ lọc BÁN (một điều kiện là đủ)")
            st.markdown("".join(dong_tieu_chi(n, t, ct) for n, t, ct in xep["dk_ban"]), unsafe_allow_html=True)
        st.subheader("Chỉ số chính")
        st.dataframe({k: [so_vn(v, 2)] for k, v in kq.items()}, hide_index=True, use_container_width=True)

        b1, b2 = st.columns([1, 3])
        if b1.button("Tạo báo cáo PDF", type="primary"):
            with st.spinner("Đang dựng PDF..."):
                st.session_state["pdf"] = (ma, xuat_pdf(ma, gia, kq, round(xep["diem_tong"]), 100, dong_pdf(xep),
                                                       xep["tin_hieu"], bctc, ty_so, xep=xep, khau_vi=kv,
                                                       ten_khau_vi=ten_kv, ten_nganh=ten_nganh))
        pdf = st.session_state.get("pdf")
        if pdf and pdf[0] == ma:
            b2.download_button("Tải file PDF", data=pdf[1], file_name=f"BaoCao_{ma}.pdf", mime="application/pdf")
        st.caption("Tín hiệu định lượng phục vụ học tập, không phải khuyến nghị đầu tư.")

with tabs[1]:
    if not r:
        st.info("Bấm **Phân tích** trước để xem mã có hợp khẩu vị của bạn không.")
    else:
        st.subheader(f"{ma} và khẩu vị {ten_kv}")
        st.markdown(f"<div class='x10-card' style='background:{kv['mau']}'><b style='font-size:20px'>{kv['hang']}</b><br>"
                    f"{tom_tat(ma, ten_kv, kv)}"
                    f"{thanh_phan_tram(kv['ty_le'] or 0)}</div>", unsafe_allow_html=True)
        if not kv["dong"]:
            st.info("Hãy bật ít nhất một tiêu chí ở thanh bên (mục Tuỳ chỉnh tiêu chí lọc).")
        for nhom in NHOM:
            ds = [d for d in kv["dong"] if d["nhom"] == nhom]
            if ds:
                st.markdown(f"**{nhom}**")
                st.markdown("".join(
                    f"<div class='x10-row'>{tag_trang_thai(d['trang_thai'])}<div style='flex:1'><b>{d['nhan']}</b>"
                    f"<div class='x10-small' style='color:#6B6389;opacity:1'>Ngưỡng: {d['nguong']}</div></div>"
                    f"<div style='font-weight:700'>{d['gia_tri']}</div></div>" for d in ds), unsafe_allow_html=True)
        st.subheader("Mã này hợp khẩu vị nào nhất?")
        st.caption("So sánh nhanh với ngưỡng mặc định của từng khẩu vị có sẵn.")
        ctx = ngu_canh_tu_ket_qua(r)
        bang = []
        for k, v in KHAU_VI.items():
            if k == "tuy_chinh":
                continue
            kq_k = danh_gia(ctx, cau_hinh_khau_vi(k))
            bang.append({"Khẩu vị": v["ten"], "% hợp": round(kq_k["ty_le"] or 0), "Đạt": f"{kq_k['dat']}/{kq_k['dat'] + kq_k['khong']}",
                         "Mức hợp": kq_k["hang"]})
        bang.sort(key=lambda x: -x["% hợp"])
        st.dataframe(bang, hide_index=True, use_container_width=True,
                     column_config={"% hợp": st.column_config.ProgressColumn("% hợp", min_value=0, max_value=100, format="%d%%")})

with tabs[2]:
    if not r:
        st.info("Bấm **Phân tích** để xem biểu đồ.")
    else:
        hang = 1 + hien_rsi + hien_vol
        fig = make_subplots(rows=hang, cols=1, shared_xaxes=True, row_heights=[0.6] + [0.2] * (hang - 1), vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=gia["time"], open=gia["open"], high=gia["high"], low=gia["low"], close=gia["close"],
                                     name="Giá", increasing_line_color="#12B76A", decreasing_line_color="#FF4F6D"), row=1, col=1)
        mau_ma = {"MA20": MAU["hong"], "MA50": MAU["tim"]}
        for m in hien_ma:
            fig.add_trace(go.Scatter(x=gia["time"], y=gia[m], name=m, line=dict(color=mau_ma[m], width=2)), row=1, col=1)
        rr = 2
        if hien_rsi:
            fig.add_trace(go.Scatter(x=gia["time"], y=gia["RSI"], name="RSI", line=dict(color=MAU["cam"], width=2)), row=rr, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#E5254B", row=rr, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#078A4F", row=rr, col=1)
            rr += 1
        if hien_vol and "volume" in gia:
            fig.add_trace(go.Bar(x=gia["time"], y=gia["volume"], name="Khối lượng", marker_color=MAU["cyan"]), row=rr, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False)
        st.plotly_chart(theme_plotly(fig, 720), use_container_width=True)

with tabs[3]:
    if not r or not bctc:
        st.info("Không có dữ liệu BCTC cho mã này." if r else "Bấm **Phân tích** để xem báo cáo tài chính.")
    else:
        for k, ten in STATEMENTS.items():
            if k in bctc:
                st.subheader(ten)
                tim = st.text_input(f"Lọc chỉ tiêu ({ten})", key=f"loc_{k}", placeholder="vd: lãi, tài sản, nợ...")
                df = bctc[k]
                if tim:
                    df = df[df.index.astype(str).str.contains(tim, case=False, na=False)]
                st.dataframe(df.style.format("{:,.0f}"), use_container_width=True, height=380)

with tabs[4]:
    if not r or ty_so.empty:
        st.info("Chưa tính được tỷ số (thiếu BCTC)." if r else "Bấm **Phân tích** để xem tỷ số tài chính.")
    else:
        st.dataframe(ty_so.style.format("{:,.2f}"), use_container_width=True)
        chon = st.selectbox("Xem biểu đồ tỷ số", list(ty_so.index))
        s = ty_so.loc[chon].dropna()
        f2 = go.Figure(go.Bar(x=[str(i) for i in s.index], y=s.values, marker_color=MAU["tim"]))
        f2.update_layout(title=chon)
        st.plotly_chart(theme_plotly(f2, 350), use_container_width=True)

with tabs[5]:
    st.subheader("Tìm mã hợp khẩu vị của bạn")
    st.caption(f"Quét theo khẩu vị đang chọn: **{ten_kv}** ({len(cfg)} tiêu chí bật). Quét càng nhiều mã càng lâu.")
    q1, q2 = st.columns(2)
    nganh = q1.multiselect("Ngành (ICB cấp 1)", industry.nganh_cap1())
    san = q2.multiselect("Sàn", ["HOSE", "HNX", "UPCOM"], default=["HOSE", "HNX"])
    nhap = st.text_area("Hoặc nhập danh sách mã (cách nhau bằng dấu phẩy)", placeholder="FPT, VNM, HPG, MWG")
    toi_da = st.slider("Số mã tối đa", 5, 60, 20)
    if st.button("Quét theo khẩu vị", type="primary"):
        if not cfg:
            st.warning("Bạn chưa bật tiêu chí nào. Hãy chọn khẩu vị hoặc bật tiêu chí ở thanh bên.")
        else:
            ds = [m.strip().upper() for m in nhap.replace("\n", ",").split(",") if m.strip()] or \
                 industry.loc_ma(nganh or None, None, san or None, toi_da)
            ds = ds[:toi_da]
            if not ds:
                st.warning("Không có mã nào khớp bộ lọc ngành và sàn.")
            else:
                bar = st.progress(0.0, text="Đang quét...")
                vni = vni_cache(so_ngay)
                st.session_state["quet"] = quet_nhieu_ma(
                    ds, so_ngay, so_nam, vni, cfg,
                    tien_do=lambda i, n, m: bar.progress(i / n, text=f"Đang quét {m} ({i + 1}/{n})" if m else "Xong"))
                bar.empty()
    if st.session_state.get("quet") is not None:
        df = st.session_state["quet"]
        st.dataframe(df, hide_index=True, use_container_width=True,
                     column_config={"% hợp khẩu vị": st.column_config.ProgressColumn("% hợp khẩu vị", min_value=0, max_value=100, format="%d%%")})
        st.download_button("Tải kết quả CSV", df.to_csv(index=False).encode("utf-8-sig"), "quet_khau_vi.csv", "text/csv")