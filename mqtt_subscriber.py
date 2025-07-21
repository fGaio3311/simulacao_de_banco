import json
import time
import logging
import socket
from paho.mqtt import client as mqtt_client  # type: ignore[import]
from twin import twin  # Importe do novo módulo

# Configuração do broker
try:
    # Tenta resolver o nome Docker
    socket.gethostbyname('mqtt-broker')
    BROKER_HOST = 'mqtt-broker'
    print("Usando broker Docker: mqtt-broker")
except socket.gaierror:
    BROKER_HOST = 'localhost'
    print("Usando broker local: localhost")

BROKER_PORT = 1883
TOPIC = 'banco/+/events'
CLIENT_ID = f'twin-subscriber-{int(time.time())}'

# Setup de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("mqtt-subscriber")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT em {BROKER_HOST}:{BROKER_PORT}!")
        client.subscribe(TOPIC, qos=1)
    else:
        logger.error(f"Falha de conexão, código {rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        ev = json.loads(payload)
        logger.info(f"Recebido no tópico {msg.topic}: {ev}")

        # Aplica o evento diretamente no Digital Twin em memória
        twin.apply_event(ev)

        # Log adicional para debug
        logger.info(f"Estado atual do Twin: {twin.summary()}")
    except json.JSONDecodeError:
        logger.error(f"Mensagem com formato inválido: {msg.payload}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)


def run_subscriber():
    client = mqtt_client.Client(
        client_id=CLIENT_ID,
        protocol=mqtt_client.MQTTv311,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect
    client.on_message = on_message

    # Configuração de reconexão automática
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    logger.info(f"Conectando a {BROKER_HOST}:{BROKER_PORT}...")

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_forever()
    except ConnectionRefusedError:
        logger.error("Conexão recusada. Verifique se o broker MQTT está ativo.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)


if __name__ == "__main__":
    run_subscriber()
