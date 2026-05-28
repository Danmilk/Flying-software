import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, emit

from Agentes.buscador_vuelos import DataLoaderAgent, FlightSearchAgent, SeatBlockingAgent
from Agentes.AgenteCierreVentas import AgenteCierreVentas
from Componentes.catalogo import ComponenteCatalogo
from Componentes.reserva import ComponenteLogicaReserva

app = Flask(__name__)
app.secret_key = "vuelos_reserva_2026"
socketio = SocketIO(app, cors_allowed_origins="*")

_DATA = os.path.join(os.path.dirname(__file__), "data")

recent_bookings = []  # feed en memoria, máx 20 entradas


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read_json(filename):
    with open(os.path.join(_DATA, filename), encoding="utf-8") as f:
        return json.load(f)


def get_seats_for_flight(flight_id):
    return [s for s in _read_json("seats.json") if s["flight_id"] == flight_id]


def get_flight_info(flight_id):
    return next((f for f in _read_json("flights.json") if f["id"] == flight_id), None)


def get_all_flights_data():
    flights = _read_json("flights.json")
    seats   = _read_json("seats.json")
    result  = []
    for fl in flights:
        fid = fl["id"]
        fl_seats = [s for s in seats if s["flight_id"] == fid]
        result.append({
            "id":               fid,
            "origin":           fl["origin"],
            "destination":      fl["destination"],
            "date":             fl["date"],
            "seats_available":  fl["seats_available"],
            "seats":            fl_seats,
        })
    return result


def format_date(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        months = ["ENE","FEB","MAR","ABR","MAY","JUN",
                  "JUL","AGO","SEP","OCT","NOV","DIC"]
        return f"{d.day:02d} {months[d.month - 1]} {d.year}"
    except Exception:
        return date_str


def add_to_feed(flight_id, destination, fila, columna, passenger_name):
    global recent_bookings
    recent_bookings.insert(0, {
        "time":           datetime.now().strftime("%H:%M:%S"),
        "flight_id":      flight_id,
        "destination":    destination,
        "fila":           fila,
        "columna":        columna,
        "passenger_name": passenger_name,
    })
    recent_bookings = recent_bookings[:20]


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "passenger_name" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("destinations"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip().upper()
        if name:
            session["passenger_name"] = name
            return redirect(url_for("destinations"))
        return render_template("login.html", error="El nombre no puede estar vacío.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/destinations", methods=["GET", "POST"])
def destinations():
    if "passenger_name" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        destination = request.form.get("destination")
        if destination:
            session["destination"] = destination
            return redirect(url_for("catalog"))

    flights = DataLoaderAgent.load_flights()
    seats_idx = DataLoaderAgent.load_seats(flights)
    blocker = SeatBlockingAgent(seats_idx, flights)
    search  = FlightSearchAgent(flights, blocker)
    destinos = search.get_known_destinations("BUENOS AIRES")

    catalogo = ComponenteCatalogo()
    dest_totals = {}
    for v in catalogo.vuelos:
        d = v["destino"]
        dest_totals[d] = dest_totals.get(d, 0) + v["asientos_disponibles"]

    return render_template("destinations.html",
                           destinos=destinos,
                           dest_totals=dest_totals,
                           passenger_name=session["passenger_name"])


@app.route("/catalog", methods=["GET", "POST"])
def catalog():
    if "passenger_name" not in session:
        return redirect(url_for("login"))
    if "destination" not in session:
        return redirect(url_for("destinations"))

    if request.method == "POST":
        flight_id = request.form.get("flight_id")
        if flight_id:
            session["flight_id"] = flight_id
            return redirect(url_for("seats"))

    catalogo = ComponenteCatalogo()
    vuelos = [v for v in catalogo.vuelos if v["destino"] == session["destination"]]

    return render_template("catalog.html",
                           vuelos=vuelos,
                           destination=session["destination"],
                           passenger_name=session["passenger_name"])


@app.route("/seats")
def seats():
    if "passenger_name" not in session:
        return redirect(url_for("login"))
    if "flight_id" not in session:
        return redirect(url_for("catalog"))

    flight_id = session["flight_id"]
    seat_list = get_seats_for_flight(flight_id)

    seat_map = {}
    for s in seat_list:
        fila = s["fila"]
        col  = s["columna"]
        seat_map.setdefault(fila, {})[col] = s

    filas    = sorted(seat_map.keys(), key=lambda x: int(x) if x.isdigit() else x)
    columnas = ["A", "B"]

    return render_template("seats.html",
                           flight_id=flight_id,
                           seat_map=seat_map,
                           filas=filas,
                           columnas=columnas,
                           passenger_name=session["passenger_name"],
                           destination=session.get("destination", ""))


@app.route("/book", methods=["POST"])
def book():
    if "passenger_name" not in session or "flight_id" not in session:
        return jsonify({"success": False, "message": "Sesión inválida"}), 401

    data           = request.get_json()
    fila           = data.get("fila")
    columna        = data.get("columna")
    flight_id      = session["flight_id"]
    passenger_name = session["passenger_name"]

    result = ComponenteLogicaReserva().recibir_datos_seleccion(
        flight_id=flight_id,
        fila=fila,
        columna=columna,
        passenger_name=passenger_name
    )

    if result and result["success"]:
        AgenteCierreVentas().ejecutar()

        flight_info = get_flight_info(flight_id)
        destination = flight_info["destination"] if flight_info else ""
        date_str    = flight_info["date"]        if flight_info else ""

        # Lee el contador actualizado después de que AgenteCierreVentas corrió
        updated_flight = get_flight_info(flight_id)
        seats_available = updated_flight["seats_available"] if updated_flight else 0

        add_to_feed(flight_id, destination, fila, columna, passenger_name)

        payload = {
            "fila":             fila,
            "columna":          columna,
            "passenger_name":   passenger_name,
            "flight_id":        flight_id,
            "destination":      destination,
            "seats_available":  seats_available,
            "time":             datetime.now().strftime("%H:%M:%S"),
        }

        # Evento específico de vuelo (para la página de asientos)
        socketio.emit("seat_booked", payload, room=f"flight_{flight_id}")
        # Broadcast global (para catálogo y monitor)
        socketio.emit("seat_booked_global", payload)

        session["last_booking"] = {
            "fila":        fila,
            "columna":     columna,
            "flight_id":   flight_id,
            "destination": destination,
            "date":        format_date(date_str),
            "origin":      "BUENOS AIRES",
        }

    return jsonify(result)


@app.route("/confirmation")
def confirmation():
    if "passenger_name" not in session:
        return redirect(url_for("login"))
    booking = session.get("last_booking")
    if not booking:
        return redirect(url_for("destinations"))
    return render_template("confirmation.html",
                           passenger_name=session["passenger_name"],
                           booking=booking)


@app.route("/monitor")
def monitor():
    flights_data = get_all_flights_data()
    grouped = {}
    for fl in flights_data:
        dest = fl["destination"]
        grouped.setdefault(dest, []).append(fl)
    return render_template("monitor.html",
                           grouped=grouped,
                           feed=recent_bookings)


@app.route("/api/monitor-data")
def monitor_data():
    return jsonify(get_all_flights_data())


# ── SocketIO events ───────────────────────────────────────────────────────────

@socketio.on("join_flight")
def on_join_flight(data):
    flight_id = data.get("flight_id")
    if flight_id:
        join_room(f"flight_{flight_id}")


@socketio.on("join_monitor")
def on_join_monitor():
    join_room("monitors")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
