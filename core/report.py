import io
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core.dinhdang import so_vn, ty_dong

INK, TIM, HONG, LIME, CYAN, VANG = "#1B1233", "#6C3BFF", "#FF4F9A", "#B8F13C", "#22D3EE", "#FFD43B"
P_LIME, P_HONG, P_CYAN, P_VANG, P_TIM = "#DDF9A4", "#FFD0E5", "#C6F3FC", "#FFE9A3", "#E5DBFF"
XAM, DO, XANH = "#6B6389", "#D4183D", "#078A4F"
TT_MAU = {"Đạt": LIME, "Không": LIME, "Không đạt": "#FF8FA3", "Kích hoạt": "#FF8FA3",
          "Thiếu dữ liệu": "#E3E0EE", "N/A": "#E3E0EE"}
TIN_HIEU_MAU = {"MUA": LIME, "THEO DÕI": VANG, "BÁN / TRÁNH": "#FF8FA3"}

_THU_MUC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_UNG_VIEN = [
    (os.path.join(_THU_MUC, "assets", "fonts", "BeVietnamPro-Regular.ttf"), os.path.join(_THU_MUC, "assets", "fonts", "BeVietnamPro-Bold.ttf")),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    (os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans.ttf"),
     os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans-Bold.ttf")),
]


def _dang_ky_font():
    for thuong, dam in _FONT_UNG_VIEN:
        if os.path.exists(thuong) and os.path.exists(dam):
            pdfmetrics.registerFont(TTFont("VN", thuong))
            pdfmetrics.registerFont(TTFont("VN-B", dam))
            return
    raise RuntimeError("Không tìm thấy phông chữ hỗ trợ tiếng Việt. Hãy chép BeVietnamPro-Regular.ttf và "
                       "BeVietnamPro-Bold.ttf vào thư mục assets/fonts/.")


_dang_ky_font()


def _st(ten, co=10, dam=False, mau=INK, **kw):
    return ParagraphStyle(ten, fontName="VN-B" if dam else "VN", fontSize=co, leading=kw.pop("leading", co * 1.4),
                          textColor=colors.HexColor(mau), **kw)


S_TX = _st("tx", 10)
S_NHO = _st("nho", 8.5, mau=XAM)
S_H2 = _st("h2", 14, True, spaceBefore=14, spaceAfter=7)
S_CELL = _st("cell", 9)


def _gia_hien_thi(v):
    return f"{so_vn(v * 1000, 0)} đ" if v < 1000 else f"{so_vn(v, 0)} đ"


def _ve_trang(canvas, doc, ma):
    w, h = A4
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(colors.HexColor(TIM)); canvas.rect(0, h - 4.2 * cm, w, 4.2 * cm, stroke=0, fill=1)
        for i, m in enumerate([HONG, LIME, CYAN, VANG]):
            canvas.setFillColor(colors.HexColor(m)); canvas.rect(w - (4 - i) * 1.1 * cm, h - 4.2 * cm, 1.1 * cm, 0.45 * cm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor(LIME)); canvas.setFont("VN-B", 10)
        canvas.drawString(2 * cm, h - 1.5 * cm, "X10 INVESTMENT LAB · BÁO CÁO PHÂN TÍCH CỔ PHIẾU")
        canvas.setFillColor(colors.white); canvas.setFont("VN-B", 34); canvas.drawString(2 * cm, h - 3.1 * cm, ma)
        canvas.setFont("VN", 10); canvas.drawRightString(w - 2 * cm, h - 1.5 * cm, f"Ngày lập {datetime.now():%d/%m/%Y}")
    else:
        canvas.setFillColor(colors.HexColor(TIM)); canvas.rect(0, h - 1.2 * cm, w, 1.2 * cm, stroke=0, fill=1)
        canvas.setFillColor(colors.white); canvas.setFont("VN-B", 10)
        canvas.drawString(2 * cm, h - 0.8 * cm, f"{ma} · X10 Investment Lab")
    canvas.setStrokeColor(colors.HexColor("#DCCFFB")); canvas.line(2 * cm, 1.5 * cm, w - 2 * cm, 1.5 * cm)
    canvas.setFillColor(colors.HexColor(XAM)); canvas.setFont("VN", 7.5)
    canvas.drawString(2 * cm, 1.0 * cm, "Báo cáo tự động, chỉ mang tính tham khảo, không phải lời khuyên đầu tư.")
    canvas.drawRightString(w - 2 * cm, 1.0 * cm, f"Trang {doc.page}")
    canvas.restoreState()


def _bieu_do(gia, ma):
    plt.rcParams["font.size"] = 9
    fig, ax = plt.subplots(3, 1, figsize=(8.4, 7.2), sharex=True, gridspec_kw={"height_ratios": [3.2, 1, 1.2]})
    ax[0].plot(gia["time"], gia["close"], color=TIM, lw=2.2, label="Giá")
    ax[0].fill_between(gia["time"], gia["close"], gia["close"].min(), color=TIM, alpha=0.08)
    ax[0].plot(gia["time"], gia["MA20"], color=HONG, lw=1.4, label="MA20")
    ax[0].plot(gia["time"], gia["MA50"], color="#0BA5C4", lw=1.4, label="MA50")
    ax[0].set_title(f"{ma}: giá và đường trung bình", loc="left", fontweight="bold", color=INK)
    ax[0].legend(loc="upper left", ncol=3, frameon=False)
    if "volume" in gia:
        ax[1].bar(gia["time"], gia["volume"], color=CYAN, width=1.0)
    ax[1].set_title("Khối lượng", loc="left", fontsize=9, color=XAM)
    ax[2].plot(gia["time"], gia["RSI"], color="#FF8A3D", lw=1.6)
    ax[2].axhline(70, ls="--", c=DO, lw=1); ax[2].axhline(30, ls="--", c=XANH, lw=1)
    ax[2].fill_between(gia["time"], 30, 70, color=P_TIM, alpha=0.5); ax[2].set_ylim(0, 100)
    ax[2].set_title("RSI(14): trên 70 là nóng, dưới 30 là nguội", loc="left", fontsize=9, color=XAM)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False); a.grid(axis="y", color="#EFE8FF"); a.tick_params(colors=XAM)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150); plt.close(fig)
    buf.seek(0)
    return buf


def _bang(rows, rong, dau_ngang=True, can_phai_tu=1, mau_o=None):
    t = Table(rows, colWidths=rong, repeatRows=1 if dau_ngang else 0)
    lenh = [("FONTNAME", (0, 0), (-1, -1), "VN"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(INK)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7DFFA")),
            ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor(INK))]
    if can_phai_tu is not None:
        lenh.append(("ALIGN", (can_phai_tu, 0), (-1, -1), "RIGHT"))
    if dau_ngang:
        lenh += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(INK)), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                 ("FONTNAME", (0, 0), (-1, 0), "VN-B")]
    for i in range(1 if dau_ngang else 0, len(rows)):
        if i % 2 == 0:
            lenh.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F7F3FF")))
    for (c, r), m in (mau_o or {}).items():
        lenh.append(("BACKGROUND", (c, r), (c, r), colors.HexColor(m)))
        lenh.append(("FONTNAME", (c, r), (c, r), "VN-B"))
    t.setStyle(TableStyle(lenh))
    return t


KHOAN_MUC = {
    "balance_sheet": ["TỔNG TÀI SẢN", "TÀI SẢN NGẮN HẠN", "Tiền và tương đương tiền", "Hàng tồn kho", "TÀI SẢN DÀI HẠN",
                      "NỢ PHẢI TRẢ", "Nợ ngắn hạn", "Nợ dài hạn", "Vay ngắn hạn", "Vay dài hạn", "VỐN CHỦ SỞ HỮU"],
    "income_statement": ["Doanh số thuần", "Giá vốn hàng bán", "Lãi gộp", "Chi phí bán hàng", "Chi phí quản lý doanh nghiệp",
                         "EBIT", "EBITDA", "Lãi/(lỗ) ròng trước thuế", "Lãi/(lỗ) thuần sau thuế",
                         "Lợi nhuận của Cổ đông của Công ty mẹ", "Lãi cơ bản trên cổ phiếu"],
    "cash_flow": ["Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh", "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư",
                  "Lưu chuyển tiền tệ từ hoạt động tài chính", "Lưu chuyển tiền thuần trong kỳ",
                  "Tiền và tương đương tiền cuối kỳ", "Cổ tức đã trả", "Tiền mua tài sản cố định và các tài sản dài hạn khác"],
}
TEN_BC = {"balance_sheet": "Bảng cân đối kế toán", "income_statement": "Kết quả kinh doanh", "cash_flow": "Lưu chuyển tiền tệ"}


def _chon_dong(df, khoan_muc):
    chon = []
    chuan = {str(i).strip().lower(): i for i in df.index}
    for t in khoan_muc:
        if t.lower() in chuan:
            chon.append(chuan[t.lower()])
    if not chon:
        chon = list(df.abs().iloc[:, -1].sort_values(ascending=False).head(10).index)
    return chon


def _bang_bctc(k, df):
    nam = list(df.columns)[-4:]
    rows, mau_chu = [["Chỉ tiêu (tỷ đồng)"] + [str(n) for n in nam]], []
    for i, idx in enumerate(_chon_dong(df, KHOAN_MUC.get(k, [])), start=1):
        la_eps = "trên cổ phiếu" in str(idx).lower()
        o = []
        for j, n in enumerate(nam, start=1):
            v = df.loc[idx, n]
            o.append(so_vn(v, 0) if la_eps else ty_dong(v))
            if v is not None and v == v and v < 0:
                mau_chu.append(("TEXTCOLOR", (j, i), (j, i), colors.HexColor(DO)))
        rows.append([str(idx)[:46] + (" (đồng)" if la_eps else "")] + o)
    t = _bang(rows, [7.4 * cm] + [2.4 * cm] * len(nam))
    t.setStyle(TableStyle(mau_chu))
    return t


def _bang_ty_so(ty_so):
    nam = list(ty_so.columns)[-5:]
    rows, mau_chu = [["Tỷ số"] + [str(n) for n in nam]], []
    for i, (idx, r) in enumerate(ty_so.iterrows(), start=1):
        rows.append([str(idx)] + [so_vn(r[n], 2 if "lần" in str(idx) else 1) for n in nam])
        for j, n in enumerate(nam, start=1):
            if r[n] == r[n] and r[n] < 0:
                mau_chu.append(("TEXTCOLOR", (j, i), (j, i), colors.HexColor(DO)))
    t = _bang(rows, [6.2 * cm] + [2.1 * cm] * len(nam))
    t.setStyle(TableStyle(mau_chu))
    return t


def xuat_pdf(ma, gia, kq, diem, toi_da, ly_do, kn, bctc, ty_so, xep=None, khau_vi=None, ten_khau_vi="", ten_nganh=""):
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.0 * cm,
                            bottomMargin=2.0 * cm, title=f"Báo cáo {ma}", author="X10 Investment Lab")
    W = 17 * cm
    tin_hieu = xep["tin_hieu"] if xep else kn
    tong = xep["diem_tong"] if xep else diem
    st = [Spacer(1, 2.5 * cm)]
    if ten_nganh:
        st.append(Paragraph(ten_nganh, S_NHO))

    mau_th = TIN_HIEU_MAU.get(tin_hieu, VANG)
    dong_phu = (f"Kỹ thuật {so_vn(xep['diem_ta'], 0)} (80%) · Cơ bản {so_vn(xep['diem_fa'], 0)} (20%)" if xep
                else f"Đạt {diem}/{toi_da} tiêu chí")
    ket = Table([[Paragraph(f'<font size="20"><b>{tin_hieu}</b></font>', _st("kl", 20, True, alignment=1)),
                  [Paragraph(f'<font size="22"><b>{so_vn(tong, 0)}</b></font><font size="11"> / 100 điểm</font>', _st("d", 22, True)),
                   Paragraph(dong_phu, S_TX)]]], colWidths=[5.6 * cm, W - 5.6 * cm])
    ket.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), colors.HexColor(mau_th)),
                             ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(P_TIM)), ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(INK)),
                             ("LINEAFTER", (0, 0), (0, 0), 1.5, colors.HexColor(INK)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("LEFTPADDING", (0, 0), (-1, -1), 14)]))
    st += [ket, Spacer(1, 10)]

    the = [("Giá đóng cửa", _gia_hien_thi(kq["Giá đóng cửa"]), P_LIME),
           ("GTGD 20 phiên", (so_vn(xep["gtgd"] / 1e9, 1) + " tỷ") if xep else "-", P_HONG),
           ("RSI(14)", so_vn(kq["RSI(14)"], 0), P_CYAN),
           ("Lợi suất 6 tháng", so_vn(kq["Lợi suất 6 tháng (%)"], 1, "%"), P_VANG)]
    o = [[Paragraph(f'<font size="8" color="{XAM}">{a}</font><br/><font size="14"><b>{b}</b></font>', _st("kpi", 14, leading=18)) for a, b, _ in the]]
    kp = Table(o, colWidths=[W / 4] * 4)
    kp.setStyle(TableStyle([("BACKGROUND", (i, 0), (i, 0), colors.HexColor(the[i][2])) for i in range(4)] +
                           [("BOX", (i, 0), (i, 0), 1.2, colors.HexColor(INK)) for i in range(4)] +
                           [("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
    st += [kp]

    st.append(Paragraph("Vì sao có tín hiệu này?", S_H2))
    if xep:
        rows, mau = [["Kết quả", "Điều kiện", "Chi tiết"]], {}
        for loai, ds in (("MUA", xep["dk_mua"]), ("BÁN", xep["dk_ban"])):
            for ten, tt, ct in ds:
                rows.append([tt, Paragraph(f"<b>[{loai}]</b> {ten}", S_CELL), Paragraph(ct, S_CELL)])
                mau[(0, len(rows) - 1)] = TT_MAU.get(tt, "#E3E0EE")
        st.append(_bang(rows, [2.4 * cm, 6.4 * cm, 8.2 * cm], can_phai_tu=None, mau_o=mau))
    else:
        st += [Paragraph("• " + r, S_TX) for r in ly_do]

    if khau_vi and khau_vi["dong"]:
        st.append(Paragraph(f"Mức hợp khẩu vị: {ten_khau_vi}", S_H2))
        pt = "-" if khau_vi["ty_le"] is None else so_vn(khau_vi["ty_le"], 0, "%")
        hv = Table([[Paragraph(f"<b>{khau_vi['hang']}</b>", _st("hv", 12, True)), Paragraph(
            f"Đạt {khau_vi['dat']}/{khau_vi['dat'] + khau_vi['khong']} tiêu chí ({pt})", S_TX)]], colWidths=[6 * cm, 11 * cm])
        hv.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), colors.HexColor(khau_vi["mau"])), ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(INK)),
                                ("LINEAFTER", (0, 0), (0, 0), 1.5, colors.HexColor(INK)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
        st += [hv, Spacer(1, 6)]
        rows, mau = [["Kết quả", "Tiêu chí", "Ngưỡng", "Giá trị của mã"]], {}
        for d in khau_vi["dong"]:
            rows.append([d["trang_thai"], Paragraph(d["nhan"], S_CELL), d["nguong"], d["gia_tri"]])
            mau[(0, len(rows) - 1)] = TT_MAU.get(d["trang_thai"], "#E3E0EE")
        st.append(_bang(rows, [2.6 * cm, 6.6 * cm, 4 * cm, 3.8 * cm], can_phai_tu=None, mau_o=mau))

    st += [PageBreak(), Paragraph("Biểu đồ kỹ thuật", S_H2), Image(_bieu_do(gia, ma), width=17 * cm, height=14.5 * cm)]

    if ty_so is not None and not ty_so.empty:
        st += [Paragraph("Tỷ số tài chính chính", S_H2), _bang_ty_so(ty_so)]
    if bctc:
        st += [Paragraph("Báo cáo tài chính (các khoản chính, đơn vị tỷ đồng)", S_H2)]
        for k, df in bctc.items():
            st += [Paragraph(TEN_BC.get(k, k), _st("bc", 11, True, spaceBefore=8, spaceAfter=4, mau=TIM)), _bang_bctc(k, df), Spacer(1, 6)]
    st += [Spacer(1, 12), Paragraph("Nguồn dữ liệu: vnstock (giá), vnfinancialdata (BCTC), phân ngành ICB từ vn-annual-report-miner. "
                                    "Báo cáo chỉ mang tính tham khảo, không phải lời khuyên đầu tư.", S_NHO)]
    doc.build(st, onFirstPage=lambda c, d: _ve_trang(c, d, ma), onLaterPages=lambda c, d: _ve_trang(c, d, ma))
    return out.getvalue()