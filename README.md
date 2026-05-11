# ESP32 Piratebus Kit

<p align="center"> <strong>Desarrollado por Glitchboi</strong><br> Seguridad desde México para todos </p>

![Estado](https://img.shields.io/badge/status-En_desarrollo-yellow) ![License](https://img.shields.io/badge/license-MIT-blue) ![Hardware](https://img.shields.io/badge/hardware-ESP32-red) ![EasyEDA](https://img.shields.io/badge/EDA-EasyEDA-blue)

---

## Descripción

PCB personalizada que expande el proyecto [ESP32-Bus-Pirate](https://github.com/geo-tp/ESP32-Bus-Pirate) con módulos integrados para NFC, Ethernet y Sub-GHz, todo en un solo kit de hardware orientado a seguridad e investigación. Inspirado en el combo **HackerBox 0124: Bus Driver**, este proyecto nació para tener una plataforma compacta, accesible y open-source para pentesting de protocolos y comunicaciones inalámbricas.

---

## Características

- Base compatible con [ESP32-Bus-Pirate](https://github.com/geo-tp/ESP32-Bus-Pirate)
- Módulo **NFC** (PN532) para análisis y emulación de tarjetas
- Módulo **Ethernet** (W5500) para sniffing y análisis en red local
- Módulo **Sub-GHz / 2.4 GHz** (CC1101/nRF24L01) para análisis de protocolos como 433/868/915 MHz y Wi-Fi / Zigbee / BLE
- Archivos de diseño disponibles en **EasyEDA Pro** (`.epro`) y **Gerbers** listos para fabricar

---

## Módulos

| Módulo                              | Descripción                                                           | Documentación                       |
| ----------------------------------- | --------------------------------------------------------------------- | ----------------------------------- |
| [Buspirate Main](Buspirate_Main/)   | PCB principal con ESP32, base del sistema                             | [README](Buspirate_Main/README.md)  |
| [NFC Module](NFC_Module/)           | Lectura, escritura y emulación NFC (PN532)                            | [README](NFC_Module/README.md)      |
| [Ethernet Module](Ethernet_Module/) | Interfaz de red cableada (W5500)                                      | [README](Ethernet_Module/README.md) |
| [SubGhz Module](SubGhz_Module/)     | RF en bandas 433/868/915 MHz y Wi-Fi / Zigbee / BLE (CC1101/nRF24L01) | [README](SubGhz_Module/README.md)   |

> Cada módulo tiene su propio README con información detallada.

---

## Estructura del Repositorio

```
ESP32-Piratebus-Kit/
├── Buspirate_Main/
│   ├── README.md
│   ├── Buspirate_Main.epro
│   └── Buspirate_Main.zip
├── NFC_Module/
│   ├── README.md
│   ├── NFC_Module.epro
│   └── NFC_Module.zip
├── Ethernet_Module/
│   ├── README.md
│   ├── EthernetModule.epro
│   └── Ethernet_Module.zip
├── SubGhz_Module/
│   ├── README.md
│   ├── SubGhz_Module.epro
│   └── SubGhzModule.zip
├── docs/
│   └── logo.png
├── LICENSE
└── README.md
```

---

## Fabricación

Los archivos de diseño están disponibles en dos formatos:

### EasyEDA Pro

Importa el proyecto directamente:

1. Abre [EasyEDA Pro](https://pro.easyeda.com)
2. `File > Open > Project`
3. Selecciona el archivo `.epro` del módulo correspondiente

### Gerbers (fabricación directa)

Los archivos `.zip` están listos para subir a cualquier servicio de fabricación (JLCPCB, PCBWay, etc.).

**Parámetros recomendados:**

- Capas: 2
- Grosor de PCB: 1.6 mm
- Acabado superficial: HASL / ENIG
- Color de soldermask: a tu gusto

---

## Uso

Una vez ensamblada la PCB, flashea el firmware de [ESP32-Bus-Pirate](https://github.com/geo-tp/ESP32-Bus-Pirate) siguiendo su documentación oficial:

```bash
git clone https://github.com/geo-tp/ESP32-Bus-Pirate.git
cd ESP32-Bus-Pirate
# Sigue las instrucciones del proyecto original para flash
```

---

## Contribuir

Este proyecto no solo es un repositorio: es un espacio abierto para aprender, experimentar y construir juntos. **Buscamos activamente contribuciones**, ya sea en la parte técnica o en la documentación.

- **En hardware:** Si detectas oportunidades para mejorar la eficiencia (otros chips, consumo de energía, alternativas de componentes), ¡tus sugerencias son bienvenidas!
- **En diseño PCB:** Mejoras al ruteo, optimizaciones de señal, ajustes de footprint o integración de nuevos módulos.
- **En documentación:** Si algo puede explicarse mejor o más claro, abre un PR directo.

No necesitas ser experto. Si ves algo mejorable, **cuéntanos o abre un Pull Request**.

---

## Créditos

- Proyecto basado en [ESP32-Bus-Pirate](https://github.com/geo-tp/ESP32-Bus-Pirate) hecho por [geo-tp](https://github.com/geo-tp)
- Inspirado en [HackerBox 0124: Bus Driver](https://hackerboxes.com)

Diseñado / Modificado por:
- [Glitchboi](https://www.linkedin.com/in/erik-alc%C3%A1ntara-covarrubias-29a97628a)
