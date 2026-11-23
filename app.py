"""NASA APOD beginner Flask app, compatible with Vercel's Python runtime."""
from datetime import date, datetime
import os
import random

import requests
from flask import Flask, render_template, request

app = Flask(__name__)
NASA_APOD_URL = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
REQUEST_TIMEOUT = 10
FIRST_APOD_DATE = date(1995, 6, 16)
NASA_API_KEY = os.getenv("NASA_API_KEY", "").strip() or "DEMO_KEY"
KEY_LABEL = "自訂 NASA_API_KEY（新版端點不需金鑰）" if NASA_API_KEY != "DEMO_KEY" else "DEMO_KEY（新版端點不需金鑰）"


class ApodError(Exception):
    """A safe, user-facing APOD request error."""


def to_legacy_date(value: str) -> str:
    """Validate YYYY-MM-DD and convert to the endpoint's YYMMDD filter."""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ApodError("日期格式不正確，請使用 YYYY-MM-DD。") from exc
    if parsed < FIRST_APOD_DATE:
        raise ApodError("APOD 資料始於 1995-06-16，請選擇該日或之後的日期。")
    if parsed > date.today():
        raise ApodError("尚無未來日期的每日天文圖，請選擇今天或之前的日期。")
    return parsed.strftime("%y%m%d")


def fetch_apods(params: dict | None = None) -> list[dict]:
    """Fetch and normalize APOD records from NASA's official endpoint."""
    try:
        response = requests.get(NASA_APOD_URL, params=params or {}, timeout=REQUEST_TIMEOUT)
        if response.status_code == 429:
            raise ApodError("NASA 服務目前請求過於頻繁（429），請稍後再試。")
        response.raise_for_status()
        payload = response.json()
    except ApodError:
        raise
    except requests.Timeout as exc:
        raise ApodError("連線 NASA 服務逾時，請稍後再試。") from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "未知"
        raise ApodError(f"NASA 服務回應錯誤（HTTP {status}），請稍後再試。") from exc
    except requests.RequestException as exc:
        raise ApodError("目前無法連線 NASA 服務，請檢查網路後再試。") from exc
    except ValueError as exc:
        raise ApodError("NASA 回傳的資料格式無法讀取，請稍後再試。") from exc

    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ApodError("NASA 回傳的資料格式不符合預期，請稍後再試。")
    return [item for item in payload if isinstance(item, dict)]


def get_today_apod() -> list[dict]:
    today = date.today()
    records = fetch_apods({"date_from": today.strftime("%y%m%d"), "date_to": today.strftime("%y%m%d")})
    # On days when today's post is not published yet, show the newest available record.
    return records or fetch_apods({"per_page": 1})


@app.route("/", methods=["GET", "POST"])
def index():
    records: list[dict] = []
    error = None
    mode = "today"
    date_value = ""
    start_value = ""
    end_value = ""

    try:
        if request.method == "POST":
            mode = request.form.get("mode", "date")
            if mode == "date":
                date_value = request.form.get("date", "").strip()
                compact = to_legacy_date(date_value)
                records = fetch_apods({"date_from": compact, "date_to": compact})
            elif mode == "range":
                start_value = request.form.get("start_date", "").strip()
                end_value = request.form.get("end_date", "").strip()
                start_compact, end_compact = to_legacy_date(start_value), to_legacy_date(end_value)
                if start_value > end_value:
                    raise ApodError("起始日期不可晚於結束日期。")
                # The upstream API caps per_page at 25. Fetch one page for a beginner-friendly archive view.
                records = fetch_apods({"date_from": start_compact, "date_to": end_compact, "per_page": 25})
            elif mode == "random":
                try:
                    count = int(request.form.get("count", "3"))
                except ValueError as exc:
                    raise ApodError("抽取張數請填寫 1 到 25 的整數。") from exc
                if not 1 <= count <= 25:
                    raise ApodError("抽取張數請介於 1 到 25。")
                pool = fetch_apods({"per_page": 25})
                records = random.sample(pool, min(count, len(pool)))
            else:
                raise ApodError("查詢方式無效，請重新操作。")
        else:
            records = get_today_apod()
    except ApodError as exc:
        error = str(exc)

    if request.method == "POST" and not error and not records:
        error = "這段日期沒有找到 APOD 資料，請調整日期後再試。"
    return render_template("index.html", records=records, error=error, mode=mode,
                           date_value=date_value, start_value=start_value,
                           end_value=end_value, key_label=KEY_LABEL)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
