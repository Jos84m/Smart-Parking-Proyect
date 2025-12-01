from machine import Pin
import time

# -------------------------------
# PINES DE SEGMENTOS (YA DADOS)
# -------------------------------
segment_pins = [
    Pin(12, Pin.OUT),  # a
    Pin(13, Pin.OUT),  # b
    Pin(4, Pin.OUT),  # c
    Pin(5, Pin.OUT),  # d
    Pin(6, Pin.OUT),  # e
    Pin(11, Pin.OUT),  # f
    Pin(10, Pin.OUT)   # g
]

# -------------------------------
# MATRIZ DE DIGITOS (YA DADA)
# -------------------------------
digits = [
    [0, 0, 0, 0, 0, 0, 1],  # 0
    [1, 0, 0, 1, 1, 1, 1],  # 1
    [0, 0, 1, 0, 0, 1, 0],  # 2
    [0, 0, 0, 0, 1, 1, 0],  # 3
    [1, 0, 0, 1, 1, 0, 0],  # 4
    [0, 1, 0, 0, 1, 0, 0],  # 5
    [0, 1, 0, 0, 0, 0, 0],  # 6
    [0, 0, 0, 1, 1, 1, 1],  # 7
    [0, 0, 0, 0, 0, 0, 0],  # 8
    [0, 0, 0, 0, 1, 0, 0],  # 9
    [0, 0, 0, 1, 0, 0, 0],  # A
    [1, 1, 0, 0, 0, 0, 0],  # B
    [0, 1, 1, 0, 0, 0, 1],  # C
    [1, 0, 0, 0, 0, 1, 0],  # D
    [0, 1, 1, 0, 0, 0, 0],  # E
    [0, 1, 1, 1, 0, 0, 0],  # F
]

# -------------------------------
# FUNCIÓN PARA MOSTRAR UN DÍGITO
# -------------------------------
def mostrar_digito(num):
    patrón = digits[num]
    for i in range(7):
        segment_pins[i].value(patrón[i])

# -------------------------------
# PROGRAMA PRINCIPAL
# -------------------------------
try:
    secuencia = [3, 4, 8, 9]  # << LO QUE PEDISTE (3,4,8,9)
    
    while True:
        for numero in secuencia:
            print("Mostrando:", numero)
            mostrar_digito(numero)
            time.sleep(1)

except KeyboardInterrupt:
    for pin in segment_pins:
        pin.value(1)
    print("Finalizado")
