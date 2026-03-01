from flask import Flask, request, jsonify
from datetime import datetime, timezone
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

        #  DEBUG OUTPUT
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
    if not stop:
        return jsonify({"error": "Missing stop"}), 400

    url = (
        "http://api.511.org/transit/StopMonitoring"
        f"?agency=SF&api_key={API_KEY}&stopCode={stop}&format=json"
    )

    print("Fetching URL:", url)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        # Handle UTF-8 BOM safely
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
            eta_iso = (
                call.get("ExpectedArrivalTime")
                or call.get("AimedArrivalTime")
            )

            if eta_iso:
                minutes = iso_to_minutes(eta_iso)
                if minutes is not None:
                    arrivals.append({
                        "line": line,
                        "minutes": minutes
                    })

        # Sort by soonest arrival
        arrivals.sort(key=lambda x: x["minutes"])

        result = {
            "stop": stop,
            "arrivals": arrivals[:3]  # next 3 only
        }

        print(
            f"Fetched {len(result['arrivals'])} arrivals "
            f"for stop {stop}"
        )

        return jsonify(result)

    except Exception as e:
        print(f"Exception occurred while fetching 511 data for stop {stop}: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Listen on all interfaces so MatrixPortal can reach it
    app.run(host="0.0.0.0", port=8000, debug=True)
