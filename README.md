# Sistema de Reserva de Vuelos

Aplicación web en Python (Flask) que permite buscar y reservar asientos en vuelos, con actualización en tiempo real entre múltiples sesiones simultáneas. Desarrollada como ejercicio de integración de componentes, aspectos y agentes.

## Cómo correr

```bash
python app.py
```

Abrir `http://localhost:5000` en el browser.
Para el demo de persistencia en tiempo real, abrir la misma URL en dos tabs o dos dispositivos en la misma red.

El monitor de vuelos está siempre accesible en `http://localhost:5000/monitor` sin necesidad de login.

## Arquitectura

### Componentes
| Módulo | Responsabilidad |
|---|---|
| `Componentes/catalogo.py` | Carga y filtra vuelos disponibles (excluye los sin asientos) |
| `Componentes/reserva.py` | Gestiona la selección de asiento y delega la escritura al aspecto de bloqueo |

### Aspectos
| Módulo | Responsabilidad |
|---|---|
| `Aspectos/logging_aspect.py` | Registra cada reserva exitosa en `data/audit_logs.txt` |
| `Aspectos/alertas.py` | Envuelve operaciones críticas con notificaciones de inicio, éxito y error |
| `Aspectos/bloqueo.py` | Controla el acceso atómico a los asientos: valida, bloquea y guarda |

### Agentes
| Módulo | Responsabilidad |
|---|---|
| `Agentes/AgenteCierreVentas.py` | Recalcula `seats_available` en `flights.json` tras cada reserva y detecta vuelos llenos |
| `Agentes/buscador_vuelos.py` | Carga datos, filtra destinos y genera el mapa de asientos visual |

### Interfaz web (`app.py` + `templates/`)
| Ruta | Descripción |
|---|---|
| `/login` | Ingreso con nombre del pasajero |
| `/destinations` | Selección de destino con total de asientos disponibles por ruta |
| `/catalog` | Lista de vuelos con contador live (se actualiza sin recargar) |
| `/seats` | Mapa interactivo del avión — clic para seleccionar asiento |
| `/confirmation` | Tarjeta de embarque con datos de la reserva |
| `/monitor` | Dashboard en tiempo real de todos los vuelos (sin login) |

## Tiempo real

La app usa **Flask-SocketIO** para sincronizar el estado entre todas las sesiones abiertas:

- Al reservar un asiento, el mapa se actualiza instantáneamente en cualquier otro browser que esté viendo el mismo vuelo
- El contador de asientos en el catálogo baja solo cuando alguien reserva
- El monitor recibe todas las reservas en tiempo real con animación y feed de actividad

## Datos

- **`data/flights.json`** — 10 vuelos desde Buenos Aires hacia 3 destinos: Madrid, New York y Miami
- **`data/seats.json`** — 10 asientos por vuelo (filas 1–5, columnas A y B)
- **`data/audit_logs.txt`** — registro de auditoría generado automáticamente

La persistencia es en disco: los JSON se actualizan en cada reserva y sobreviven reinicios del servidor.

## Flujo principal

1. El usuario ingresa su nombre
2. El agente buscador filtra destinos desde Buenos Aires
3. El catálogo muestra vuelos disponibles con asientos libres actualizados
4. El mapa del avión permite seleccionar el asiento con un clic
5. El aspecto de bloqueo valida y persiste la reserva atómicamente
6. El agente de cierre recalcula la disponibilidad y detecta vuelos llenos
7. El aspecto de logs registra la operación en el archivo de auditoría
8. SocketIO notifica a todas las sesiones conectadas

## Requisitos

```
flask
flask-socketio
colorama
```

```bash
pip install flask flask-socketio colorama
```
