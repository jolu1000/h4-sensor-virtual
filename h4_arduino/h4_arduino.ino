/*
  Proyecto H4 - Sensor virtual y reconfiguración ante fallas físicas
  Primer hito: lectura del sensor a sustituir (HC-SR04 #1) y de una
  variable correlacionada (HC-SR04 #2 + ángulo del servo).

  El Arduino mide y mueve el servo; la Raspberry Pi recibe los datos por
  USB y les pone la marca de tiempo al guardarlos en SQLite.

  Salida por serial (115200 baudios), una línea por muestra:
      t_ms,angulo,d1_cm,d2_cm
  d1/d2 = -1 cuando el sensor no responde (sin eco / desconectado).

  Comandos que se pueden enviar por serial:
      S      -> modo barrido (el servo va y vuelve solo)
      A90    -> fija el servo en 90 grados (cualquier valor 0-180)
*/

#include <Servo.h>

// ---- Pines ----
const int TRIG1 = 2;   // HC-SR04 #1 (sensor a sustituir)
const int ECHO1 = 3;
const int TRIG2 = 4;   // HC-SR04 #2 (variable correlacionada)
const int ECHO2 = 5;
const int SERVO_PIN = 9;

// ---- Parámetros ----
const unsigned long PERIODO_MS = 100;    // 10 muestras por segundo
const unsigned long TIMEOUT_US = 25000;  // ~4 m; si no hay eco -> -1
const int ANG_MIN = 30;
const int ANG_MAX = 150;
const int PASO_BARRIDO = 2;              // grados por muestra en barrido

Servo servo;
int angulo = 90;
int direccion = 1;
bool barrido = true;
unsigned long ultimo = 0;
String comando = "";

float medirDistancia(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long dur = pulseIn(echo, HIGH, TIMEOUT_US);
  if (dur == 0) return -1.0;             // sin eco: falla o fuera de rango
  return dur * 0.0343 / 2.0;             // velocidad del sonido ~343 m/s
}

void leerComandos() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      comando.trim();
      if (comando == "S") {
        barrido = true;
      } else if (comando.startsWith("A")) {
        int a = comando.substring(1).toInt();
        angulo = constrain(a, 0, 180);
        barrido = false;
        servo.write(angulo);
      }
      comando = "";
    } else {
      comando += c;
    }
  }
}

void setup() {
  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);
  servo.attach(SERVO_PIN);
  servo.write(angulo);
  Serial.begin(115200);
  Serial.println("# t_ms,angulo,d1_cm,d2_cm");
}

void loop() {
  leerComandos();

  unsigned long ahora = millis();
  if (ahora - ultimo < PERIODO_MS) return;
  ultimo = ahora;

  if (barrido) {
    angulo += direccion * PASO_BARRIDO;
    if (angulo >= ANG_MAX || angulo <= ANG_MIN) direccion = -direccion;
    angulo = constrain(angulo, ANG_MIN, ANG_MAX);
    servo.write(angulo);
  }

  // Se disparan por turnos, con una pausa, para que el eco de uno
  // no lo capture el otro (interferencia cruzada).
  float d1 = medirDistancia(TRIG1, ECHO1);
  delay(15);
  float d2 = medirDistancia(TRIG2, ECHO2);

  Serial.print(ahora);
  Serial.print(',');
  Serial.print(angulo);
  Serial.print(',');
  Serial.print(d1, 1);
  Serial.print(',');
  Serial.println(d2, 1);
}
