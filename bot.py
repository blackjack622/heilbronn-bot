import json
from datetime import datetime, timedelta
from pathlib import Path

import requests

# =========================
# BURAYI DOLDUR
# =========================
TOKEN = "8677644764:AAHijkweDAV22MyQejQk5JoEJGAidGcP-Jw"
CHAT_ID = "618746044"

SERVICE_ID = 144511
DAYS_TO_SCAN = 270

STATE_FILE = Path("state.json")
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


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_notified_earliest": None}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
            print(f"{date_str} için uygun veri yok. HTTP {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:
        print(f"Hata (date={date_str}): {e}")
        return []


def extract_earliest_slot(slots):
    if not slots:
        return None

    starts = []

    for slot in slots:
        start = slot.get("start")
        if not start:
            continue

        try:
            starts.append(datetime.fromisoformat(start))
        except Exception:
            pass

    if not starts:
        return None

    return min(starts)


def find_earliest_appointment():
    today = datetime.now().date()

    for i in range(DAYS_TO_SCAN + 1):
        current_date = today + timedelta(days=i)
        date_str = current_date.isoformat()

        print(f"Kontrol ediliyor: {date_str}")

        slots = fetch_timeslots_for_date(date_str)
        if not slots:
            continue

        earliest = extract_earliest_slot(slots)
        if earliest is not None:
            return earliest, slots

    return None, []


def main():
    state = load_state()

    earliest, slots = find_earliest_appointment()

    if earliest is None:
        print("Hiç randevu bulunamadı.")
        return

    print("Bulunan en erken randevu:", earliest.isoformat())

    earliest_iso = earliest.isoformat()
    last_notified = state.get("last_notified_earliest")

    if last_notified is None:
        send_message(
            "İlk bulunan en erken randevu:\n"
            f"{earliest.strftime('%d.%m.%Y %H:%M')}\n"
            f"{REFERER}"
        )
        state["last_notified_earliest"] = earliest_iso
        save_state(state)
        return

    last_dt = datetime.fromisoformat(last_notified)

    if earliest < last_dt:
        send_message(
            "Daha erken randevu bulundu!\n"
            f"{earliest.strftime('%d.%m.%Y %H:%M')}\n"
            f"{REFERER}"
        )
        state["last_notified_earliest"] = earliest_iso
        save_state(state)
    else:
        print("Daha erken randevu yok.")


if __name__ == "__main__":
    main()