import machine
import utime
import math
import handleJson

# Configurar los pines ADC para los tres sensores y el pin del relevador
adc_pins = [machine.ADC(26), machine.ADC(27), machine.ADC(28)]
relay_pin = machine.Pin(15, machine.Pin.OUT)  # Ajusta el pin según tu configuración

# Conectar a WiFi al inicio
handleJson.conectar_wifi()

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

# Función para enviar el log
def enviar_log(limites, corrientes_rms):
    json_data = {
        "TokenApi": handleJson.token,
        "Comando": "Log",
        "MaxAmp_1": limites["MaxAmp_1"],
        "MaxAmp_2": limites["MaxAmp_2"],
        "MaxAmp_3": limites["MaxAmp_3"],
        "SensCon_1": corrientes_rms[0],
        "SensCon_2": corrientes_rms[1],
        "SensCon_3": corrientes_rms[2]
    }
    response = handleJson.post_json(handleJson.url, json_data)
    if response and response.status_code == 200:
        print("Log enviado correctamente")
    else:
        print("Error al enviar el log")

# Obtener límites de corriente desde el servidor
limites = handleJson.get_limits()
if not limites:
    print("Error al obtener los límites de corriente.")
    limites = {"MaxAmp_1": 10, "MaxAmp_2": 10, "MaxAmp_3": 10}  # Valores por defecto
else:
    print("Límites de corriente:", limites)

# Variables para controlar el envío del log y actualización de límites
ultimo_envio = 0
intervalo_envio = 10  # 10 segundos
ultimo_chequeo = 0
intervalo_chequeo = 5  # 5 segundos

while True:
    corrientes_rms = [leer_corriente_rms(adc_pin, voltajes_base[i], 100, 2) for i, adc_pin in enumerate(adc_pins)]
    print("Corrientes RMS: Sensor 1: {:.2f} A, Sensor 2: {:.2f} A, Sensor 3: {:.2f} A".format(*corrientes_rms))
    
    # Comprobar si alguna corriente supera los límites
    alarma = False
    if corrientes_rms[0] > limites["MaxAmp_1"]:
        print("Alerta: Sensor 1 supera el límite!")
        alarma = True
    if corrientes_rms[1] > limites["MaxAmp_2"]:
        print("Alerta: Sensor 2 supera el límite!")
        alarma = True
    if corrientes_rms[2] > limites["MaxAmp_3"]:
        print("Alerta: Sensor 3 supera el límite!")
        alarma = True
    
    if alarma:
        relay_pin.value(1)  # Encender el relevador
        if utime.time() - ultimo_envio > intervalo_envio:
            enviar_log(limites, corrientes_rms)
            ultimo_envio = utime.time()
    else:
        relay_pin.value(0)  # Apagar el relevador si no hay alarma
    
    # Actualizar límites de corriente cada 5 segundos
    if utime.time() - ultimo_chequeo > intervalo_chequeo:
        nuevos_limites = handleJson.get_limits()
        if nuevos_limites:
            limites = nuevos_limites
        ultimo_chequeo = utime.time()
    
    utime.sleep(0.1)  # Intervalo de espera entre ciclos de lectura

