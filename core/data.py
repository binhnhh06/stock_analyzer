import pandas as pd
import requests
from functools import lru_cache
from datetime import datetime, timedelta

# Lỗi gần nhất của từng nguồn dữ liệu, để app hiển thị lý do thay vì im lặng.
LOI = {}

try:
    from vnstock import Vnstock
except Exception as e:
    Vnstock = None
    LOI["vnstock"] = (f"Không import được vnstock: {e}. Gói này đã bị gỡ khỏi PyPI, "
                      "cần copy thủ công thư mục vnstock và vnai vào site-packages của venv.")

try:
    import vnfinancialdata as vnf
except Exception as e:
    vnf = None
    LOI["vnfinancialdata"] = f"Chưa cài vnfinancialdata ({e}). Chạy: pip install vnfinancialdata"

STATEMENTS = {"balance_sheet": "Bảng cân đối kế toán",
              "income_statement": "Kết quả kinh doanh",
              "cash_flow": "Lưu chuyển tiền tệ"}


def _can_vnstock():
    if Vnstock is None:
        raise RuntimeError(LOI.get("vnstock", "Thiếu thư viện vnstock"))


def _goi_y(e):
    t = str(e).lower()
    if any(k in t for k in ("401", "403", "token", "login", "private", "gated", "authent")):
        return " Có thể chưa đăng nhập Hugging Face: pip install huggingface_hub rồi chạy: hf auth login"
    if any(k in t for k in ("connection", "timeout", "resolve", "network")):
        return " Có thể lỗi mạng, thử lại hoặc đổi mạng."
    return ""


def _cot(df, *ung_vien):
    """Tìm tên cột (không phân biệt hoa thường) trong danh sách ứng viên."""
    thap = {str(c).lower(): c for c in df.columns}
    for u in ung_vien:
        if u in thap:
            return thap[u]
    return None


NGUON_GIA = ("VCI", "KBS", "TCBS", "MSN")


def lay_gia(ma, so_ngay=730):
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=so_ngay)).strftime("%Y-%m-%d")
    loi = []
    for nguon in NGUON_GIA:
        try:
            s = Vnstock().stock(symbol=ma, source=nguon)
            gia = s.quote.history(start=start, end=end, interval="1D")
            if gia is not None and len(gia) > 60:
                gia["time"] = pd.to_datetime(gia["time"])
                return gia
            loi.append(f"{nguon}: ít dữ liệu")
        except BaseException as e:
            loi.append(f"{nguon}: {str(e)[:60]}")
    raise RuntimeError("Mọi nguồn giá đều lỗi (" + " | ".join(loi) + ")")


@lru_cache(maxsize=8)
def _nap_bang(san, st):
    return vnf.load(exchange=san, statement=st)


def lay_bctc_vnf(ma, so_nam=6):
    """Trả về dict {statement: bảng item_name x năm}. Rỗng nếu không có dữ liệu.
    Lý do thiếu dữ liệu được ghi vào LOI (khoá bắt đầu bằng 'bctc')."""
    for k in [k for k in LOI if k.startswith("bctc")]:
        LOI.pop(k)
    kq = {}
    if vnf is None:
        LOI["bctc"] = LOI.get("vnfinancialdata", "Chưa cài vnfinancialdata")
        return kq
    for st in STATEMENTS:
        thay_ma = False
        for san in ("HSX", "HNX"):
            try:
                df = _nap_bang(san, st)
            except Exception as e:
                LOI[f"bctc:{st}:{san}"] = f"Không tải được {st}/{san}: {type(e).__name__}: {e}.{_goi_y(e)}"
                continue
            c_ma = _cot(df, "ticker", "symbol", "stock_code", "code", "company_code")
            c_nam = _cot(df, "year", "fiscal_year", "period")
            c_gt = _cot(df, "value")
            c_ten = _cot(df, "item_name")
            if not all([c_ma, c_nam, c_gt, c_ten]):
                LOI[f"bctc:{st}:{san}"] = f"Tên cột không khớp code, dataset có các cột: {list(df.columns)}"
                continue
            d = df[df[c_ma].astype(str).str.upper() == ma]
            if d.empty:
                continue
            thay_ma = True
            d = d.copy()
            d[c_nam] = pd.to_numeric(d[c_nam], errors="coerce")
            d = d.dropna(subset=[c_nam, c_gt])
            nam = sorted(d[c_nam].astype(int).unique())[-so_nam:]
            d = d[d[c_nam].isin(nam)]
            bang = d.pivot_table(index=c_ten, columns=c_nam, values=c_gt, aggfunc="first")
            bang.columns = [int(c) for c in bang.columns]
            kq[st] = bang.dropna(how="all")
            break
        if not thay_ma and not any(k.startswith(f"bctc:{st}") for k in LOI):
            LOI[f"bctc:{st}"] = f"Mã {ma} không có trong dataset (chỉ hỗ trợ HSX, HNX, không có UPCOM)."
    return kq


def lay_ratio(ma):
    try:
        _can_vnstock()
        s = Vnstock().stock(symbol=ma, source="VCI")
        ratio = s.finance.ratio(period="year", lang="vi")
        if isinstance(ratio.columns, pd.MultiIndex):
            ratio.columns = [" ".join(map(str, c)).strip() for c in ratio.columns]
        LOI.pop("ratio", None)
        return ratio
    except Exception as e:
        LOI["ratio"] = f"Không lấy được chỉ số tài chính từ vnstock: {type(e).__name__}: {e}"
        return pd.DataFrame()


def _dnse(ma, loai, so_ngay):
    """Lấy nến ngày từ endpoint biểu đồ công khai của DNSE. loai: 'index' hoặc 'stock'."""
    den = int(datetime.now().timestamp())
    tu = int((datetime.now() - timedelta(days=so_ngay)).timestamp())
    r = requests.get(f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{loai}",
                     params={"symbol": ma, "resolution": "1D", "from": tu, "to": den}, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = pd.DataFrame({"time": pd.to_datetime(j["t"], unit="s") + pd.Timedelta(hours=7),
                      "open": j["o"], "high": j["h"], "low": j["l"], "close": j["c"], "volume": j["v"]})
    d["time"] = d["time"].dt.normalize()
    return d


def lay_vnindex(so_ngay=730):
    try:
        d = _dnse("VNINDEX", "index", so_ngay)
        if len(d) > 60:
            return d
    except BaseException:
        pass
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=so_ngay)).strftime("%Y-%m-%d")
    for nguon in ("VCI", "KBS", "TCBS", "MSN"):
        try:
            d = Vnstock().stock(symbol="VNINDEX", source=nguon).quote.history(start=start, end=end, interval="1D")
            if d is not None and len(d) > 60:
                d["time"] = pd.to_datetime(d["time"])
                return d
        except BaseException:
            continue
    return None

def lay_bctc(ma, so_nam=6):
    """vnfinancialdata trước, thiếu thì bổ sung từ vnstock."""
    kq = lay_bctc_vnf(ma, so_nam)
    if len(kq) >= 2:
        return kq
    try:
        from core.bctc_du_phong import lay_bctc_du_phong
        bo_sung = lay_bctc_du_phong(ma, so_nam)
    except Exception as e:
        LOI["bctc_du_phong"] = f"Nguồn dự phòng vnstock lỗi: {type(e).__name__}: {e}"
        return kq
    for k, v in bo_sung.items():
        kq.setdefault(k, v)
    if bo_sung:
        for key in [x for x in LOI if x.startswith("bctc")]:
            LOI.pop(key)
    else:
        LOI["bctc_du_phong"] = f"vnstock cũng không trả BCTC cho mã {ma}."
    return kq