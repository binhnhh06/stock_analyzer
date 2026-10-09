import math
from core.dinhdang import so_vn

NHOM = ["Chất lượng doanh nghiệp", "Tăng trưởng", "Định giá", "Kỹ thuật", "Rủi ro & thanh khoản", "Thị trường"]


def _tc(key, nhom, nhan, loai, don_vi="", mac_dinh=None, tt=None, td=None, buoc=1.0, tp=1, duong=False, mo_ta=""):
    return dict(key=key, nhom=nhom, nhan=nhan, loai=loai, don_vi=don_vi, mac_dinh=mac_dinh,
                toi_thieu=tt, toi_da=td, buoc=buoc, thap_phan=tp, duong=duong, mo_ta=mo_ta)


TIEU_CHI = [
    _tc("roe", NHOM[0], "ROE tối thiểu", "min", "%", 12, 0, 60, 1, 1, mo_ta="Lợi nhuận trên vốn chủ sở hữu năm gần nhất"),
    _tc("roe_tb3", NHOM[0], "ROE trung bình 3 năm tối thiểu", "min", "%", 12, 0, 60, 1, 1, mo_ta="Hiệu quả ổn định, không chỉ một năm đẹp"),
    _tc("bien_ln_rong", NHOM[0], "Biên lợi nhuận ròng tối thiểu", "min", "%", 5, 0, 60, 1, 1),
    _tc("bien_ln_gop", NHOM[0], "Biên lợi nhuận gộp tối thiểu", "min", "%", 15, 0, 90, 1, 1),
    _tc("no_vcsh", NHOM[0], "Nợ / VCSH tối đa", "max", "lần", 2.0, 0, 15, 0.1, 2, mo_ta="Đòn bẩy tài chính, càng thấp càng an toàn"),
    _tc("no_vay_vcsh", NHOM[0], "Nợ vay / VCSH tối đa", "max", "lần", 1.0, 0, 15, 0.1, 2),
    _tc("thanh_toan", NHOM[0], "Thanh toán hiện hành tối thiểu", "min", "lần", 1.2, 0, 10, 0.1, 2, mo_ta="Tài sản ngắn hạn / nợ ngắn hạn"),
    _tc("cfo_lnst", NHOM[0], "Dòng tiền kinh doanh / LNST tối thiểu", "min", "lần", 0.8, 0, 5, 0.1, 2, mo_ta="Lợi nhuận có tiền thật đi kèm hay không"),
    _tc("so_nam_lai", NHOM[0], "Số năm có lãi liên tiếp tối thiểu", "min", "năm", 3, 0, 10, 1, 0),
    _tc("chi_tra_co_tuc", NHOM[0], "Chi trả cổ tức / LNST tối thiểu", "min", "%", 20, 0, 100, 5, 0, mo_ta="Ước tính từ cổ tức tiền mặt đã chi, trung bình 3 năm"),
    _tc("tang_truong_lnst", NHOM[1], "Tăng trưởng LNST tối thiểu", "min", "%", 10, -50, 200, 5, 0),
    _tc("tang_truong_dt", NHOM[1], "Tăng trưởng doanh thu tối thiểu", "min", "%", 8, -50, 200, 5, 0),
    _tc("pe", NHOM[2], "P/E tối đa (và lớn hơn 0)", "max", "lần", 20, 1, 100, 1, 1, duong=True, mo_ta="Giá / lợi nhuận mỗi cổ phiếu"),
    _tc("pb", NHOM[2], "P/B tối đa (và lớn hơn 0)", "max", "lần", 3, 0.1, 30, 0.1, 2, duong=True, mo_ta="Giá / giá trị sổ sách"),
    _tc("gia_tren_ma50", NHOM[3], "Giá nằm trên MA50", "bool"),
    _tc("gia_tren_ma200", NHOM[3], "Giá nằm trên MA200", "bool"),
    _tc("ma20_tren_ma50", NHOM[3], "MA20 cắt lên trên MA50", "bool"),
    _tc("rsi_min", NHOM[3], "RSI(14) tối thiểu", "min", "", 40, 0, 100, 1, 0),
    _tc("rsi_max", NHOM[3], "RSI(14) tối đa", "max", "", 70, 0, 100, 1, 0, mo_ta="Tránh mua khi quá nóng"),
    _tc("loi_suat_6t", NHOM[3], "Lợi suất 6 tháng tối thiểu", "min", "%", 0, -50, 200, 5, 0),
    _tc("cach_dinh", NHOM[3], "Giảm từ đỉnh 60 phiên tối đa", "max", "%", 15, 0, 80, 1, 1),
    _tc("bien_dong", NHOM[4], "Biến động giá năm tối đa", "max", "%", 35, 5, 120, 1, 0, mo_ta="Độ lệch chuẩn lợi suất ngày quy năm"),
    _tc("gtgd", NHOM[4], "Giá trị giao dịch TB 20 phiên tối thiểu", "min", "tỷ/phiên", 2, 0, 500, 1, 1),
    _tc("vnindex_ma50", NHOM[5], "VN-Index nằm trên MA50", "bool"),
    _tc("diem_tong", NHOM[5], "Điểm thống nhất X10 tối thiểu", "min", "điểm", 60, 0, 100, 5, 0),
]

KHAU_VI = {
    "an_toan": {"ten": "An toàn, giữ vốn", "mau": "#22D3EE",
                "mo_ta": "Ưu tiên doanh nghiệp vay ít, lãi đều, giá ít biến động.",
                "phu_hop": "Người mới, vốn không muốn rủi ro lớn.",
                "tieu_chi": {"roe": 10, "no_vcsh": 1.0, "thanh_toan": 1.5, "bien_ln_rong": 5, "so_nam_lai": 4,
                             "bien_dong": 30, "gtgd": 5, "gia_tren_ma200": True, "pe": 20, "pb": 3, "cach_dinh": 15}},
    "can_bang": {"ten": "Cân bằng", "mau": "#6C3BFF",
                 "mo_ta": "Vừa có chất lượng, vừa có xu hướng giá tốt, định giá không quá đắt.",
                 "phu_hop": "Đa số nhà đầu tư dài hạn vừa phải.",
                 "tieu_chi": {"roe": 12, "no_vcsh": 2.0, "bien_ln_rong": 5, "tang_truong_lnst": 0, "pe": 22,
                              "gia_tren_ma50": True, "rsi_min": 40, "rsi_max": 70, "gtgd": 2, "vnindex_ma50": True,
                              "diem_tong": 50}},
    "tang_truong": {"ten": "Tăng trưởng", "mau": "#FF4F9A",
                    "mo_ta": "Chọn doanh nghiệp lợi nhuận và doanh thu tăng nhanh, giá đang có đà.",
                    "phu_hop": "Chấp nhận biến động để tìm cổ phiếu tăng mạnh.",
                    "tieu_chi": {"tang_truong_lnst": 15, "tang_truong_dt": 10, "roe": 15, "no_vcsh": 2.5, "pe": 35,
                                 "gia_tren_ma50": True, "ma20_tren_ma50": True, "loi_suat_6t": 5, "gtgd": 3}},
    "gia_tri": {"ten": "Giá trị, mua rẻ", "mau": "#B8F13C",
                "mo_ta": "Tìm cổ phiếu định giá thấp nhưng doanh nghiệp vẫn khoẻ, có dòng tiền thật.",
                "phu_hop": "Kiên nhẫn, chờ thị trường định giá lại.",
                "tieu_chi": {"pe": 12, "pb": 1.5, "roe": 10, "no_vcsh": 1.5, "so_nam_lai": 3, "cfo_lnst": 0.8, "gtgd": 1}},
    "co_tuc": {"ten": "Thu nhập cổ tức", "mau": "#FFD43B",
               "mo_ta": "Ưu tiên doanh nghiệp lãi ổn định, chia cổ tức đều, nợ thấp.",
               "phu_hop": "Muốn dòng tiền đều đặn từ cổ tức.",
               "tieu_chi": {"chi_tra_co_tuc": 20, "roe": 12, "no_vcsh": 1.5, "so_nam_lai": 5, "cfo_lnst": 0.8,
                            "bien_dong": 35, "pe": 18}},
    "luot_song": {"ten": "Lướt sóng ngắn hạn", "mau": "#FF8A3D",
                  "mo_ta": "Bám theo xu hướng và thanh khoản, ít quan tâm định giá.",
                  "phu_hop": "Giao dịch ngắn hạn, theo dõi thị trường hằng ngày.",
                  "tieu_chi": {"gia_tren_ma50": True, "ma20_tren_ma50": True, "rsi_min": 50, "rsi_max": 75, "gtgd": 10,
                               "vnindex_ma50": True, "diem_tong": 60}},
    "tuy_chinh": {"ten": "Tự chọn tiêu chí", "mau": "#E3E0EE",
                  "mo_ta": "Bạn tự bật/tắt từng tiêu chí ở thanh bên.",
                  "phu_hop": "Người đã biết mình cần gì.", "tieu_chi": {}},
}


def cau_hinh_khau_vi(ma_khau_vi):
    return dict(KHAU_VI[ma_khau_vi]["tieu_chi"])


def _chuoi(ty_so, ten):
    if ty_so is None or ty_so.empty or ten not in ty_so.index:
        return None
    s = ty_so.loc[ten].dropna()
    return s if len(s) else None


def _gan_nhat(ty_so, ten):
    s = _chuoi(ty_so, ten)
    return float(s.iloc[-1]) if s is not None else None


def _tb(ty_so, ten, n=3):
    s = _chuoi(ty_so, ten)
    return float(s.tail(n).mean()) if s is not None else None


def _so_nam_lai(ty_so):
    s = _chuoi(ty_so, "Biên LN ròng (%)")
    if s is None:
        return None
    dem = 0
    for v in reversed(list(s.values)):
        if v > 0:
            dem += 1
        else:
            break
    return float(dem)


def xay_ngu_canh(gia, kq, ty_so, xep, vni):
    c = gia["close"]
    last = float(c.iloc[-1])
    ma200 = c.rolling(200).mean().iloc[-1]
    ma50, ma20 = kq.get("MA50"), kq.get("MA20")
    dinh = float(c.tail(60).max())
    vni_ma50 = None
    if vni is not None and len(vni) >= 50:
        v = vni["close"]
        vni_ma50 = bool(v.iloc[-1] >= v.rolling(50).mean().iloc[-1])
    return {
        "roe": _gan_nhat(ty_so, "ROE (%)"), "roe_tb3": _tb(ty_so, "ROE (%)"),
        "bien_ln_rong": _gan_nhat(ty_so, "Biên LN ròng (%)"), "bien_ln_gop": _gan_nhat(ty_so, "Biên LN gộp (%)"),
        "no_vcsh": _gan_nhat(ty_so, "Nợ / VCSH (lần)"), "no_vay_vcsh": _gan_nhat(ty_so, "Nợ vay / VCSH (lần)"),
        "thanh_toan": _gan_nhat(ty_so, "Thanh toán hiện hành (lần)"), "cfo_lnst": _gan_nhat(ty_so, "CFO / LNST (lần)"),
        "so_nam_lai": _so_nam_lai(ty_so), "chi_tra_co_tuc": _tb(ty_so, "Chi trả cổ tức / LNST (%)"),
        "tang_truong_lnst": _gan_nhat(ty_so, "Tăng trưởng LNST (%)"),
        "tang_truong_dt": _gan_nhat(ty_so, "Tăng trưởng doanh thu (%)"),
        "pe": kq.get("P/E"), "pb": kq.get("P/B"),
        "gia_tren_ma50": None if ma50 is None or math.isnan(ma50) else bool(last > ma50),
        "gia_tren_ma200": None if math.isnan(ma200) else bool(last > ma200),
        "ma20_tren_ma50": None if ma20 is None or ma50 is None or math.isnan(ma20) or math.isnan(ma50) else bool(ma20 > ma50),
        "rsi_min": kq.get("RSI(14)"), "rsi_max": kq.get("RSI(14)"),
        "loi_suat_6t": kq.get("Lợi suất 6 tháng (%)"), "cach_dinh": (dinh - last) / dinh * 100,
        "bien_dong": kq.get("Biến động năm (%)"), "gtgd": xep["gtgd"] / 1e9,
        "vnindex_ma50": vni_ma50, "diem_tong": xep["diem_tong"],
    }


def _co_so(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def _text_gia_tri(t, v):
    if not _co_so(v):
        return "Không có dữ liệu"
    if t["loai"] == "bool":
        return "Có" if v else "Không"
    return f"{so_vn(v, t['thap_phan'])} {t['don_vi']}".strip()


def _text_nguong(t, nguong):
    if t["loai"] == "bool":
        return "Phải đúng"
    dau = "≥" if t["loai"] == "min" else "≤"
    pre = "0 < giá trị " if t["duong"] else ""
    return f"{pre}{dau} {so_vn(nguong, t['thap_phan'])} {t['don_vi']}".strip()


def danh_gia(ctx, cau_hinh):
    dong = []
    for t in TIEU_CHI:
        k = t["key"]
        if k not in cau_hinh:
            continue
        nguong, v = cau_hinh[k], ctx.get(k)
        if not _co_so(v):
            tt = "Thiếu dữ liệu"
        elif t["loai"] == "bool":
            tt = "Đạt" if v else "Không đạt"
        elif t["loai"] == "min":
            tt = "Đạt" if v >= nguong else "Không đạt"
        else:
            ok = v <= nguong and (v > 0 if t["duong"] else True)
            tt = "Đạt" if ok else "Không đạt"
        dong.append({"nhom": t["nhom"], "nhan": t["nhan"], "nguong": _text_nguong(t, nguong),
                     "gia_tri": _text_gia_tri(t, v), "trang_thai": tt})
    dat = sum(d["trang_thai"] == "Đạt" for d in dong)
    khong = sum(d["trang_thai"] == "Không đạt" for d in dong)
    thieu = sum(d["trang_thai"] == "Thiếu dữ liệu" for d in dong)
    ty_le = dat / (dat + khong) * 100 if dat + khong else None
    if ty_le is None:
        hang, mau = "Chưa chọn tiêu chí" if not dong else "Thiếu dữ liệu để kết luận", "#E3E0EE"
    elif ty_le >= 85:
        hang, mau = "Rất hợp khẩu vị", "#B8F13C"
    elif ty_le >= 65:
        hang, mau = "Khá hợp khẩu vị", "#DDF9A4"
    elif ty_le >= 45:
        hang, mau = "Hợp một phần", "#FFD43B"
    else:
        hang, mau = "Chưa hợp khẩu vị", "#FF8FA3"
    return {"dong": dong, "dat": dat, "khong": khong, "thieu": thieu, "ty_le": ty_le,
            "hang": hang, "mau": mau, "dat_het": bool(dong) and khong == 0 and dat > 0}


def tom_tat(ma, ten_khau_vi, res):
    if not res["dong"]:
        return "Bạn chưa bật tiêu chí nào. Hãy chọn một khẩu vị hoặc bật tiêu chí ở thanh bên."
    if res["ty_le"] is None:
        return f"Chưa đủ dữ liệu để đánh giá {ma} theo khẩu vị {ten_khau_vi}."
    truot = [d["nhan"] for d in res["dong"] if d["trang_thai"] == "Không đạt"]
    s = f"{ma} đạt {res['dat']}/{res['dat'] + res['khong']} tiêu chí của khẩu vị {ten_khau_vi}."
    if truot:
        s += " Chưa đạt: " + "; ".join(truot[:4]) + ("..." if len(truot) > 4 else "") + "."
    if res["thieu"]:
        s += f" Có {res['thieu']} tiêu chí thiếu dữ liệu nên không tính."
    return s