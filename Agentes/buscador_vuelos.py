import sys
import io

# Force the standard output to encode in UTF-8, overriding Windows CP1252
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    
"""
============================================================
 SISTEMA DE BÚSQUEDA DE VUELOS - AGENTES AUTÓNOMOS
 Archivo: Agentes/buscador_vuelos.py
 Datos  : ../data/flights.json  y  ../data/seats.json
============================================================

Agentes:
  • DataLoaderAgent   → carga y valida los JSON desde ../data/
  • FlightSearchAgent → busca y ordena vuelos por asientos disponibles
  • SeatBlockingAgent → gestiona bloqueos de asientos (compras)
  • InterfaceAgent    → valida entradas y coordina la experiencia

HOOK PARA AGENTE EXTERNO DE COMPRAS:
  Ver SeatBlockingAgent.receive_block_update()
  y   SeatBlockingAgent.receive_bulk_update()
"""

import json
import os
import time
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
#  PATHS — relativo a Agentes/buscador_vuelos.py
# ─────────────────────────────────────────────

BASE_DIR  = Path(__file__).resolve().parent.parent  # sube de Agentes/ a Flying-software/
DATA_DIR  = BASE_DIR / "data"
FLIGHTS_FILE = DATA_DIR / "flights.json"
SEATS_FILE   = DATA_DIR / "seats.json"


# ─────────────────────────────────────────────
#  AGENTE CARGADOR DE DATOS
# ─────────────────────────────────────────────

class DataLoaderAgent:
    """
    Agente autónomo responsable de cargar y validar los datos desde los JSON.
    Convierte la lista plana de asientos en un índice dict para acceso O(1).

    Propiedades del agente:
      • Autonomía    → detecta y reporta errores de datos sin intervención
      • Reactividad  → informa con claridad si los archivos no existen o están corruptos
    """

    @staticmethod
    def load_flights() -> list:
        """Carga flights.json y retorna lista de vuelos."""
        if not FLIGHTS_FILE.exists():
            raise FileNotFoundError(
                f"\n  ✖  No se encontró: {FLIGHTS_FILE}"
                f"\n     Verifique que exista el archivo data/flights.json en el proyecto."
            )
        try:
            with open(FLIGHTS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"\n  ✖  flights.json tiene formato inválido: {e}")

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("\n  ✖  flights.json debe ser una lista de vuelos no vacía.")

        # Validar campos mínimos requeridos
        required = {"id", "origin", "destination", "date", "seats_available"}
        for i, flight in enumerate(data):
            missing = required - set(flight.keys())
            if missing:
                raise ValueError(f"\n  ✖  Vuelo #{i} le faltan campos: {missing}")

        return data

    @staticmethod
    def load_seats(flights: list) -> dict:
        """
        Carga seats.json y convierte la lista plana en:
          { flight_id: { "1A": {seat_obj}, "1B": {seat_obj}, ... }, ... }
        """
        if not SEATS_FILE.exists():
            raise FileNotFoundError(
                f"\n  ✖  No se encontró: {SEATS_FILE}"
                f"\n     Verifique que exista el archivo data/seats.json en el proyecto."
            )
        try:
            with open(SEATS_FILE, encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"\n  ✖  seats.json tiene formato inválido: {e}")

        if not isinstance(raw, list):
            raise ValueError("\n  ✖  seats.json debe ser una lista de asientos.")

        # Construir índice { flight_id -> { seat_key -> seat_obj } }
        index = {}
        for seat in raw:
            fid = seat.get("flight_id", "").strip().upper()
            fila = str(seat.get("fila", "")).strip()
            col  = str(seat.get("columna", "")).strip().upper()
            if not fid or not fila or not col:
                continue
            seat_key = f"{fila}{col}"
            if fid not in index:
                index[fid] = {}
            index[fid][seat_key] = {
                "flight_id":      fid,
                "fila":           fila,
                "columna":        col,
                "passenger_name": seat.get("passenger_name", ""),
                "ocupado":        bool(seat.get("ocupado", False))
            }

        # Recalcular seats_available desde el estado real de seats.json
        for flight in flights:
            fid = flight["id"].strip().upper()
            if fid in index:
                libres = sum(1 for s in index[fid].values() if not s["ocupado"])
                flight["seats_available"] = libres

        return index


# ─────────────────────────────────────────────
#  AGENTE BLOQUEADOR DE ASIENTOS
# ─────────────────────────────────────────────

class SeatBlockingAgent:
    """
    Agente autónomo que gestiona el bloqueo de asientos cuando se realiza una compra.

    Propiedades del agente:
      • Autonomía    → actualiza el estado sin intervención humana
      • Reactividad  → responde a eventos de compra en tiempo real
      • Adaptabilidad → acepta actualizaciones externas vía hooks

    ════════════════════════════════════════════════
    HOOK PARA AGENTE EXTERNO (agente de compras)
    ════════════════════════════════════════════════
    Para integrar con el agente de compras externo, usar:

        # Bloquear un asiento individual:
        blocking_agent.receive_block_update("FL001", "2A", "Juan Pérez")

        # Bloquear varios asientos en bulk (sincronización al iniciar):
        blocking_agent.receive_bulk_update([
            {"flight_id": "FL001", "seat_id": "1A", "passenger_name": "Ana López"},
            {"flight_id": "FL003", "seat_id": "3B", "passenger_name": "Carlos Díaz"},
        ])

        # Liberar un asiento (cancelación):
        blocking_agent.release_seat("FL001", "2A")

        # Consultar estado:
        blocking_agent.get_blocked_seats("FL001")    → lista de seat_ids bloqueados
        blocking_agent.get_available_count("FL001")  → int con asientos libres
    ════════════════════════════════════════════════
    """

    def __init__(self, seats_ref: dict, flights_ref: list):
        self._seats   = seats_ref    # referencia compartida al índice de asientos
        self._flights = flights_ref  # referencia compartida a lista de vuelos
        self._log     = []           # historial de operaciones

    # ── Helpers internos ──────────────────────────────────

    def _normalize_seat(self, seat_id: str) -> str:
        """Normaliza formato: '2a' → '2A', 'A2' → '2A', ' 3 B ' → '3B'."""
        s = seat_id.strip().upper().replace(" ", "")
        if s and s[0].isalpha():          # formato columna-primero: 'A2'
            col, fila = s[0], s[1:]
            s = fila + col
        return s

    def _flight_exists(self, fid: str) -> bool:
        return fid in self._seats

    def _seat_exists(self, fid: str, sid: str) -> bool:
        return sid in self._seats.get(fid, {})

    def _recalculate_available(self, fid: str):
        """Recalcula seats_available en el objeto de vuelo tras un cambio."""
        count = sum(1 for s in self._seats[fid].values() if not s["ocupado"])
        for f in self._flights:
            if f["id"].upper() == fid:
                f["seats_available"] = count
                break

    def _log_event(self, event: str, fid: str, sid: str, passenger: str = ""):
        self._log.append({
            "event": event, "flight_id": fid,
            "seat_id": sid, "passenger": passenger
        })

    # ── API pública (hooks para agente externo) ───────────

    def receive_block_update(self, flight_id: str, seat_id: str,
                             passenger_name: str = "RESERVADO") -> dict:
        """
        HOOK PRINCIPAL: bloquea un asiento (llamado por el agente de compras).
        Retorna {"success": bool, "message": str}
        """
        fid = flight_id.strip().upper()
        sid = self._normalize_seat(seat_id)

        if not self._flight_exists(fid):
            return {"success": False, "message": f"Vuelo {fid} no existe."}
        if not self._seat_exists(fid, sid):
            return {"success": False, "message": f"Asiento {sid} no existe en {fid}."}
        if self._seats[fid][sid]["ocupado"]:
            return {"success": False, "message": f"Asiento {sid} ya está ocupado."}

        self._seats[fid][sid]["ocupado"] = True
        self._seats[fid][sid]["passenger_name"] = passenger_name
        self._recalculate_available(fid)
        self._log_event("BLOCK", fid, sid, passenger_name)
        return {"success": True, "message": f"Asiento {sid} bloqueado en vuelo {fid}."}

    def receive_bulk_update(self, blocked_seats_list: list) -> list:
        """
        HOOK BULK: recibe lista de bloqueos del agente externo.
        Cada item: {"flight_id": str, "seat_id": str, "passenger_name": str}
        """
        results = []
        for item in blocked_seats_list:
            r = self.receive_block_update(
                item.get("flight_id", ""),
                item.get("seat_id", ""),
                item.get("passenger_name", "RESERVADO")
            )
            results.append({**item, **r})
        return results

    def release_seat(self, flight_id: str, seat_id: str) -> dict:
        """Libera un asiento bloqueado (cancelación de compra)."""
        fid = flight_id.strip().upper()
        sid = self._normalize_seat(seat_id)

        if not self._flight_exists(fid) or not self._seat_exists(fid, sid):
            return {"success": False, "message": "Vuelo o asiento no encontrado."}
        if not self._seats[fid][sid]["ocupado"]:
            return {"success": False, "message": f"Asiento {sid} ya estaba libre."}

        self._seats[fid][sid]["ocupado"] = False
        self._seats[fid][sid]["passenger_name"] = ""
        self._recalculate_available(fid)
        self._log_event("RELEASE", fid, sid)
        return {"success": True, "message": f"Asiento {sid} liberado en vuelo {fid}."}

    def get_blocked_seats(self, flight_id: str) -> list:
        """Lista de seat_ids bloqueados para un vuelo."""
        fid = flight_id.strip().upper()
        return [sid for sid, s in self._seats.get(fid, {}).items() if s["ocupado"]]

    def get_available_count(self, flight_id: str) -> int:
        """Cantidad de asientos disponibles para un vuelo."""
        fid = flight_id.strip().upper()
        return sum(1 for s in self._seats.get(fid, {}).values() if not s["ocupado"])

    def get_log(self) -> list:
        return self._log


# ─────────────────────────────────────────────
#  AGENTE BUSCADOR DE VUELOS
# ─────────────────────────────────────────────

class FlightSearchAgent:
    """
    Agente autónomo que busca y ordena vuelos por disponibilidad.

    Propiedades del agente:
      • Autonomía    → decide el orden óptimo sin instrucciones adicionales
      • Reactividad  → refleja cambios de disponibilidad en tiempo real
      • Proactividad → filtra vuelos sin asientos antes de mostrarlos
    """

    def __init__(self, flights_ref: list, blocking_agent: SeatBlockingAgent):
        self._flights = flights_ref
        self._blocker = blocking_agent

    def search(self, origin: str, destination: str) -> list:
        """
        Busca vuelos por origen y destino.
        Retorna vuelos ordenados por asientos disponibles (mayor primero).
        Excluye vuelos sin asientos disponibles (llenos o bloqueados).
        """
        origin      = origin.strip().upper()
        destination = destination.strip().upper()

        matches = [
            f for f in self._flights
            if f["origin"].upper() == origin
            and f["destination"].upper() == destination
            and f["seats_available"] > 0
        ]
        matches.sort(key=lambda f: f["seats_available"], reverse=True)
        return matches

    def get_known_origins(self) -> list:
        return sorted(set(f["origin"].upper() for f in self._flights))

    def get_known_destinations(self, origin: Optional[str] = None) -> list:
        if origin:
            origin = origin.strip().upper()
            return sorted(set(
                f["destination"].upper()
                for f in self._flights if f["origin"].upper() == origin
            ))
        return sorted(set(f["destination"].upper() for f in self._flights))


# ─────────────────────────────────────────────
#  AGENTE DE INTERFAZ (coordinador UX)
# ─────────────────────────────────────────────

class InterfaceAgent:
    """
    Agente coordinador de la experiencia en terminal.
    Valida entradas, orquesta los agentes y presenta resultados.
    """

    SEP  = "═" * 58
    SEP2 = "─" * 58

    def __init__(self, search_agent: FlightSearchAgent,
                 blocking_agent: SeatBlockingAgent,
                 seats_ref: dict):
        self._searcher = search_agent
        self._blocker  = blocking_agent
        self._seats    = seats_ref

    # ── Visualización ─────────────────────────────────────

    def _clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _header(self):
        print(self.SEP)
        print("  ✈  SISTEMA DE BÚSQUEDA DE VUELOS — AGENTE AUTÓNOMO")
        print(self.SEP)

    def _pause(self, msg: str = "\n  Presione ENTER para continuar..."):
        input(msg)

    def _format_date(self, date_str: str) -> str:
        meses = {
            "01": "Enero",    "02": "Febrero",   "03": "Marzo",
            "04": "Abril",    "05": "Mayo",       "06": "Junio",
            "07": "Julio",    "08": "Agosto",     "09": "Septiembre",
            "10": "Octubre",  "11": "Noviembre",  "12": "Diciembre"
        }
        try:
            y, m, d = date_str.split("-")
            return f"{d} {meses.get(m, m)} {y}"
        except Exception:
            return date_str

    def _seat_bar(self, available: int, total: int = 10) -> str:
        filled = total - available
        bar    = "█" * available + "░" * filled
        pct    = int((available / total) * 100)
        return f"[{bar}] {available}/{total} libres ({pct}%)"

    def _print_flight_card(self, idx: int, flight: dict):
        available = flight["seats_available"]
        if available >= 7:
            status = "ALTA DISPONIBILIDAD  ✔"
        elif available >= 4:
            status = "DISPONIBILIDAD MEDIA ⚠"
        else:
            status = "ÚLTIMOS ASIENTOS     ⚡"

        print(f"\n  [{idx}] Vuelo: {flight['id']}  |  {status}")
        print(f"      {self.SEP2}")
        print(f"      Origen    : {flight['origin']}")
        print(f"      Destino   : {flight['destination']}")
        print(f"      Fecha     : {self._format_date(flight['date'])}")
        print(f"      Asientos  : {self._seat_bar(available)}")

    def _print_seat_map(self, flight_id: str):
        seats = self._seats.get(flight_id.upper(), {})
        print(f"\n  Mapa de asientos — Vuelo {flight_id}")
        print(f"  {'─'*30}")
        print(f"  {'FILA':>6}   A         B")
        print(f"  {'─'*30}")

        # Detectar filas disponibles dinámicamente desde el JSON
        filas = sorted(set(
            s["fila"] for s in seats.values()
        ), key=lambda x: int(x) if x.isdigit() else x)

        for fila in filas:
            sa = seats.get(f"{fila}A", {})
            sb = seats.get(f"{fila}B", {})
            ico_a = "[ X ]" if sa.get("ocupado") else "[   ]"
            ico_b = "[ X ]" if sb.get("ocupado") else "[   ]"
            print(f"    {fila:>4}   {ico_a}    {ico_b}")

        print(f"\n  Leyenda: [   ] = Disponible   [ X ] = Ocupado")

    # ── Validación de entradas ────────────────────────────

    def _input_validated(self, prompt: str, valid_options: list, campo: str) -> str:
        """Solicita input y valida contra lista. Reintenta hasta acertar."""
        opciones_upper = [o.upper() for o in valid_options]
        while True:
            raw = input(prompt).strip()
            if not raw:
                print(f"  ⚠  El campo '{campo}' no puede estar vacío.")
                continue
            valor = raw.upper()
            if valor in opciones_upper:
                return valor
            sugerencias = [o for o in opciones_upper if valor in o or o.startswith(valor)]
            if sugerencias:
                print(f"  ⚠  '{raw}' no reconocido. ¿Quisiste decir: {', '.join(sugerencias)}?")
            else:
                print(f"  ⚠  '{raw}' no es un {campo} válido.")
                print(f"     Opciones disponibles: {', '.join(valid_options)}")

    def _input_yes_no(self, prompt: str) -> bool:
        while True:
            r = input(prompt + " [S/N]: ").strip().upper()
            if r in ("S", "SI", "SÍ", "YES", "Y"):
                return True
            if r in ("N", "NO"):
                return False
            print("  ⚠  Responda S (sí) o N (no).")

    def _input_flight_choice(self, results: list) -> Optional[dict]:
        indices_validos = [str(i + 1) for i in range(len(results))]
        while True:
            raw = input(f"\n  Ingrese número de vuelo (1-{len(results)}) o 0 para volver: ").strip()
            if raw == "0":
                return None
            if raw in indices_validos:
                return results[int(raw) - 1]
            print(f"  ⚠  Opción inválida. Ingrese un número entre 1 y {len(results)}, o 0.")

    # ── Flujo principal ───────────────────────────────────

    def run(self):
        while True:
            self._clear()
            self._header()

            # ── 1. Origen ──
            print("\n  PASO 1 — Seleccione el origen del vuelo")
            origenes = self._searcher.get_known_origins()
            for i, o in enumerate(origenes, 1):
                print(f"    {i}. {o}")

            origin = self._input_validated("\n  > Origen: ", origenes, "origen")

            # ── 2. Destino ──
            print(f"\n  PASO 2 — Seleccione el destino desde {origin}")
            destinos = self._searcher.get_known_destinations(origin)
            if not destinos:
                print(f"  ⚠  No hay destinos disponibles desde {origin}.")
                self._pause()
                continue

            for i, d in enumerate(destinos, 1):
                print(f"    {i}. {d}")

            destination = self._input_validated("\n  > Destino: ", destinos, "destino")

            # ── 3. Búsqueda ──
            print(f"\n  🔍 Agente buscando vuelos {origin} → {destination}...")
            time.sleep(0.5)

            results = self._searcher.search(origin, destination)

            self._clear()
            self._header()
            print(f"\n  Ruta    : {origin}  →  {destination}")
            print(f"  Vuelos  : {len(results)} disponibles")
            print(f"  Orden   : Mayor disponibilidad primero")
            print(f"\n  {self.SEP2}")

            if not results:
                print("\n  ✈  No hay vuelos con asientos disponibles para esta ruta.")
                print("     Todos los vuelos pueden estar completos o bloqueados.")
            else:
                for idx, flight in enumerate(results, 1):
                    self._print_flight_card(idx, flight)

                # ── 4. Mapa de asientos ──
                print(f"\n  {self.SEP2}")
                ver_mapa = self._input_yes_no("\n  ¿Desea ver el mapa de asientos de algún vuelo?")

                if ver_mapa:
                    vuelo_elegido = self._input_flight_choice(results)
                    if vuelo_elegido:
                        self._clear()
                        self._header()
                        print(f"\n  Detalle — Vuelo {vuelo_elegido['id']}")
                        print(f"  {vuelo_elegido['origin']}  →  {vuelo_elegido['destination']}")
                        print(f"  Fecha: {self._format_date(vuelo_elegido['date'])}")
                        self._print_seat_map(vuelo_elegido["id"])
                        self._pause()

            # ── 5. Nueva búsqueda ──
            nueva = self._input_yes_no("\n  ¿Desea realizar otra búsqueda?")
            if not nueva:
                self._clear()
                self._header()
                print("\n  Gracias por usar el Sistema de Búsqueda de Vuelos.")
                print("  ¡Buen viaje!  ✈\n")
                print(self.SEP)
                break


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    """
    Inicializa los agentes y arranca el sistema.

    Arquitectura:
      DataLoaderAgent   → carga ../data/flights.json y ../data/seats.json
      SeatBlockingAgent → gestiona bloqueos (hook para agente externo)
      FlightSearchAgent → busca y ordena vuelos en tiempo real
      InterfaceAgent    → coordina UX y valida entradas
    """

    # 1. Cargar datos desde ../data/
    print("  Cargando datos...")
    try:
        flights   = DataLoaderAgent.load_flights()
        seats_idx = DataLoaderAgent.load_seats(flights)
    except (FileNotFoundError, ValueError) as e:
        print(e)
        print("\n  Verifique la estructura del proyecto:")
        print("    Flying-software/")
        print("    ├── data/")
        print("    │   ├── flights.json")
        print("    │   └── seats.json")
        print("    └── Agentes/")
        print("        └── buscador_vuelos.py")
        return

    # 2. Instanciar agentes
    blocking_agent = SeatBlockingAgent(seats_idx, flights)
    search_agent   = FlightSearchAgent(flights, blocking_agent)
    interface      = InterfaceAgent(search_agent, blocking_agent, seats_idx)

    # ══════════════════════════════════════════════════════
    #  ZONA DE INTEGRACIÓN CON AGENTE EXTERNO DE COMPRAS
    #  Descomentar cuando el agente bloqueador esté listo.
    # ══════════════════════════════════════════════════════
    #
    # EJEMPLO 1 — Bloqueo individual (una compra confirmada):
    # blocking_agent.receive_block_update("FL001", "1A", "María García")
    #
    # EJEMPLO 2 — Sincronización masiva al iniciar sesión:
    # blocking_agent.receive_bulk_update([
    #     {"flight_id": "FL001", "seat_id": "1A", "passenger_name": "Juan Pérez"},
    #     {"flight_id": "FL001", "seat_id": "1B", "passenger_name": "Ana López"},
    # ])
    #
    # EJEMPLO 3 — Cancelación / liberación de asiento:
    # blocking_agent.release_seat("FL001", "1A")
    # ══════════════════════════════════════════════════════

    # 3. Arrancar
    interface.run()


if __name__ == "__main__":
    main()