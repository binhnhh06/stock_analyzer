import streamlit as st

MAU = {
    "muc": "#1B1233", "nen": "#F4EFFF", "trang": "#FFFFFF",
    "tim": "#6C3BFF", "tim_dam": "#5B2EFF", "hong": "#FF4F9A", "lime": "#B8F13C",
    "cyan": "#22D3EE", "vang": "#FFD43B", "cam": "#FF8A3D", "do": "#E5254B",
    "xanh_la": "#078A4F", "chu_mo": "#6B6389", "vien": "#DCCFFB",
}
DAY_MAU = [MAU["tim"], MAU["hong"], MAU["cyan"], MAU["cam"], MAU["lime"], MAU["vang"]]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp [data-testid="stMarkdownContainer"] {font-family:'Be Vietnam Pro',system-ui,sans-serif;}
[data-testid="stIconMaterial"], span.material-icons, span.material-symbols-rounded {font-family:'Material Symbols Rounded','Material Icons' !important;}
.stApp{background:#F4EFFF;color:#1B1233}
.block-container{padding-top:1.2rem;max-width:1280px}
header[data-testid="stHeader"]{background:transparent}
h1,h2,h3,h4{font-weight:800;letter-spacing:-0.01em;color:#1B1233}
[data-testid="stSidebar"]{background:#FFFFFF;border-right:2px solid #1B1233}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#6C3BFF}
[data-testid="stMetric"]{background:#fff;border:2px solid #1B1233;border-radius:18px;padding:12px 16px}
[data-testid="stMetricLabel"]{font-weight:600;color:#3A3158}
[data-testid="stMetricValue"]{font-weight:800}
[data-testid="stHorizontalBlock"]>div:nth-child(4n+1) [data-testid="stMetric"]{background:#DDF9A4}
[data-testid="stHorizontalBlock"]>div:nth-child(4n+2) [data-testid="stMetric"]{background:#FFD0E5}
[data-testid="stHorizontalBlock"]>div:nth-child(4n+3) [data-testid="stMetric"]{background:#C6F3FC}
[data-testid="stHorizontalBlock"]>div:nth-child(4n+4) [data-testid="stMetric"]{background:#FFE9A3}
.stButton>button,.stDownloadButton>button{border:2px solid #1B1233;border-radius:14px;font-weight:800;color:#1B1233;background:#fff;box-shadow:3px 3px 0 #1B1233;transition:transform .08s,box-shadow .08s}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translate(-1px,-1px);box-shadow:5px 5px 0 #1B1233;border-color:#1B1233;color:#1B1233}
.stButton>button:active,.stDownloadButton>button:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #1B1233}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"],button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primary"]:hover{background:#FF4F9A;color:#1B1233}
button[data-baseweb="tab"]{font-weight:700;font-size:15px}
button[data-baseweb="tab"][aria-selected="true"]{color:#6C3BFF}
[data-baseweb="tab-highlight"]{background:#6C3BFF;height:4px;border-radius:2px}
[data-testid="stAlert"]{border:2px solid #1B1233;border-radius:16px}
[data-testid="stExpander"]{border:2px solid #1B1233;border-radius:16px;background:#fff}
[data-testid="stDataFrame"]{border:2px solid #1B1233;border-radius:14px;overflow:hidden}
.x10-hero{display:flex;align-items:center;gap:14px;margin-bottom:6px}
.x10-logo{width:52px;height:52px;border-radius:16px;background:#6C3BFF;border:2px solid #1B1233;box-shadow:3px 3px 0 #1B1233;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#B8F13C}
.x10-title{font-size:26px;font-weight:800;line-height:30px;color:#1B1233}
.x10-sub{font-size:13px;color:#6B6389}
.x10-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;background:#FFD43B;border:2px solid #1B1233;box-shadow:4px 4px 0 #1B1233;border-radius:20px;padding:14px 18px;margin:12px 0 18px 0}
.x10-step{display:flex;align-items:center;gap:10px;font-size:14px;line-height:19px}
.x10-num{width:32px;height:32px;border-radius:50%;border:2px solid #1B1233;display:flex;align-items:center;justify-content:center;font-weight:800;flex:none}
.x10-signal{background:linear-gradient(145deg,#5B2EFF 0%,#9B3BFF 60%,#D13BFF 100%);color:#fff;border:2px solid #1B1233;box-shadow:5px 5px 0 #1B1233;border-radius:24px;padding:18px 22px;display:flex;flex-wrap:wrap;gap:18px;align-items:center;justify-content:space-between;margin-bottom:14px}
.x10-chip{display:inline-block;padding:6px 16px;border-radius:12px;border:2px solid #1B1233;font-weight:800;letter-spacing:1px;color:#1B1233}
.x10-big{font-size:34px;font-weight:800;line-height:38px}
.x10-small{font-size:12px;opacity:.85}
.x10-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:2px solid #EFE8FF;font-size:14px}
.x10-tag{display:inline-block;padding:2px 10px;border-radius:8px;border:1.5px solid #1B1233;font-size:12px;font-weight:800;color:#1B1233;white-space:nowrap}
.x10-card{background:#fff;border:2px solid #1B1233;border-radius:20px;padding:16px 18px;margin-bottom:12px}
.x10-bar{height:10px;border-radius:5px;background:#fff;border:1.5px solid #1B1233;overflow:hidden;margin-top:8px}
.x10-bar>div{height:100%;background:#1B1233}
"""


def ap_dung_theme():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def theme_plotly(fig, cao=None):
    fig.update_layout(
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Be Vietnam Pro, system-ui, sans-serif", color=MAU["muc"], size=13),
        colorway=DAY_MAU, margin=dict(t=30, l=10, r=10, b=10),
        legend=dict(orientation="h", y=1.04, x=0),
    )
    fig.update_xaxes(gridcolor="#EFE8FF", linecolor=MAU["muc"])
    fig.update_yaxes(gridcolor="#EFE8FF", linecolor=MAU["muc"])
    if cao:
        fig.update_layout(height=cao)
    return fig


def tieu_de_trang(tieu_de="X10 Investment Lab", phu_de="Phân tích cổ phiếu Việt Nam theo khẩu vị của bạn"):
    st.markdown(
        f'<div class="x10-hero"><div class="x10-logo">X10</div><div><div class="x10-title">{tieu_de}</div>'
        f'<div class="x10-sub">{phu_de}</div></div></div>', unsafe_allow_html=True)


def huong_dan_3_buoc():
    st.markdown(
        '<div class="x10-steps">'
        '<div class="x10-step"><div class="x10-num" style="background:#FF4F9A">1</div><div><b>Chọn khẩu vị</b><br>An toàn, cân bằng, tăng trưởng...</div></div>'
        '<div class="x10-step"><div class="x10-num" style="background:#22D3EE">2</div><div><b>Nhập mã</b><br>Rồi bấm Phân tích</div></div>'
        '<div class="x10-step"><div class="x10-num" style="background:#B8F13C">3</div><div><b>Đọc kết luận</b><br>Hợp hay không, vì sao, tải PDF</div></div>'
        '</div>', unsafe_allow_html=True)


_MAU_TIN_HIEU = {"MUA": MAU["lime"], "THEO DÕI": MAU["vang"], "BÁN / TRÁNH": "#FF8FA3"}


def the_tin_hieu(ma, tin_hieu, diem_tong, diem_ta, diem_fa, gia=None, ten_nganh=""):
    mau = _MAU_TIN_HIEU.get(tin_hieu, MAU["vang"])
    gia_html = f'<div><div class="x10-small">GIÁ ĐÓNG CỬA</div><div class="x10-big">{gia}</div></div>' if gia else ""
    nganh = f'<div class="x10-small">{ten_nganh}</div>' if ten_nganh else ""
    st.markdown(
        f'<div class="x10-signal"><div><div class="x10-big">{ma}</div>{nganh}</div>'
        f'<div class="x10-chip" style="background:{mau};font-size:20px">{tin_hieu}</div>{gia_html}'
        f'<div><div class="x10-small">ĐIỂM THỐNG NHẤT</div><div class="x10-big">{diem_tong:.0f}<span style="font-size:16px">/100</span></div>'
        f'<div class="x10-small">Kỹ thuật {diem_ta:.0f} · Cơ bản {diem_fa:.0f}</div></div></div>',
        unsafe_allow_html=True)


_MAU_TRANG_THAI = {"Đạt": MAU["lime"], "Không đạt": "#FF8FA3", "Thiếu dữ liệu": "#E3E0EE",
                   "Kích hoạt": "#FF8FA3", "Không": MAU["lime"], "N/A": "#E3E0EE"}


def tag_trang_thai(trang_thai):
    mau = _MAU_TRANG_THAI.get(trang_thai, "#E3E0EE")
    return f'<span class="x10-tag" style="background:{mau}">{trang_thai}</span>'


def dong_tieu_chi(ten, trang_thai, chi_tiet):
    return (f'<div class="x10-row">{tag_trang_thai(trang_thai)}<div><b>{ten}</b>'
            f'<div class="x10-small" style="color:#6B6389;opacity:1">{chi_tiet}</div></div></div>')


def thanh_phan_tram(ty_le, mau=None):
    mau = mau or MAU["muc"]
    return f'<div class="x10-bar"><div style="width:{max(0, min(100, ty_le)):.0f}%;background:{mau}"></div></div>'