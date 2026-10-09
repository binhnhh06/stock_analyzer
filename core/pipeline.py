import pandas as pd
from core.data import lay_gia, lay_bctc, lay_ratio
from core.analysis import phan_tich, tinh_ty_so
from core.strategy import danh_gia_x10
from core.profiles import xay_ngu_canh, danh_gia
from core import industry


def phan_tich_ma(ma, so_ngay, so_nam, vni):
    gia0, ratio, bctc = lay_gia(ma, so_ngay), lay_ratio(ma), lay_bctc(ma, so_nam)
    ty_so = tinh_ty_so(bctc)
    gia, kq, diem, toi_da, ly_do, kn = phan_tich(gia0, ratio, ty_so)
    xep = danh_gia_x10(gia, kq, ty_so, vni)
    return {"ma": ma, "gia": gia, "kq": kq, "bctc": bctc, "ty_so": ty_so, "xep": xep,
            "diem": diem, "toi_da": toi_da, "ly_do": ly_do, "kn": kn, "vni": vni}


def ngu_canh_tu_ket_qua(r):
    return xay_ngu_canh(r["gia"], r["kq"], r["ty_so"], r["xep"], r["vni"])


def quet_nhieu_ma(danh_sach, so_ngay, so_nam, vni, cau_hinh, tien_do=None):
    hang = []
    for i, ma in enumerate(danh_sach):
        if tien_do:
            tien_do(i, len(danh_sach), ma)
        info = industry.thong_tin(ma)
        dong = {"Mã": ma, "Ngành": info.get("icb2", ""), "Sàn": info.get("san", "")}
        try:
            r = phan_tich_ma(ma, so_ngay, so_nam, vni)
            kv = danh_gia(ngu_canh_tu_ket_qua(r), cau_hinh)
            dong.update({
                "% hợp khẩu vị": round(kv["ty_le"], 0) if kv["ty_le"] is not None else None,
                "Đạt": f"{kv['dat']}/{kv['dat'] + kv['khong']}",
                "Mức hợp": kv["hang"],
                "Tín hiệu X10": r["xep"]["tin_hieu"],
                "Điểm X10": r["xep"]["diem_tong"],
                "Giá đóng cửa": r["kq"]["Giá đóng cửa"],
                "ROE (%)": r["kq"].get("ROE (%) (từ BCTC)"),
                "P/E": r["kq"].get("P/E"),
                "Lợi suất 6T (%)": r["kq"]["Lợi suất 6 tháng (%)"],
                "Ghi chú": "" if r["bctc"] else "Không có BCTC, điểm cơ bản trung tính",
            })
        except Exception as e:
            dong["Ghi chú"] = f"Lỗi: {str(e)[:60]}"
        hang.append(dong)
    if tien_do:
        tien_do(len(danh_sach), len(danh_sach), "")
    df = pd.DataFrame(hang)
    if "% hợp khẩu vị" in df:
        df = df.sort_values(["% hợp khẩu vị", "Điểm X10"], ascending=False, na_position="last")
    return df.reset_index(drop=True)