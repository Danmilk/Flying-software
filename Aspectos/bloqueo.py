import json
import os
from functools import wraps

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
SEATS_FILE   = os.path.join(_BASE, "seats.json")
FLIGHTS_FILE = os.path.join(_BASE, "flights.json")


def load_json(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def validate_flight(flight_id):
    flights = load_json(FLIGHTS_FILE)
    return any(f["id"] == flight_id for f in flights)


def find_seat(flight_id, fila, columna):
    seats = load_json(SEATS_FILE)
    for seat in seats:
        if (
            seat["flight_id"] == flight_id
            and seat["fila"] == str(fila)
            and seat["columna"] == str(columna)
        ):
            return seat, seats
    return None, seats


def seat_lock_aspect(func):
    @wraps(func)
    def wrapper(flight_id, fila, columna, passenger_name="", *args, **kwargs):
        if not validate_flight(flight_id):
            return {"success": False, "message": "El vuelo no existe"}

        seat, seats = find_seat(flight_id, fila, columna)
        if seat is None:
            return {"success": False, "message": "El asiento no existe"}

        if seat["ocupado"] is True:
            return {"success": False, "message": "El asiento ya está ocupado"}

        seat["ocupado"] = True
        seat["passenger_name"] = passenger_name
        save_json(SEATS_FILE, seats)

        try:
            result = func(flight_id, fila, columna, passenger_name, *args, **kwargs)
            return result
        except Exception as error:
            seat["ocupado"] = False
            seat["passenger_name"] = ""
            save_json(SEATS_FILE, seats)
            return {"success": False, "message": str(error)}
    return wrapper


@seat_lock_aspect
def lock_seat(flight_id, fila, columna, passenger_name=""):
    return {
        "success": True,
        "message": f"Asiento {fila}{columna} reservado para {passenger_name} en vuelo {flight_id}"
    }
