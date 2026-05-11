# ESP32 Bus Pirate Companion App

Interfaz gráfica de escritorio para el **ESP32 Piratebus Kit** — conecta, controla y flashea tu dispositivo sin tocar la terminal.

---

## Características

| Función | Descripción |
|---|---|
| Terminal serial | Envía comandos y visualiza respuestas con coloreado por tipo |
| Referencia de pines | Pinouts por módulo y puerto (NFC, SubGHz, Ethernet) |
| Selector de modos | 21 modos del firmware con un clic (I2C, SPI, UART, etc.) |
| Flash local | Flashea un `.bin` local directamente desde la GUI |
| Flash GitHub | Descarga y flashea cualquier release de ESP32-Bus-Pirate |
| Historial de comandos | Navega comandos anteriores con flechas ↑↓ |
| Persistencia | Recuerda el último puerto y baudrate usados |

---

## Requisitos

- Python 3.9+
- `customtkinter >= 5.2.0`
- `pyserial >= 3.5`
- `esptool >= 4.0`

---

## Instalación

```bash
# 1. Clona el repositorio (si no lo tienes)
git clone <repo-url>
cd ESP32_Buspirate_Kit/companion_app

# 2. Crea un entorno virtual (recomendado)
python -m venv .env
source .env/bin/activate        # Linux / macOS
# .env\Scripts\activate         # Windows

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Ejecuta la app
python buspirate_gui.py
```

---

## Uso

### Conexión serial
1. Selecciona el puerto COM / ttyACM del ESP32 en el selector.
2. Elige el baudrate (por defecto `115200`).
3. Presiona **Conectar** — el terminal mostrará la bienvenida del firmware.

### Módulos (tabs laterales)

- **NFC** — Pinout del PN532 en I²C para los puertos 1 y 2.
- **SubGhz** — Pinout del CC1101 / nRF24L01 en SPI.
- **Ethernet** — Pinout del W5500 en SPI.
- **Modos** — Botones de acceso rápido para todos los modos del firmware.

### Flash de firmware

**Archivo local:**
1. Tab `Firmware` → `Seleccionar .bin...`
2. Selecciona el binario descargado previamente.
3. Presiona **Flashear archivo local**.

**Desde GitHub:**
1. Tab `Firmware` → `Buscar versiones`.
2. Selecciona la versión en el desplegable.
3. Presiona **Descargar y Flashear**.

> La app desconecta el serial automaticamente antes de flashear.

---

## Dependencias del sistema para flashear

`esptool` se invoca como modulo Python (`python -m esptool`). Asegúrate de que esté instalado en el mismo entorno virtual.

En Linux puede ser necesario agregar tu usuario al grupo `dialout`:

```bash
sudo usermod -aG dialout $USER
# Cierra sesión y vuelve a entrar para aplicar
```
