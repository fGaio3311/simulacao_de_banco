import time, json
import paho.mqtt.client as mqtt

# Subscriber
def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload.decode()}")

sub = mqtt.Client()
sub.on_message = on_message
sub.connect("localhost",1883)
sub.subscribe("banco/+/events", qos=1)
sub.loop_start()

# Publisher
pub = mqtt.Client()
pub.connect("localhost",1883)
event = {"user":"test","action":"ping","timestamp":"2025-07-09T16:30:00"}
time.sleep(1)
pub.publish("banco/test/events", json.dumps(event), qos=1)

time.sleep(2)
sub.loop_stop()
