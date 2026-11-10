# Proyecto H4 — Primer hito

**Objetivo del hito (rúbrica):** lectura del sensor a sustituir y de una variable correlacionada, registradas con marca de tiempo.

- Sensor a sustituir: HC-SR04 #1 (`d1_cm`)
- Variable correlacionada: HC-SR04 #2 (`d2_cm`) + ángulo del servo (`angulo`)
- El Arduino mide y mueve el servo; la Raspberry Pi guarda todo en SQLite con marca de tiempo.

## Archivos

| Archivo | Dónde corre | Qué hace |
|---|---|---|
| `h4_arduino/h4_arduino.ino` | Arduino UNO | Mide los dos HC-SR04 a 10 Hz, mueve el servo en barrido y manda `t_ms,angulo,d1,d2` por USB |
| `registrar.py` | Raspberry Pi | Lee el USB, agrega la marca de tiempo y guarda en `h4_lecturas.db` |
| `graficar.py` | Raspberry Pi o PC | Genera `evidencia_hito1.png` (series de tiempo + correlación d1 vs d2) |
| `diagrama_conexiones.png` | — | Esquema general de conexiones |
| `protoboard_montaje.png` | — | Dónde va cada cable en la protoboard, agujero por agujero |

## ¿En qué sistema corre?

- `h4_arduino.ino` corre **dentro del Arduino**. Se sube con el Arduino IDE desde Windows, Linux (Pop!_OS) o la misma Raspberry.
- `registrar.py` y `graficar.py` funcionan igual en **Raspberry Pi OS, Pop!_OS y Windows**. El puerto se detecta solo: en Linux es `/dev/ttyUSB0` y en Windows, `COM3` o similar.
- **Pop!_OS / Linux:** para tener permiso de leer el USB, ejecuta una vez `sudo usermod -aG dialout $USER` y cierra y vuelve a abrir la sesión.
- **Windows:** usa `python` en vez de `python3`. Si no aparece el puerto, instala el driver CH340.

## Pasos

1. **Conexiones:** sigue `diagrama_conexiones.png`. Todo va al Arduino; la Raspberry solo se conecta al Arduino por el cable USB.
2. **Cargar el sketch:** abre `h4_arduino.ino` en el Arduino IDE (desde un PC o desde la Raspberry), elige *Arduino Uno* y el puerto, y súbelo.
   Si el IDE no reconoce el puerto, el clon usa el chip CH340: en Windows hay que instalar su driver.
   Prueba rápida: abre el Monitor Serie a 115200 baudios y deberías ver líneas como `12345,90,18.4,19.9`.
3. **En la Raspberry:**
   ```bash
   pip install pyserial matplotlib numpy      # en Raspberry Pi OS reciente: agrega --break-system-packages
   python3 registrar.py --duracion 120        # graba 2 minutos
   python3 graficar.py                        # crea evidencia_hito1.png
   ```
   Sin hardware puedes probar todo con `python3 registrar.py --simular --duracion 20`.
4. **Para el informe:** el gráfico `evidencia_hito1.png` (trae fecha y hora), una foto del montaje y el repositorio con commits.

## Comandos del servo (desde el Monitor Serie)

- `S` → barrido automático entre 30° y 150°
- `A90` → fija el servo en 90° (cualquier valor de 0 a 180)

## Notas

- `d1`/`d2` se guardan como NULL cuando el sensor no devuelve eco (desconectado, tapado o fuera de rango). Eso es justamente lo que después usarán para detectar las fallas.
- Si el Arduino se reinicia cuando el servo se mueve, el servo está pidiendo demasiada corriente del USB: pongan un condensador (100–470 µF) entre 5V y GND, o alimenten el servo aparte (uniendo los GND).
