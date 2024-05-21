import machine
import utime
import math
import handleJson

# Configurar los pines ADC para los tres sensores
adc_pins = [machine.ADC(26), machine.ADC(27), machine.ADC(28)]

# Leer el valor base del ADC cuando no hay corriente
def leer_valor_base(adc_pin):
    num_lecturas = 100
    suma = 0
    for _ in range(num_lecturas):
        suma += adc_pin.read_u16()
        utime.sleep_ms(10)  # Intervalo de espera consistente con el código original
    valor_base = suma / num_lecturas
    voltaje_base = (valor_base / 65535) * 3.3
    return voltaje_base

# Calibrar el voltaje base para cada sensor
voltajes_base = [leer_valor_base(adc_pin) for adc_pin in adc_pins]
print("Voltajes base:", voltajes_base)

def leer_corriente_rms(adc_pin, voltaje_base, num_muestras, intervalo_ms):
    suma_cuadrados = 0
    for _ in range(num_muestras):
        valor_adc = adc_pin.read_u16()
        voltaje = (valor_adc / 65535) * 3.3
        corriente = (voltaje - voltaje_base) / 0.1
        suma_cuadrados += corriente ** 2
        utime.sleep_ms(intervalo_ms)  # Intervalo de espera consistente con el código original
    
    corriente_rms = math.sqrt(suma_cuadrados / num_muestras)
    return corriente_rms

# Obtener límites de corriente desde el servidor
limites = handleJson.get_limits()
if not limites:
    print("Error al obtener los límites de corriente.")
    limites = {"MaxAmp_1": 10, "MaxAmp_2": 10, "MaxAmp_3": 10}  # Valores por defecto
else:
    print("Límites de corriente:", limites)

while True:
    corrientes_rms = [leer_corriente_rms(adc_pin, voltajes_base[i], 100, 2) for i, adc_pin in enumerate(adc_pins)]
    print("Corrientes RMS: Sensor 1: {:.2f} A, Sensor 2: {:.2f} A, Sensor 3: {:.2f} A".format(*corrientes_rms))
    
    # Comprobar si alguna corriente supera los límites
    if corrientes_rms[0] > limites["MaxAmp_1"]:
        print("Alerta: Sensor 1 supera el límite!")
    if corrientes_rms[1] > limites["MaxAmp_2"]:
        print("Alerta: Sensor 2 supera el límite!")
    if corrientes_rms[2] > limites["MaxAmp_3"]:
        print("Alerta: Sensor 3 supera el límite!")
    
    utime.sleep(0.1)  # Intervalo de espera entre ciclos de lectura

