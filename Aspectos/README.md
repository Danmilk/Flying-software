# Sistema de Reserva de Vuelos

Aplicación de consola en Python que permite buscar y reservar asientos en vuelos. Desarrollada como ejercicio de integración de componentes, aspectos y agentes.

## Arquitectura

### Componentes
| Módulo | Responsabilidad |
|---|---|
| Catálogo de vuelos | Muestra los vuelos disponibles y permite seleccionar uno |
| Sistema de reserva | Gestiona la selección y confirmación de asientos |

### Aspectos
| Módulo | Responsabilidad |
|---|---|
| Logs | Registra todas las operaciones realizadas en el sistema |
| Mensajes y alertas | Notifica al usuario sobre el estado de cada acción |

### Agentes
| Módulo | Responsabilidad |
|---|---|
| Cierre de ventana de un vuelo | Detecta cuando un vuelo queda sin asientos y lo cierra automáticamente |
| Buscador del catálogo | Filtra el catálogo de vuelos según el destino que elige el usuario |

## Datos

- **`data/flights.json`** — 10 vuelos desde Buenos Aires hacia 3 destinos: Madrid, New York y Miami
- **`data/seats.json`** — 10 asientos por vuelo (filas 1–5, columnas A y B)

La persistencia es en disco: dos terminales corriendo la app simultáneamente comparten los mismos datos en tiempo real.

## Flujo principal

1. El usuario ingresa su nombre (mock login)
2. El agente buscador filtra vuelos por destino elegido
3. El catálogo muestra los vuelos disponibles
4. El sistema de reserva gestiona la selección del asiento
5. El agente de cierre monitorea si el vuelo quedó sin asientos
6. Los aspectos de logs y alertas registran y notifican cada paso

## Requisitos

- Python 3.x
- `colorama` — `pip install colorama`
