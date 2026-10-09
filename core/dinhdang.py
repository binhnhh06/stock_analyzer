import math


def so_vn(v, thap_phan=1, hau_to=""):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "-"
        s = f"{float(v):,.{thap_phan}f}"
    except (TypeError, ValueError):
        return "-"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"{s}{hau_to}"


def ty_dong(v, thap_phan=1):
    try:
        return so_vn(float(v) / 1e9, thap_phan)
    except (TypeError, ValueError):
        return "-"