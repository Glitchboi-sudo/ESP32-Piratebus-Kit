#!/usr/bin/env python3
"""
ESP32 Bus Pirate Companion GUI
Interfaz gráfica moderna para facilitar el uso del Bus Pirate
"""

import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import queue
import time
import re
import json
import os
import subprocess
import tempfile
import urllib.request
import urllib.error
from tkinter import filedialog
from typing import Optional
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "buspirate_config.json")

# GitHub releases API endpoint
FIRMWARE_API_URL = "https://api.github.com/repos/geo-tp/ESP32-Bus-Pirate/releases"

# Pin assignments per module and port
MODULE_PINS = {
    "nfc": {
        1: {"SDA": 6,  "SCL": 7},
        2: {"SDA": 15, "SCL": 14},
    },
    "subghz": {
        1: {"CS": 39, "MISO": 38, "CK": 9,  "MOSI": 8,  "GD0": 7},
        2: {"CS": 10, "MISO": 11, "CK": 12, "MOSI": 13, "GD0": 14},
    },
    "ethernet": {
        1: {"CS": 39, "MISO": 38, "SCK": 9,  "MOSI": 8,  "IRQ": 7},
        2: {"CS": 10, "MISO": 11, "SCK": 12, "MOSI": 13, "IRQ": 14},
    },
}

GENERAL_COMMANDS = """\
help                 - Show this help
mode [name]          - Set active mode
man                  - Show firmware guide
system               - Show system infos
profile              - Save/load GPIOs config
alias                - Create shortcut
hex [number]         - Convert dec/hex/bin
logic <gpio>         - Logic analyzer
analogic <gpio>      - Analogic plotter
wizard <gpio>        - GPIO activity analyzer
listen <gpio>        - GPIO activity to audio
repeat <count> <cmd> - Repeat command
P                    - Enable pull-up
p                    - Disable pull-up"""

MODE_COMMANDS: dict = {
    "hiz": "(No mode-specific commands — all pins in high impedance.)",
    "1wire": """\
scan                 - Scan 1-Wire devices
ping                 - Ping 1-Wire device
sniff                - View 1-Wire traffic
read                 - Read ID + SP
write id [8 bytes]   - Write device ID
write sp [8 bytes]   - Write scratchpad
temp                 - Read temperature
ibutton              - iButton operations
eeprom               - EEPROM operations
config               - Configure settings
[0xAA r:8] ...       - Instruction syntax""",
    "uart": """\
scan                 - Scan UART lines activity
autobaud             - Detect baud rate on RX
ping                 - Send and expect reply
sniff                - Monitor ascii UART traffic
sniff raw            - Monitor hex UART traffic
read                 - Receive ascii data
raw                  - Receive raw hex data
write [text]         - Send at current baud
bridge               - Full-duplex mode
at                   - AT commands operations
emulator             - Emulate UART device
trigger [pattern]    - Send response on pattern
spam [text] [ms]     - Write text every ms
xmodem <send> <path> - Send file via XMODEM
xmodem <recv> <path> - Receive file via XMODEM
config               - Configure settings
swap                 - Swap RX and TX GPIOs
['Hello'] [r:64]...  - Instruction syntax""",
    "hduart": """\
bridge               - Half-duplex I/O
config               - Configure settings
[0x1 D:10 r:255]     - Instruction syntax""",
    "i2c": """\
scan                 - Find devices
discovery            - Report on devices
ping <addr>          - Check ACK
identify <addr>      - Identify device
sniff                - View traffic
slave <addr>         - Emulate I2C device
read <addr> [reg]    - Read register
write <a> [r] [val]  - Write register
dump <addr> [len]    - Read all registers
regs <addr> [len]    - Probe register R/W
glitch <addr>        - Run attack sequence
flood <addr>         - Saturate target I/O
health <addr>        - Perform timing test
monitor <addr> [ms]  - Monitor register changes
eeprom [addr]        - I2C EEPROM operations
recover              - Attempt bus recovery
jam                  - Jam I2C bus with noise
swap                 - Swap SDA and SCL GPIOs
config               - Configure settings
[0x13 0x4B 0x1]      - Instruction syntax""",
    "spi": """\
sniff                - View traffic
sdcard               - SD operations
slave                - Emulate SPI slave
flash                - SPI Flash operations
eeprom               - SPI EEPROM operations
config               - Configure settings
[0x9F r:3]           - Instruction syntax""",
    "2wire": """\
sniff                - View 2WIRE traffic
smartcard            - Smartcard operations
config               - Configure settings
[0xAB r:4]           - Instruction syntax""",
    "3wire": """\
eeprom               - 3WIRE EEPROM operations
config               - Configure settings""",
    "dio": """\
scan                  - Detect pins activity
pins                  - Show pins state
sniff <gpio>          - Track toggle states
read <gpio>           - Get pin state
set <gpio> <H/L/I/O>  - Set pin state
pullup <gpio>         - Set pin pullup
pulldown <gpio>       - Set pin pulldown
pulse <gpio> <us>     - Send pulse on pin
servo <gpio> <angle>  - Set servo angle
pwm <gpio> [frq duty%]- Set PWM on pin
toggle <gpio> <ms>    - Toggle pin periodically
measure <gpio> [ms]   - Calculate frequency
jam <gpio> [min max]  - Random high/low states
reset <gpio>          - Reset to default""",
    "led": """\
fill <color>         - Fill all LEDs with a color
set <index> <color>  - Set specific LED color
blink                - Blink all LEDs
rainbow              - Rainbow animation
chase                - Chasing light effect
cycle                - Cycle through colors
wave                 - Wave animation
reset                - Turn off all LEDs
setprotocol          - Select LED protocol
config               - Configure LED settings""",
    "infrared": """\
send <dev> sub <cmd> - Send IR signal
receive              - Receive IR signal
setprotocol          - Set IR protocol type
devicebgone          - OFF devices blast
remote               - Universal remote commands
replay [count]       - Replay recorded IR frames
record               - Record IR signals to file
load                 - Load .ir files from FS
jam                  - Send random IR signals
config               - Configure settings""",
    "usb": """\
stick                - Mount SD as USB
keyboard [text]      - Start keyboard bridge
mouse [action]       - Mouse move and click
mouse jiggle [ms]    - Random mouse moves
gamepad [key]        - Gamepad button press
sysctrl [action]     - Hardware control actions
host                 - Connect device to ESP32
reset                - Reset interface
config               - Configure settings""",
    "bluetooth": """\
scan                 - Discover devices
pair <mac>           - Pair with a device
sniff                - Sniff Bluetooth data
spoof <mac>          - Spoof mac address
status               - Show current status
server               - Create an HID server
keyboard [text]      - Start keyboard bridge
mouse <x> <y>        - Move mouse cursor
mouse click          - Mouse left click
mouse jiggle [ms]    - Random mouse moves
reset                - Reset interface""",
    "wifi": """\
scan                 - List Wi-Fi networks
connect              - Connect to a network
ping <host>          - Ping a remote host
discovery [timeout]  - Discover network devices
sniff                - Monitor Wi-Fi packets
waterfall            - Show channel activity
probe                - Search for net access
repeater             - Forward Wi-Fi traffic
spoof ap <mac>       - Spoof AP MAC
spoof sta <mac>      - Spoof Station MAC
status               - Show Wi-Fi status
deauth [ssid]        - Deauthenticate hosts
disconnect           - Disconnect from Wi-Fi
ap <ssid> <password> - Set access point
spam                 - Spam random beacons
flood [channel]      - Flood channel with packets
ssh [h] [u] [pw] [p] - Open SSH session
telnet <host> [port] - Open telnet session
nc <host> <port>     - Open netcat session
nmap <h> [-p ports]  - Scan host ports
modbus <host> [port] - Modbus TCP operations
http get <url>       - HTTP(s) GET request
http analyze <url>   - Get analysis report
lookup mac|ip <addr> - Lookup MAC or IP address
webui                - Show the web UI IP
reset                - Reset interface""",
    "jtag": """\
scan swd             - Scan SWD pins
scan jtag            - Scan JTAG pins
config               - Configure settings""",
    "i2s": """\
play <freq> [ms]     - Play sine wave for ms
record               - Read mic continuously
test <speaker|mic>   - Run basic audio tests
reset                - Reset to default
config               - Configure settings""",
    "can": """\
sniff                - Print all received frames
send [id]            - Send frame with given ID
receive [id]         - Capture frames with ID
status               - State of the CAN controller
config               - Configure MCP2515 settings""",
    "ethernet": """\
connect              - Connect using DHCP
status               - Show ETH status
ping <host>          - Ping a remote host
discovery [timeout]  - Discover network devices
ssh [h] [u] [pw] [p] - Open SSH session
telnet <host> [port] - Open telnet session
nc <host> <port>     - Open netcat session
nmap <h> [-p ports]  - Scan host ports
modbus <host> [port] - Modbus TCP operations
http get <url>       - HTTP(s) GET request
http analyze <url>   - Get analysis report
lookup mac|ip <addr> - Lookup MAC or IP address
reset                - Reset interface
config               - Configure W5500 settings""",
    "subghz": """\
scan                 - Search best frequency
sweep                - Analyze frequency band
send <payload> [te]  - Send a frame payload
receive              - Receive raw/decoded signals
replay               - Record and replay frames
jam                  - Jam selected frequencies
bruteforce           - Bruteforce 12 bit keys
trace                - Observe RX signal trace
waterfall            - Show frequency peaks
record               - Record frame to .sub file
load                 - Load .sub files from FS
ear                  - RSSI to audio mapping
setfrequency         - Set operating frequency
config               - Configure CC1101 settings""",
    "rfid": """\
read                 - Read RFID tag data
write                - Write UID/Block to tag
clone                - Clone Mifare UID
erase                - Erase RFID tag
config               - Configure PN532 settings""",
    "rf24": """\
scan                 - Search best active channel
send                 - Send a frame payload
receive              - Receive frames
sweep                - Analyze channels activity
jam                  - Jam selected channels group
waterfall            - Show channel peaks
setchannel           - Set operating channel
config               - Configure NRF24 settings""",
}


def load_config() -> dict:
    default_config = {"last_port": "", "last_baudrate": "115200"}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                default_config.update(saved)
    except Exception:
        pass
    return default_config

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

ANSI_ESCAPE_PATTERN = re.compile(r'''
    \x1b\[[0-9;]*[A-Za-z]  |  # CSI sequences
    \x1b\][^\x07]*\x07     |  # OSC sequences
    \x1b[PX^_].*?\x1b\\    |  # DCS, SOS, PM, APC sequences
    \x1b.                  |  # Otros escapes de 2 caracteres
    \x07                   |  # Bell
    \x08                   |  # Backspace
    \r                        # Carriage return
''', re.VERBOSE)

PROMPT_PATTERN = re.compile(r'[A-Z0-9]{2,6}>\s*')

def clean_ansi(text: str) -> str:
    cleaned = ANSI_ESCAPE_PATTERN.sub('', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned

def clean_echo_spam(text: str) -> str:
    result_lines = []
    for line in text.split('\n'):
        prompts = list(PROMPT_PATTERN.finditer(line))
        if len(prompts) > 1:
            last_prompt = prompts[-1]
            result_lines.append(line[last_prompt.start():])
        else:
            result_lines.append(line)
    return '\n'.join(result_lines)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BusPirateGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("ESP32 Bus Pirate Companion")
        self.root.geometry("1400x900")

        self.ser: Optional[serial.Serial] = None
        self.connected = False
        self.read_thread: Optional[threading.Thread] = None
        self.running = False
        self.command_history = []
        self.history_index = -1
        self.config = load_config()
        self.output_queue = queue.Queue()

        # Mode help widget ref (populated during UI build)
        self.mode_help_text: Optional[ctk.CTkTextbox] = None

        # Firmware state
        self.firmware_releases: dict = {}   # {tag: download_url}
        self.fw_version_var = ctk.StringVar(value="")
        self.fw_status_label: Optional[ctk.CTkLabel] = None
        self.fw_version_combo: Optional[ctk.CTkComboBox] = None
        self.fw_flash_btn: Optional[ctk.CTkButton] = None

        # Local firmware state
        self.local_bin_path: Optional[str] = None
        self.local_bin_label: Optional[ctk.CTkLabel] = None
        self.local_flash_btn: Optional[ctk.CTkButton] = None

        self.create_widgets()
        self.setup_styles()
        self.update_output()
        self.refresh_ports()

    # ─────────────────────────────── UI BUILD ────────────────────────────────

    def create_widgets(self):
        # HEADER
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="ESP32 BusPirate Companion",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(side="left", padx=20, pady=20)

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="● Desconectado",
            font=ctk.CTkFont(size=14),
            text_color="#FF6B6B"
        )
        self.status_label.pack(side="right", padx=20, pady=20)

        # CONNECTION BAR
        connection_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0, fg_color="#2B2B2B")
        connection_frame.pack(fill="x", padx=10, pady=(10, 0))
        connection_frame.pack_propagate(False)

        ctk.CTkLabel(connection_frame, text="Puerto:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))

        self.port_var = ctk.StringVar()
        self.port_combo = ctk.CTkComboBox(
            connection_frame, variable=self.port_var,
            values=["Detectando..."], width=200, state="readonly"
        )
        self.port_combo.pack(side="left", padx=5)

        ctk.CTkButton(connection_frame, text="🔄", width=40, command=self.refresh_ports).pack(side="left", padx=5)

        ctk.CTkLabel(connection_frame, text="Baudrate:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(20, 5))

        saved_baudrate = self.config.get("last_baudrate", "115200")
        self.baudrate_var = ctk.StringVar(value=saved_baudrate)
        ctk.CTkComboBox(
            connection_frame, variable=self.baudrate_var,
            values=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"],
            width=120, state="readonly"
        ).pack(side="left", padx=5)

        self.connect_btn = ctk.CTkButton(
            connection_frame, text="Conectar", width=120,
            command=self.toggle_connection, fg_color="#4CAF50", hover_color="#45A049"
        )
        self.connect_btn.pack(side="right", padx=10)

        # MAIN CONTENT
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1, minsize=420)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel — module shortcuts
        shortcuts_frame = ctk.CTkFrame(main_frame)
        shortcuts_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        shortcuts_frame.grid_rowconfigure(1, weight=1)
        shortcuts_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            shortcuts_frame, text="Módulos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, pady=(10, 5))

        self.shortcut_tabs = ctk.CTkTabview(shortcuts_frame)
        self.shortcut_tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        self.create_nfc_tab()
        self.create_subghz_tab()
        self.create_ethernet_tab()
        self.create_modes_tab()
        self.create_firmware_tab()

        # Right panel — terminal
        terminal_frame = ctk.CTkFrame(main_frame)
        terminal_frame.grid(row=0, column=1, sticky="nsew")

        terminal_header = ctk.CTkFrame(terminal_frame, height=40, corner_radius=0, fg_color="#1E1E1E")
        terminal_header.pack(fill="x")
        terminal_header.pack_propagate(False)

        ctk.CTkLabel(
            terminal_header, text="Terminal",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=5)

        ctk.CTkButton(
            terminal_header, text="Limpiar", width=80, height=25,
            command=self.clear_terminal, fg_color="#FF6B6B", hover_color="#E85555"
        ).pack(side="right", padx=10, pady=5)

        ctk.CTkButton(
            terminal_header, text="Guardar Log", width=100, height=25,
            command=self.export_session_log, fg_color="#2D5A3E", hover_color="#1F4030"
        ).pack(side="right", padx=5, pady=5)

        self.output_text = ctk.CTkTextbox(
            terminal_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#0D1117", wrap="word"
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.output_text.bind("<Key>", self._terminal_key_filter)

        input_frame = ctk.CTkFrame(terminal_frame, height=60, fg_color="#1E1E1E")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        input_frame.pack_propagate(False)

        ctk.CTkLabel(input_frame, text="BP>", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(10, 5))

        self.input_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            placeholder_text="Escribe un comando o usa los atajos..."
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", lambda e: self.send_command())
        self.input_entry.bind("<Up>", self.history_up)
        self.input_entry.bind("<Down>", self.history_down)

        ctk.CTkButton(
            input_frame, text="Enviar", width=100, command=self.send_command,
            fg_color="#2196F3", hover_color="#1976D2"
        ).pack(side="right", padx=10)

    # ───────────────────────────── MODULE TABS ───────────────────────────────

    def _port_section(self, parent, module: str, port: int):
        """Pinout reference card for a module port — no commands sent."""
        pins = MODULE_PINS[module][port]

        section = ctk.CTkFrame(parent, fg_color="#1A1A2E", corner_radius=8)
        section.pack(fill="x", padx=8, pady=5)

        ctk.CTkLabel(
            section, text=f"Puerto {port}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#A0A0C0"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        for pin_name, io_num in pins.items():
            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=1)
            ctk.CTkLabel(
                row, text=pin_name,
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#7EC8E3", width=52, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row, text="→",
                font=ctk.CTkFont(size=11), text_color="#555577"
            ).pack(side="left", padx=4)
            ctk.CTkLabel(
                row, text=f"IO{io_num}",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color="#E0E0E0"
            ).pack(side="left")

        ctk.CTkFrame(section, height=1, fg_color="#2A2A3E").pack(fill="x", padx=10, pady=(6, 0))
        ctk.CTkLabel(
            section, text="Configura el modo desde la tab  Modos",
            font=ctk.CTkFont(size=10), text_color="#606080"
        ).pack(pady=(4, 8))

    def create_nfc_tab(self):
        tab = self.shortcut_tabs.add("NFC")

        ctk.CTkLabel(tab, text="NFC Module — PN532",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(tab, text="I²C · 13.56 MHz  |  modo: I2C",
                     font=ctk.CTkFont(size=11), text_color="#A0A0A0").pack(pady=(0, 6))

        self._port_section(tab, "nfc", 1)
        self._port_section(tab, "nfc", 2)

    def create_subghz_tab(self):
        tab = self.shortcut_tabs.add("SubGhz")

        ctk.CTkLabel(tab, text="SubGhz/2.4 GHz Module",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(tab, text="CC1101 → SUBGHZ  |  nRF24 → RF24",
                     font=ctk.CTkFont(size=11), text_color="#A0A0A0").pack(pady=(0, 6))

        self._port_section(tab, "subghz", 1)
        self._port_section(tab, "subghz", 2)

    def create_ethernet_tab(self):
        tab = self.shortcut_tabs.add("Ethernet")

        ctk.CTkLabel(tab, text="Ethernet Module — W5500",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(tab, text="SPI · 10/100 Mbps  |  modo: ETHERNET",
                     font=ctk.CTkFont(size=11), text_color="#A0A0A0").pack(pady=(0, 6))

        self._port_section(tab, "ethernet", 1)
        self._port_section(tab, "ethernet", 2)

    def create_modes_tab(self):
        """Quick-select buttons for all official ESP32 Bus Pirate modes."""
        tab = self.shortcut_tabs.add("Modos")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=2)   # scroll frame de botones
        tab.grid_rowconfigure(5, weight=1)   # textbox de comandos

        ctk.CTkLabel(tab, text="Modos disponibles",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
                         row=0, column=0, pady=(10, 2))
        ctk.CTkLabel(tab, text="Clic → envía el modo y muestra info",
                     font=ctk.CTkFont(size=10), text_color="#707070").grid(
                         row=1, column=0, pady=(0, 6))

        # Official mode list from firmware
        modes = [
            ("1", "HIZ"),
            ("2", "1WIRE"),
            ("3", "UART"),
            ("4", "HDUART"),
            ("5", "I2C"),
            ("6", "SPI"),
            ("7", "2WIRE"),
            ("8", "3WIRE"),
            ("9", "DIO"),
            ("10", "LED"),
            ("11", "INFRARED"),
            ("12", "USB"),
            ("13", "BLUETOOTH"),
            ("14", "WIFI"),
            ("15", "JTAG"),
            ("16", "I2S"),
            ("17", "CAN"),
            ("18", "ETHERNET"),
            ("19", "SUBGHZ"),
            ("20", "RFID"),
            ("21", "RF24"),
        ]

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        scroll.columnconfigure(0, weight=1)
        scroll.columnconfigure(1, weight=1)

        for i, (num, name) in enumerate(modes):
            col = i % 2
            row = i // 2
            btn = ctk.CTkButton(
                scroll,
                text=f"{num}. {name}",
                height=30,
                font=ctk.CTkFont(family="Consolas", size=12),
                fg_color="#1E3A5F", hover_color="#163050",
                anchor="w",
                command=lambda n=name.lower(): self._mode_button_action(n)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

        # ── Help panel ────────────────────────────────────────────────────
        ctk.CTkFrame(tab, height=1, fg_color="#333355").grid(
            row=3, column=0, sticky="ew", padx=10, pady=(4, 4))

        ctk.CTkLabel(tab, text="Comandos del modo",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#A0A0C0").grid(
                         row=4, column=0, sticky="w", padx=10, pady=(0, 2))

        self.mode_help_text = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#0D1117",
            text_color="#C0C0C0",
            corner_radius=8,
            wrap="none",
            state="disabled",
        )
        self.mode_help_text.grid(row=5, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self._set_mode_help_text("Haz clic en un modo para ver sus comandos.")

    # ─────────────────────────── MODE HELP ───────────────────────────────────

    def _mode_button_action(self, mode_name: str):
        self._update_mode_help(mode_name)
        self.send_shortcut(f"mode {mode_name}")

    def _set_mode_help_text(self, text: str):
        if self.mode_help_text is None:
            return
        self.mode_help_text.configure(state="normal")
        self.mode_help_text.delete("1.0", "end")
        self.mode_help_text.insert("1.0", text)
        self.mode_help_text.configure(state="disabled")

    def _update_mode_help(self, mode_name: str):
        commands = MODE_COMMANDS.get(mode_name.lower())
        if commands is None:
            self._set_mode_help_text(f"(Sin comandos registrados para '{mode_name}')")
            return
        header = f"── {mode_name.upper()} ──\n"
        self._set_mode_help_text(header + commands)

    # ─────────────────────────── SESSION LOG ─────────────────────────────────

    def export_session_log(self):
        content = self.output_text.get("1.0", "end")
        if not content.strip():
            self.append_output("No hay contenido para guardar.\n", "error")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            title="Guardar log de sesión",
            initialfile=f"buspirate_session_{timestamp}.txt",
            defaultextension=".txt",
            filetypes=[("Texto plano", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("# ESP32 Bus Pirate — Session Log\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Puerto: {self.port_var.get()}\n")
                f.write("# " + "─" * 58 + "\n\n")
                f.write(content)
            self.append_output(f"Log guardado: {os.path.basename(path)}\n", "info")
        except Exception as e:
            self.append_output(f"Error al guardar log: {e}\n", "error")

    # ──────────────────────────── FIRMWARE TAB ───────────────────────────────

    def create_firmware_tab(self):
        tab = self.shortcut_tabs.add("Firmware")

        ctk.CTkLabel(tab, text="Flash Firmware",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 0))
        ctk.CTkLabel(tab, text="ESP32 Bus Pirate · DevKit",
                     font=ctk.CTkFont(size=11), text_color="#A0A0A0").pack(pady=(0, 8))

        # ── Sección: Archivo local ──────────────────────────────────────────
        local_frame = ctk.CTkFrame(tab, fg_color="#1A1A2E", corner_radius=8)
        local_frame.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(local_frame, text="Archivo local",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#A0A0C0").pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkButton(
            local_frame, text="📂  Seleccionar .bin...",
            command=self._browse_bin_file,
            fg_color="#2D5A8E", hover_color="#1F3F66"
        ).pack(fill="x", padx=10, pady=(0, 4))

        self.local_bin_label = ctk.CTkLabel(
            local_frame, text="Sin archivo seleccionado",
            font=ctk.CTkFont(size=10), text_color="#707070", wraplength=300
        )
        self.local_bin_label.pack(pady=(0, 4))

        self.local_flash_btn = ctk.CTkButton(
            local_frame, text="Flashear archivo local",
            command=self._flash_local,
            fg_color="#5A3A8E", hover_color="#3F2A66", state="disabled"
        )
        self.local_flash_btn.pack(fill="x", padx=10, pady=(0, 10))

        # ── Separador ──────────────────────────────────────────────────────
        ctk.CTkFrame(tab, height=1, fg_color="#333355").pack(fill="x", padx=10, pady=(4, 8))

        # ── Sección: GitHub Releases ────────────────────────────────────────
        ctk.CTkLabel(tab, text="GitHub Releases",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#A0A0C0").pack(anchor="w", padx=10, pady=(0, 4))

        ctk.CTkButton(
            tab, text="🔄  Buscar versiones",
            command=self._fetch_releases_async,
            fg_color="#2D5A8E", hover_color="#1F3F66"
        ).pack(fill="x", padx=10, pady=(0, 6))

        self.fw_status_label = ctk.CTkLabel(
            tab, text="Presiona 'Buscar versiones'",
            font=ctk.CTkFont(size=11), text_color="#909090", wraplength=320
        )
        self.fw_status_label.pack(pady=(0, 6))

        self.fw_version_combo = ctk.CTkComboBox(
            tab, variable=self.fw_version_var,
            values=["—  sin versiones  —"],
            width=330, state="disabled"
        )
        self.fw_version_combo.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(
            tab,
            text="⚠️  Desconectar del serial antes de flashear",
            font=ctk.CTkFont(size=11), text_color="#FFA040", wraplength=320
        ).pack(pady=(0, 6))

        self.fw_flash_btn = ctk.CTkButton(
            tab, text="Descargar y Flashear",
            command=self.download_and_flash,
            fg_color="#8B1A1A", hover_color="#6B1010", state="disabled"
        )
        self.fw_flash_btn.pack(fill="x", padx=10, pady=(0, 10))

    # ─────────────────────────── FIRMWARE FLASH ──────────────────────────────

    def _browse_bin_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar firmware .bin",
            filetypes=[("Firmware binario", "*.bin"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return
        self.local_bin_path = path
        filename = os.path.basename(path)
        display = filename if len(filename) <= 36 else f"...{filename[-33:]}"
        self.local_bin_label.configure(text=display, text_color="#E0E0E0")
        self.local_flash_btn.configure(state="normal")

    def _flash_local(self):
        if not self.local_bin_path:
            self.append_output("Selecciona un archivo .bin primero\n", "error")
            return

        port_selection = self.port_var.get()
        if not port_selection or "No hay" in port_selection:
            self.append_output("Selecciona un puerto serial válido\n", "error")
            return

        port = port_selection.split(" - ")[0]

        if self.connected:
            self.append_output("Desconectando serial para flashear...\n", "info")
            self.disconnect()
            time.sleep(0.5)

        self.local_flash_btn.configure(state="disabled")
        threading.Thread(
            target=self._flash_local_worker,
            args=(self.local_bin_path, port),
            daemon=True
        ).start()

    def _flash_local_worker(self, fw_path: str, port: str):
        try:
            filename = os.path.basename(fw_path)
            self.output_queue.put(("info", f"\nFlasheando {filename} en {port}...\n"))

            result = subprocess.run(
                [
                    "python", "-m", "esptool",
                    "--chip", "esp32-s3",
                    "--port", port,
                    "--baud", "460800",
                    "write_flash",
                    "--flash_mode", "dio",
                    "-z", "0x0",
                    fw_path,
                ],
                capture_output=True, text=True, timeout=180
            )

            if result.returncode == 0:
                self.output_queue.put(("info", "Flash exitoso! Reinicia el dispositivo.\n"))
                if result.stdout:
                    self.output_queue.put(("response", result.stdout + "\n"))
            else:
                self.output_queue.put(("error", f"Error al flashear:\n{result.stderr}\n"))

        except Exception as e:
            self.output_queue.put(("error", f"Flash fallido: {e}\n"))
        finally:
            self.root.after(0, lambda: self.local_flash_btn.configure(state="normal"))

    def _fetch_releases_async(self):
        self.fw_status_label.configure(text="Buscando versiones en GitHub...")
        threading.Thread(target=self._fetch_releases_worker, daemon=True).start()

    def _fetch_releases_worker(self):
        try:
            req = urllib.request.Request(
                FIRMWARE_API_URL,
                headers={"User-Agent": "BusPirateCompanion/1.0", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                releases = json.loads(resp.read().decode())

            self.firmware_releases = {}
            for release in releases:
                tag = release.get("tag_name", "")
                date = release.get("published_at", "")[:10]
                display_key = f"{tag}  ({date})" if date else tag
                # Prefer assets with "s3devkitn16r8" in name, fall back to any .bin
                bin_url = None
                for asset in release.get("assets", []):
                    name = asset["name"].lower()
                    if name.endswith(".bin") and "s3devkitn16r8" in name:
                        bin_url = asset["browser_download_url"]
                        break
                if not bin_url:
                    for asset in release.get("assets", []):
                        if asset["name"].lower().endswith(".bin"):
                            bin_url = asset["browser_download_url"]
                            break
                if bin_url:
                    self.firmware_releases[display_key] = bin_url

            if self.firmware_releases:
                versions = list(self.firmware_releases.keys())
                self.root.after(0, lambda: self._update_firmware_ui(versions))
            else:
                self.root.after(0, lambda: self.fw_status_label.configure(
                    text="No se encontraron archivos .bin en los releases"))
        except Exception as e:
            msg = str(e)[:60]
            self.root.after(0, lambda: self.fw_status_label.configure(text=f"Error: {msg}"))

    def _update_firmware_ui(self, versions: list):
        self.fw_version_combo.configure(values=versions, state="readonly")
        self.fw_version_var.set(versions[0])
        self.fw_flash_btn.configure(state="normal")
        self.fw_status_label.configure(
            text=f"{len(versions)} versiones encontradas",
            text_color="#4CAF50"
        )

    def download_and_flash(self):
        version_key = self.fw_version_var.get()
        if not version_key or version_key.startswith("—"):
            self.append_output("Selecciona una versión primero\n", "error")
            return

        url = self.firmware_releases.get(version_key)
        if not url:
            self.append_output("URL de firmware no encontrada\n", "error")
            return

        port_selection = self.port_var.get()
        if not port_selection or "No hay" in port_selection:
            self.append_output("Selecciona un puerto serial válido\n", "error")
            return

        port = port_selection.split(" - ")[0]

        if self.connected:
            self.append_output("Desconectando serial para flashear...\n", "info")
            self.disconnect()
            time.sleep(0.5)

        self.fw_flash_btn.configure(state="disabled")
        threading.Thread(target=self._flash_worker, args=(url, version_key, port), daemon=True).start()

    def _flash_worker(self, url: str, version_key: str, port: str):
        try:
            self.output_queue.put(("info", f"\nDescargando {version_key}...\n"))
            req = urllib.request.Request(url, headers={"User-Agent": "BusPirateCompanion/1.0"})
            with tempfile.TemporaryDirectory() as tmpdir:
                fw_path = os.path.join(tmpdir, "firmware.bin")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                with open(fw_path, "wb") as f:
                    f.write(data)

                size_kb = len(data) // 1024
                self.output_queue.put(("info", f"Descargado ({size_kb} KB)\n"))
                self.output_queue.put(("info", f"Flasheando en {port}...\n"))

                result = subprocess.run(
                    [
                        "python", "-m", "esptool",
                        "--chip", "esp32-s3",
                        "--port", port,
                        "--baud", "460800",
                        "write_flash",
                        "--flash_mode", "dio",
                        "-z", "0x0",
                        fw_path,
                    ],
                    capture_output=True, text=True, timeout=180
                )

                if result.returncode == 0:
                    self.output_queue.put(("info", "Flash exitoso! Reinicia el dispositivo.\n"))
                    if result.stdout:
                        self.output_queue.put(("response", result.stdout + "\n"))
                else:
                    self.output_queue.put(("error", f"Error al flashear:\n{result.stderr}\n"))

        except Exception as e:
            self.output_queue.put(("error", f"Flash fallido: {e}\n"))
        finally:
            self.root.after(0, lambda: self.fw_flash_btn.configure(state="normal"))

    # ──────────────────────────── SERIAL / IO ────────────────────────────────

    def setup_styles(self):
        self.output_text.tag_config("command",   foreground="#4CAF50")
        self.output_text.tag_config("response",  foreground="#E0E0E0")
        self.output_text.tag_config("error",     foreground="#FF6B6B")
        self.output_text.tag_config("info",      foreground="#2196F3")
        self.output_text.tag_config("timestamp", foreground="#9E9E9E")

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.configure(values=["No hay puertos disponibles"])
            self.port_var.set("No hay puertos disponibles")
            return

        port_list = [f"{p.device} - {p.description or 'Sin descripción'}" for p in ports]
        self.port_combo.configure(values=port_list)

        last_port = self.config.get("last_port", "")
        selected = False
        if last_port:
            for entry in port_list:
                if entry.startswith(last_port):
                    self.port_var.set(entry)
                    selected = True
                    break
        if not selected and port_list:
            self.port_var.set(port_list[0])

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port_selection = self.port_var.get()
        if not port_selection or "No hay" in port_selection:
            self.append_output("Error: Selecciona un puerto válido\n", "error")
            return

        port = port_selection.split(" - ")[0]
        baudrate = int(self.baudrate_var.get())

        try:
            self.append_output(f"Conectando a {port} @ {baudrate} baudios...\n", "info")
            self.ser = serial.Serial(
                port=port, baudrate=baudrate,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=0.1
            )
            time.sleep(0.5)
            self.ser.write(b'\n')
            self.ser.flush()
            time.sleep(0.2)

            welcome = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            if welcome:
                cleaned = clean_echo_spam(clean_ansi(welcome))
                if cleaned.strip():
                    self.append_output(cleaned, "response")

            self.connected = True
            self.running = True
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()

            self.connect_btn.configure(text="Desconectar", fg_color="#FF6B6B", hover_color="#E85555")
            self.status_label.configure(text="● Conectado", text_color="#4CAF50")
            self.port_combo.configure(state="disabled")

            self.config["last_port"] = port
            self.config["last_baudrate"] = str(baudrate)
            save_config(self.config)

            self.append_output("Conectado exitosamente!\n", "info")

        except serial.SerialException as e:
            self.append_output(f"Error al conectar: {e}\n", "error")

    def disconnect(self):
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
        self.connect_btn.configure(text="Conectar", fg_color="#4CAF50", hover_color="#45A049")
        self.status_label.configure(text="● Desconectado", text_color="#FF6B6B")
        self.port_combo.configure(state="readonly")
        self.append_output("🔌 Desconectado del Bus Pirate\n", "info")

    def read_serial(self):
        buffer = ""
        last_data_time = 0
        BUFFER_TIMEOUT = 0.15

        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    last_data_time = time.time()
                elif buffer and (time.time() - last_data_time) > BUFFER_TIMEOUT:
                    cleaned = clean_echo_spam(clean_ansi(buffer))
                    if cleaned.strip():
                        self.output_queue.put(("response", cleaned))
                    buffer = ""
                time.sleep(0.02)
            except Exception as e:
                self.output_queue.put(("error", f"Error de lectura: {e}\n"))
                break

    def send_command(self):
        cmd = self.input_entry.get().strip()
        if not self.connected:
            self.append_output("No conectado al Bus Pirate\n", "error")
            return

        if cmd:
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.append_output(f"[{timestamp}] ", "timestamp")
            self.append_output(f"BP> {cmd}\n", "command")

        try:
            self.ser.write(f"{cmd}\n".encode('utf-8'))
            self.ser.flush()
        except Exception as e:
            self.append_output(f"Error al enviar: {e}\n", "error")

        self.input_entry.delete(0, "end")

    def send_shortcut(self, cmd: str):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, cmd)
        self.send_command()

    def _terminal_key_filter(self, event):
        # Allow navigation, selection, and copy shortcuts
        if event.state & 0x4:  # Ctrl held
            if event.keysym.lower() in ('c', 'a'):
                return None
        if event.keysym in (
            'Left', 'Right', 'Up', 'Down',
            'Home', 'End', 'Prior', 'Next',
            'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
        ):
            return None
        return "break"

    def append_output(self, text: str, tag: str = "response"):
        self.output_text.insert("end", text, tag)
        self.output_text.see("end")

    def clear_terminal(self):
        self.output_text.delete("1.0", "end")

    def update_output(self):
        try:
            while True:
                tag, text = self.output_queue.get_nowait()
                self.append_output(text, tag)
        except queue.Empty:
            pass
        self.root.after(50, self.update_output)

    def history_up(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])

    def history_down(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.input_entry.delete(0, "end")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if self.connected:
            self.disconnect()
        self.root.destroy()


def main():
    app = BusPirateGUI()
    app.run()


if __name__ == "__main__":
    main()
