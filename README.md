# muni-tracker LED Display

## Overview
A custom-built transit display powered by CircuitPython that shows real-time San Francisco MUNI arrival information alongside the current time. The display is designed to mimic the look and feel of classic MUNI signage, creating a functional and aesthetic piece for everyday use.

This project runs on an Adafruit MatrixPortal M4 connected to an LED matrix display, cycling between inbound/outbound arrival times and the current time.

---

## Background
This project started as a Christmas gift idea for someone who lives right off a MUNI line and relies on it daily.

Instead of checking a phone, the display provides quick, ambient access to arrival times in a format inspired by the physical signage seen throughout San Francisco.

---

## Hardware Setup

### Materials
- MatrixPortal M4  
- LED Matrix Display  
- Raspberry Pi Zero 2 W (for proxy server)

---

## Software Structure

### `code.py`
- Main CircuitPython script running on the MatrixPortal  
- Fetches processed transit data from the proxy server  
- Displays:
  - Next 3 arrival times (in minutes)
  - Alternates between inbound and outbound directions
  - Current time display
- Uses hardcoded:
  - Stop code
  - Line name
  - Direction labels  

> Note: These values should be updated to match your target stop and route.

> Note: There is code implemented to translate the current time to PST, as well as turn the display screen off between the hours of 11p and 7a. These can be adjusted in the 'display_allowed' funciton.

---

### `proxy.py`
- Runs on the Raspberry Pi Zero 2 W  
- Handles:
  - API requests to the 511 MUNI service  
  - Time retrieval  
  - Data parsing and formatting  
- Serves simplified data to the MatrixPortal over the local network  
- Configured to run continuously on boot  

---

### `secrets.py` (not included in repo)
Should contain:
- WiFi SSID  
- WiFi password  
- Local IP address of the Raspberry Pi

File structure:
```python
secrets = {
    # insert your wifi username and pass here
    "ssid": "insert ssid",
    "password": "insert password",

    # don't touch unless authorized
    "PROXY_URL": "insert ip of pi"
}
```

---

## Replication Guide (High-Level)

1. Assemble MatrixPortal + LED display  
2. Set up Raspberry Pi Zero 2 W with `proxy.py` running on boot  
3. Configure `secrets.py` with your network credentials  
4. Update hardcoded stop/route values in `code.py`  
5. Deploy `code.py` to the MatrixPortal  
6. Power both devices on the same network  
7. Verify data is being served and displayed correctly  

---

## Notes / Limitations

- The MatrixPortal M4 has limitations handling the raw API response format directly  
- Because of this, a proxy server is used to:
  - Fetch  
  - Decode  
  - Simplify the data before sending it to the device  

> Note: This architecture could be simplified by using an ESP32-class board instead of the M4, which typically have both built in wi-fi support and the ability to handle built-in JSON parsing

---

## Future Improvements

- Add STL file for a custom backing cover to hide rear wiring  
- Refine display housing / enclosure design  
- Improve on-device parsing to remove proxy dependency  

---

## bart-tracker

- A future alternative version of this project will replicate BART station displays  
- Goals:
  - Match visual style of BART signage  
  - Similar real-time functionality  
  - Fully integrated hardware and enclosure, perhaps using different materials like wood for backing case

---

## 
