import os
import sys

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


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_seats_for_flight(flight_id):
    import json
    data_path = os.path.join(os.path.dirname(__file__), "data", "seats.json")
    with open(data_path, encoding="utf-8") as f:
        seats = json.load(f)
    return [s for s in seats if s["flight_id"] == flight_id]


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
    search = FlightSearchAgent(flights, blocker)
    destinos = search.get_known_destinations("BUENOS AIRES")

    return render_template("destinations.html",
                           destinos=destinos,
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

    # Organizar en grilla {fila: {columna: seat}}
    seat_map = {}
    for s in seat_list:
        fila = s["fila"]
        col = s["columna"]
        if fila not in seat_map:
            seat_map[fila] = {}
        seat_map[fila][col] = s

    filas = sorted(seat_map.keys(), key=lambda x: int(x) if x.isdigit() else x)
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

    data = request.get_json()
    fila = data.get("fila")
    columna = data.get("columna")
    flight_id = session["flight_id"]
    passenger_name = session["passenger_name"]

    result = ComponenteLogicaReserva().recibir_datos_seleccion(
        flight_id=flight_id,
        fila=fila,
        columna=columna,
        passenger_name=passenger_name
    )

    if result and result["success"]:
        AgenteCierreVentas().ejecutar()
        socketio.emit("seat_booked", {
            "fila": fila,
            "columna": columna,
            "passenger_name": passenger_name
        }, room=f"flight_{flight_id}")
        session["last_booking"] = {"fila": fila, "columna": columna, "flight_id": flight_id}

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


# ── SocketIO events ───────────────────────────────────────────────────────────

@socketio.on("join_flight")
def on_join(data):
    flight_id = data.get("flight_id")
    if flight_id:
        join_room(f"flight_{flight_id}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
