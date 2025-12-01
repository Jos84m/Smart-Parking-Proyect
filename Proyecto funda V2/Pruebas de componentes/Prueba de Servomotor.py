from machine import Pin, PWM
import time

servoprofe = PWM(Pin(28))
servoprofe.freq(50)

v_grados = 45
v_repetir = 2

# Función para convertir grados a duty_ns
def map_grados(x):
    return int((x * (2500000 - 500000) / 180) + 500000)

# Función que mueve el servo entre 0° y 180° cierto número de veces
def mover_servo(repetir):
    for g in range(repetir):
        # 0 grados
        m = map_grados(0)
        servoprofe.duty_ns(m)
        time.sleep(2)

        # 180 grados
        m = map_grados(180)
        servoprofe.duty_ns(m)
        time.sleep(2)

# Llamada a la función
mover_servo(v_repetir)
