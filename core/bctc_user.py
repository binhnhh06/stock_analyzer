"""Cho người dùng tự đưa BCTC (Excel/CSV) khi dữ liệu tự động không có."""
import io
import pandas as pd
from core.data import STATEMENTS

# Chỉ tiêu mẫu cho từng báo cáo (tên khớp với bộ tính tỷ số). Đơn vị nhập: TỶ ĐỒNG.
MAU = {
    "balance_sheet": ["TỔNG TÀI SẢN", "TÀI SẢN NGẮN HẠN", "Tiền và tương đương tiền", "NỢ PHẢI TRẢ",
                      "Nợ ngắn hạn", "Vay ngắn hạn", "Vay dài hạn", "VỐN CHỦ SỞ HỮU"],
    "income_statement": ["Doanh số thuần", "Lãi gộp", "EBIT", "Trong đó: Chi phí lãi vay",
                         "Lãi/(lỗ) thuần sau thuế"],
    "cash_flow": ["Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh", "Cổ tức đã trả"],
}


def mau_excel(so_nam=4):
    """Trả về bytes file Excel mẫu 3 sheet, cột là các năm gần nhất."""
    from datetime import datetime
    nam = list(range(datetime.now().year - so_nam, datetime.now().year))
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for k, ten in STATEMENTS.items():
            d = pd.DataFrame({"Chỉ tiêu": MAU[k], **{n: [None] * len(MAU[k]) for n in nam}})
            d.to_excel(w, sheet_name=ten, index=False)
    return buf.getvalue()


def _chuan_bang(d, don_vi):
    d = d.dropna(how="all").copy()
    d = d[d.iloc[:, 0].notna()]
    d.index = d.iloc[:, 0].astype(str).str.strip()
    d = d.iloc[:, 1:]
    cot = {}
    for c in d.columns:
        s = str(c).strip().split(".")[0]
        if s.isdigit() and 1990 < int(s) < 2100:
            cot[c] = int(s)
    d = d[list(cot)].rename(columns=cot)
    d = d.apply(pd.to_numeric, errors="coerce") * don_vi
    return d.dropna(how="all").sort_index(axis=1)


def doc_bctc(file, don_vi=1e9):
    """Đọc Excel (3 sheet theo mẫu) hoặc CSV 1 bảng có cột 'Báo cáo'. Trả về dict giống lay_bctc()."""
    ten = getattr(file, "name", "").lower()
    kq = {}
    if ten.endswith(".csv"):
        d = pd.read_csv(file)
        if "Báo cáo" in d.columns:
            for k, t in STATEMENTS.items():
                p = d[d["Báo cáo"] == t].drop(columns="Báo cáo")
                if not p.empty:
                    kq[k] = _chuan_bang(p, don_vi)
        else:
            kq["balance_sheet"] = _chuan_bang(d, don_vi)
    else:
        xl = pd.read_excel(file, sheet_name=None)
        for k, t in STATEMENTS.items():
            for ten_sheet, d in xl.items():
                if ten_sheet.strip().lower() == t.lower():
                    b = _chuan_bang(d, don_vi)
                    if not b.empty:
                        kq[k] = b
    return {k: v for k, v in kq.items() if v is not None and not v.empty}