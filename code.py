import time
import displayio
from secrets import secrets
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import bitmap_label
from adafruit_bitmap_font import bitmap_font
from adafruit_imageload import load  # for BMP icon
import adafruit_ntp

#config
#------------------------
PROXY_URL = secrets["PROXY_URL"]
STOP_ID = "13915"
REFRESH_INTERVAL = 30  # seconds

ROUTE_CODE = "N"
ROUTE_NAME = "CALTRAIN"
STOP_NAME = "STANYAN"

FONT_FILE = "/fonts/Arial-12.bdf"
MUNI_ORANGE = 0xFC7E00

#matrixportal setup
#-------------------------
matrixportal = MatrixPortal(status_neopixel=None)

print("Connecting to Wi-Fi...")
matrixportal.network.connect()
print("Connected to Wi-Fi!")
print("IP Address:", matrixportal.network.ip_address)

# wip, screen to turn off (sleep mode) between 10p and 7a pst
def get_current_time_struct():
    """Fetch current time from proxy and convert to struct_time"""
    try:
        response = matrixportal.network.fetch(f"{PROXY_URL}/?stop={STOP_ID}")
        data = response.json()
        response.close()

        current_iso = data.get("current_time")
        if current_iso:
            # Convert ISO string to struct_time (ignore microseconds/Z)
            t = time.struct_time((
                date_parts[0],  # year
                date_parts[1],  # month
                date_parts[2],  # day
                time_parts[0],  # hour
                time_parts[1],  # minute
                time_parts[2],  # second
                -1,             # weekday
                -1,             # yearday
                -1              # isdst
))
            return t
            print(t)
    except Exception as e:
        print("Failed to fetch current time:", e)
    return None

def display_allowed():
    """Return True if current hour is between 7am and 10pm PST"""
    t = get_current_time_struct()
    if t:
        hour = t.tm_hour
    else:
        # fallback if time fetch fails
        hour = 8
    print("Current PST hour:", hour)
    return 7 <= hour < 22


#display setup
#------------------------
group = displayio.Group()

#font
font = bitmap_font.load_font(FONT_FILE)

#load 12x12 N icon
n_bitmap, n_palette = load("/n_icon.bmp")
n_icon = displayio.TileGrid(n_bitmap, pixel_shader=n_palette, x=0, y=0)
group.append(n_icon)

#top line label for route name (shifted right for icon)
top_line = bitmap_label.Label(
    font,
    text=ROUTE_NAME,
    color=MUNI_ORANGE
)
top_line.anchor_point = (0, 0)
top_line.anchored_position = (14, 0)  # 12px icon + 2px padding
group.append(top_line)

#second label for stop name and minutes (normal alignment)
bottom_lines = bitmap_label.Label(
    font,
    text="Loading…",
    color=MUNI_ORANGE
)
bottom_lines.anchor_point = (0, 0)
bottom_lines.anchored_position = (0, 12)  # reduced spacing from 14 → 12
group.append(bottom_lines)

matrixportal.display.root_group = group

#fetch arrivals task (calls proxy)
#-----------------------------------
def get_muni_minutes(stop_id):
    url = f"{PROXY_URL}/?stop={stop_id}"
    try:
        response = matrixportal.network.fetch(url)
        data = response.json()
        response.close()

        minutes = []
        for item in data.get("arrivals", []):
            m = item.get("minutes")
            if isinstance(m, int):
                minutes.append(m)

        return minutes[:3]

    except Exception as e:
        print("Error fetching arrivals:", e)
        return []

#display loop
#-------------------------
while True:
    if display_allowed():
        matrixportal.display.brightness = 1.0
        minutes = get_muni_minutes(STOP_ID)

        if minutes:
            minutes_text = ", ".join(str(m) for m in minutes) + "m"
        else:
            minutes_text = "No arrivals"

        top_line.text = ROUTE_NAME
        bottom_lines.text = f"{STOP_NAME}\n{minutes_text}"

        print(ROUTE_NAME, STOP_NAME, minutes_text)

        time.sleep(REFRESH_INTERVAL)
    else:
        matrixportal.display.brightness = 0
        top_line.text = ""
        bottom_lines.text = ""
        print("Outside display hours")
        time.sleep(300)
