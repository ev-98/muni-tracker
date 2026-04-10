from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import requests
import json

app = Flask(__name__)
API_KEY = "insert key here"


def iso_to_minutes(iso_time):
    if not iso_time:
        print("Missing ETA time")
        return None

    try:
        eta = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = eta - now
        minutes = int(delta.total_seconds() / 60)

        print(
            f"ETA raw: {iso_time} | "
            f"ETA parsed: {eta.isoformat()} | "
            f"Now: {now.isoformat()} | "
            f"Δsec: {int(delta.total_seconds())} | "
            f"Minutes: {minutes}"
        )

        return minutes if minutes >= 0 else None

    except Exception as e:
        print("Failed to parse ETA:", iso_time, "Error:", e)
        return None


@app.route("/", methods=["GET"])
def proxy():
    stop = request.args.get("stop")
    time_screen = request.args.get("time")

    try:
        result = {}

        #time screen request
        #-------------------------
        if time_screen:
            now_utc = datetime.now(timezone.utc)
            pst_dt = datetime.now(ZoneInfo("America/Los_Angeles"))

            # 12-hour time with am/pm
            time_12hr = pst_dt.strftime("%I:%M:%S %p").lstrip("0")
            # 24-hour time
            time_24hr = pst_dt.strftime("%H:%M:%S")

            result = {
                "weekday": pst_dt.strftime("%A"),
                "date": pst_dt.strftime("%m/%d/%Y"),
                "time_12hr": time_12hr,
                "time_24hr": time_24hr
            }

            return jsonify(result)


        #stop arrivals request
        #-------------------------
        if not stop:
            return jsonify({"error": "Missing stop"}), 400

        url = (
            "http://api.511.org/transit/StopMonitoring"
            f"?agency=SF&api_key={API_KEY}&stopCode={stop}&format=json"
        )

        print("Fetching URL:", url)
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        json_text = r.content.decode("utf-8-sig").strip()
        data = json.loads(json_text)

        arrivals = []

        visits = (
            data.get("ServiceDelivery", {})
                .get("StopMonitoringDelivery", {})
                .get("MonitoredStopVisit", [])
        )

        for visit in visits:
            vehicle = visit.get("MonitoredVehicleJourney", {})
            line = vehicle.get("PublishedLineName", "Unknown")

            call = vehicle.get("MonitoredCall", {})
            eta_iso = call.get("ExpectedArrivalTime") or call.get("AimedArrivalTime")

            if eta_iso:
                minutes = iso_to_minutes(eta_iso)
                if minutes is not None:
                    arrivals.append({
                        "line": line,
                        "minutes": minutes
                    })

        arrivals.sort(key=lambda x: x["minutes"])

        #include ISO time for board fallback if needed
        current_time_iso = datetime.now(timezone.utc).isoformat(timespec='seconds')

        result = {
            "stop": stop,
            "current_time": current_time_iso,
            "arrivals": arrivals[:3]  # next 3 only
        }

        print(
            f"Fetched {len(result['arrivals'])} arrivals "
            f"for stop {stop} | Current time: {current_time_iso}"
        )

        return jsonify(result)

    except Exception as e:
        print(f"Exception occurred while fetching 511 data for stop {stop}: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
