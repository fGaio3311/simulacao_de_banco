import mqtt from 'mqtt';

const host = process.env.REACT_APP_MQTT_WS_URL || 'ws://localhost:9001';
const options = {
  keepalive: 30,
  reconnectPeriod: 1000,
};

const client = mqtt.connect(host, options);

export function subscribe(topic, handler) {
  client.on('connect', () => {
    console.log(`MQTT conectado em ${host}, inscrevendo em ${topic}`);
    client.subscribe(topic);
  });
  client.on('message', (t, payload) => {
    if (mqtt.match(topic, t)) {
      try {
        handler(JSON.parse(payload.toString()));
      } catch (e) {
        console.error('payload inválido', e);
      }
    }
  });
}
