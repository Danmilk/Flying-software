import json
from functools import wraps

SEATS_FILE = "data/seats.json"
FLIGHTS_FILE = "data/flights.json"


def load_json(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def validate_flight(flight_id):
    flights = load_json(FLIGHTS_FILE)
    for flight in flights:
        if flight["id"] == flight_id:
            return True
    return False


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
    def wrapper(flight_id, fila, columna, *args, **kwargs):
        if not validate_flight(flight_id):
            return {"success": False, "message": "El vuelo no existe"}

        seat, seats = find_seat(flight_id, fila, columna)
        if seat is None:
            return {"success": False, "message": "El asiento no existe"}

        if seat["ocupado"] is True:
            return {"success": False, "message": "El asiento ya está ocupado"}

        seat["ocupado"] = True
        save_json(SEATS_FILE, seats)
        print(f"Asiento {fila}{columna} del vuelo {flight_id} bloqueado")

        try:
            result = func(flight_id, fila, columna, *args, **kwargs)
            return result
        except Exception as error:
            seat["ocupado"] = False
            save_json(SEATS_FILE, seats)
            print("Error detectado. Asiento liberado nuevamente.")
            return {"success": False, "message": str(error)}
    return wrapper


@seat_lock_aspect
def lock_seat(flight_id, fila, columna):
    return {
        "success": True,
        "message": f"Asiento {fila}{columna} bloqueado correctamente"
    }


def unlock_seat(flight_id, fila, columna):
    seat, seats = find_seat(flight_id, fila, columna)
    if seat is None:
        return {"success": False, "message": "Asiento no encontrado"}
    seat["ocupado"] = False
    save_json(SEATS_FILE, seats)
    return {"success": True, "message": f"Asiento {fila}{columna} liberado"}
