import io
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("VN", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("VN-B", "C:/Windows/Fonts/arialbd.ttf"))


def _bieu_do(gia, ma):
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax[0].plot(gia["time"], gia["close"], label="Giá")
    ax[0].plot(gia["time"], gia["MA20"], label="MA20")
    ax[0].plot(gia["time"], gia["MA50"], label="MA50")
    ax[0].legend(); ax[0].set_title(f"{ma} - Giá và đường trung bình")
    ax[1].plot(gia["time"], gia["RSI"], color="purple")
    ax[1].axhline(70, ls="--", c="r"); ax[1].axhline(30, ls="--", c="g"); ax[1].set_title("RSI(14)")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120); plt.close()
    buf.seek(0)
    return buf


def _fmt(v):
    try:
        return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}"
    except Exception:
        return "-"


def _bang(df, tieu_de_cot, max_dong=18):
    nam = list(df.columns)[-4:]
    rows = [[tieu_de_cot] + [str(n) for n in nam]]
    for idx, r in df.head(max_dong).iterrows():
        rows.append([str(idx)[:38]] + [_fmt(r[n]) for n in nam])
    t = Table(rows, colWidths=[7 * cm] + [2.5 * cm] * len(nam), repeatRows=1)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "VN"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                           ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey)]))
    return t


def xuat_pdf(ma, gia, kq, diem, toi_da, ly_do, kn, bctc, ty_so):
    h1 = ParagraphStyle("h1", fontName="VN-B", fontSize=18, spaceAfter=10)
    h2 = ParagraphStyle("h2", fontName="VN-B", fontSize=13, spaceBefore=10, spaceAfter=6)
    tx = ParagraphStyle("tx", fontName="VN", fontSize=10.5, leading=15)
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm)
    st = [Paragraph(f"BÁO CÁO PHÂN TÍCH CỔ PHIẾU {ma}", h1),
          Paragraph(f"Ngày lập: {datetime.now():%d/%m/%Y}", tx),
          Paragraph(f"Khuyến nghị: <b>{kn}</b> (điểm {diem}/{toi_da})", tx)]
    st += [Paragraph("• " + r, tx) for r in ly_do]
    st.append(Paragraph("1. Chỉ số chính", h2))
    bang = Table([["Chỉ tiêu", "Giá trị"]] + [[k, f"{v:,.2f}"] for k, v in kq.items()], colWidths=[8 * cm, 6 * cm])
    bang.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "VN"),
                              ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                              ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    st += [bang, Paragraph("2. Biểu đồ kỹ thuật", h2), Image(_bieu_do(gia, ma), width=16 * cm, height=12 * cm)]

    if bctc:
        st.append(PageBreak())
        st.append(Paragraph("3. Báo cáo tài chính (đơn vị theo nguồn dữ liệu)", h2))
        ten = {"balance_sheet": "Bảng cân đối kế toán", "income_statement": "Kết quả kinh doanh",
               "cash_flow": "Lưu chuyển tiền tệ"}
        for k, df in bctc.items():
            st += [Paragraph(ten.get(k, k), tx), _bang(df, "Chỉ tiêu"), Spacer(1, 8)]
    if ty_so is not None and not ty_so.empty:
        st += [Paragraph("4. Tỷ số tài chính", h2), _bang(ty_so, "Tỷ số", 12)]
    st += [Spacer(1, 12), Paragraph("Nguồn: vnstock, vnfinancialdata. Báo cáo tự động, chỉ mang tính tham khảo, không phải lời khuyên đầu tư.", tx)]
    doc.build(st)
    return out.getvalue()