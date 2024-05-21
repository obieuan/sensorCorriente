import network
import urequests as requests
import ujson
import utime
from secrets import ssid, password, token, url

# Configuración del WiFi
wlan = network.WLAN(network.STA_IF)

def conectar_wifi():
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            print("Conectando a WiFi...")
            utime.sleep(1)
        print("Conectado a WiFi. Dirección IP:", wlan.ifconfig()[0])

def post_json(url, json_data):
    """Envía un POST con JSON a una URL.

    Args:
        url: La URL a la que se enviará la solicitud.
        json_data: Los datos JSON a enviar.

    Returns:
        La respuesta de la solicitud.
    """

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=json_data)  # Use json parameter to send JSON data
    except Exception as e:
        print("Error sending JSON request:", str(e))
        return None
    return response

def get_limits():
    conectar_wifi()  # Asegurarse de estar conectado antes de solicitar los límites
    json_data = {
        "TokenApi": token,
        "Comando": "Solicitar"
    }
    response = post_json(url, json_data)
    if response is not None and response.status_code == 200:
        response_json = response.json()  # Parsear la respuesta JSON directamente a un diccionario Python
        print(response_json)  # Imprimir todo el JSON para depuración
        sensores = response_json.get("Sensores:", {})
        return {
            "MaxAmp_1": sensores.get("MaxAmp_1", 10),
            "MaxAmp_2": sensores.get("MaxAmp_2", 10),
            "MaxAmp_3": sensores.get("MaxAmp_3", 10)
        }
    else:
        print("Error en la solicitud HTTP:", response)
        return {}

