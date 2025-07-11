import json
import time
import logging
from paho.mqtt import client as mqtt_client
from main import twin  # importa a instância do seu Digital Twin já carregada pela FastAPI

# Parâmetros do broker
BROKER = 'localhost'
PORT = 1883
TOPIC = 'banco/+/events'
CLIENT_ID = f'twin-subscriber-{int(time.time())}'

# Setup de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mqtt-subscriber")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Conectado ao broker MQTT!")
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
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def run_subscriber():
    client = mqtt_client.Client(client_id=CLIENT_ID, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    # Se seu broker tiver autenticação, adicione client.username_pw_set(user, pass)
    client.connect(BROKER, PORT)
    client.loop_forever()

if __name__ == "__main__":
    run_subscriber()