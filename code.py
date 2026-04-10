import time
import displayio
from secrets import secrets
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import bitmap_label
from adafruit_bitmap_font import bitmap_font
from adafruit_imageload import load

#config
#------------------------
PROXY_URL = secrets["PROXY_URL"]
REFRESH_INTERVAL = 15

# list of stops to rotate through
STOPS = [
    {"id": "13915", "name": "CALTRAIN"},
    {"id": "13914", "name": "OCEAN BEACH"},
]

ROUTE_CODE = "N"
ROUTE_NAME = "JUDAH"

FONT_FILE = "/fonts/Arial-12.bdf"
MUNI_ORANGE = 0xFC7E00

#matrixportal setup
#-------------------------
matrixportal = MatrixPortal(status_neopixel=None)

print("Connecting to Wi-Fi...")
matrixportal.network.connect()
print("Connected to Wi-Fi!")
print("IP Address:", matrixportal.network.ip_address)

#check if display is allowed based on PST 24-hour time
def display_allowed(time_24hr=None):
    hour = 8
    if time_24hr:
        try:
            parts = time_24hr.strip().split(":")
            if len(parts) >= 1:
                hour = int(parts[0])
        except ValueError:
            print("Could not parse hour from:", time_24hr)
            hour = 8

    print("Current PST hour:", hour)
    return 7 <= hour < 22  # only allow display times

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
bottom_lines.anchored_position = (0, 12)
group.append(bottom_lines)

matrixportal.display.root_group = group

#fetch stop data task (calls proxy)
#-----------------------------------
def get_stop_data(stop_id):
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
        print("Error fetching stop data:", e)
        return []

#fetch time/date task (calls proxy)
#-----------------------------------
def get_time_data():
    url = f"{PROXY_URL}/?time=true"
    try:
        response = matrixportal.network.fetch(url)
        data = response.json()
        response.close()


        return (
            data.get("weekday"),
            data.get("date"),
            data.get("time_12hr"),
            data.get("time_24hr")
        )

    except Exception as e:
        print("Error fetching time data:", e)
        return None, None, None, None

#display loop
#-------------------------
current_screen_index = 0

while True:
    weekday, date_str, time_12hr, time_24hr = get_time_data()

    if display_allowed(time_24hr):
        matrixportal.display.brightness = 1.0

        is_stop_screen = current_screen_index < len(STOPS)

        if is_stop_screen:
            #stop screen
            current_stop = STOPS[current_screen_index]
            stop_id = current_stop["id"]
            stop_name = current_stop["name"]
            minutes = get_stop_data(stop_id)
            minutes_text = ", ".join(str(m) for m in minutes) + "m" if minutes else "No arrivals"

            n_icon.hidden = False
            top_line.anchored_position = (14, 0)
            top_line.text = ROUTE_NAME
            bottom_lines.anchored_position = (0, 12)
            bottom_lines.text = f"{stop_name}\n{minutes_text}"

            total_screens = len(STOPS) + 1
            current_screen_index = (current_screen_index + 1) % total_screens

            time.sleep(REFRESH_INTERVAL)

        else:
            #time screen
            n_icon.hidden = True
            top_line.anchored_position = (0, 0)

            time_str_only = time_12hr[:-3]
            hour, minute, second = map(int, time_str_only.split(":"))
            am_pm = time_12hr[-2:]

            seconds_elapsed = 0

            top_line.text = weekday
            bottom_lines.anchored_position = (0, 12)
            time_no_seconds = time_12hr[:-6] + " " + time_12hr[-2:]
            bottom_lines.text = f"{date_str}\n{time_no_seconds}"

            time.sleep(REFRESH_INTERVAL)

            current_screen_index = 0
    else:
        #hide display outside hours
        matrixportal.display.brightness = 0
        n_icon.hidden = True
        top_line.text = ""
        bottom_lines.text = ""
        print("Outside display hours")
        time.sleep(300)
