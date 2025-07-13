import mqtt from 'mqtt';
import { refetchDigitalTwin } from './hooks/useDigitalTwin'; // veja nota abaixo

const client = mqtt.connect('ws://localhost:9001');

client.on('connect', () => {
  client.subscribe('banco/+/events');
});

client.on('message', (topic, message) => {
  // sempre que chegar um evento, pegue novamente o resumo:
  refetchDigitalTwin();
});
