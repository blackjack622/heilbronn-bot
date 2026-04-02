import os
from datetime import datetime, timedelta

import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SERVICE_ID = 144511
DAYS_TO_SCAN = 270

BASE_URL = "https://www.etermin.net/api/timeslots"
REFERER = "https://www.etermin.net/qtermin-stadtheilbronn-abh"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": REFERER,
}


def send_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    print("Telegram cevabı:", response.text)
    response.raise_for_status()


def fetch_timeslots_for_date(date_str: str):
    params = {
        "date": date_str,
        "serviceid": str(SERVICE_ID),
        "capacity": "1",
        "caching": "false",
        "duration": "20",
        "cluster": "false",
        "slottype": "0",
        "fillcalendarstrategy": "0",
        "showavcap": "false",
        "appfuture": "270",
        "appdeadline": "480",
        "msdcm": "0",
        "oneoff": "null",
        "appdeadlinewm": "1",
        "tz": "W. Europe Standard Time",
        "tzaccount": "W. Europe Standard Time",
        "calendarid": "",
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            print(f"{date_str} → veri yok (HTTP {response.status_code})")
            return []

        data = response.json()
        if not isinstance(data, list):
            return []

        return data

    except Exception as e:
        print(f"Hata ({date_str}): {e}")
        return []


def extract_earliest_slot(slots):
    if not slots:
        return None

    times = []
    for slot in slots:
        start = slot.get("start")
        if start:
            try:
                times.append(datetime.fromisoformat(start))
            except Exception:
                pass

    if not times:
        return None

    return min(times)


def find_earliest_appointment():
    today = datetime.now().date()

    for i in range(DAYS_TO_SCAN + 1):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.isoformat()

        print(f"Kontrol ediliyor: {date_str}")
        slots = fetch_timeslots_for_date(date_str)

        if not slots:
            continue

        earliest = extract_earliest_slot(slots)
        if earliest:
            return earliest

    return None


def main():
    earliest = find_earliest_appointment()

    if earliest is None:
        send_message("Şu anda uygun randevu bulunamadı.")
        return

    send_message(
        "En erken randevu:\n"
        f"{earliest.strftime('%d.%m.%Y %H:%M')}\n"
        f"{REFERER}"
    )


if __name__ == "__main__":
    main()
