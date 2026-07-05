"""
Escuta no .64 (receptor) enquanto o sistema envia pelo .16.
Mostra TODOS os pacotes recebidos, incluindo TEXT_MESSAGE.
"""
import meshtastic.tcp_interface
import time, logging
from pubsub import pub

logging.basicConfig(level=logging.WARNING)

def on_receive(packet, interface):
    portnum = packet.get('decoded', {}).get('portnum', 'UNKNOWN')
    priority = packet.get('priority', 'N/A')
    from_id = packet.get('fromId', '?')
    channel = packet.get('channel', '?')
    text = packet.get('decoded', {}).get('text', '')
    raw_payload = packet.get('decoded', {}).get('payload', b'')
    has_bell = b'\x07' in (raw_payload if isinstance(raw_payload, bytes) else b'')
    print(f"[RX] from={from_id} ch={channel} portnum={portnum} priority={priority} bell={has_bell}")
    if text:
        print(f"     text={repr(text[:120])}")

pub.subscribe(on_receive, "meshtastic.receive")

iface = meshtastic.tcp_interface.TCPInterface('192.168.1.64')
time.sleep(4)
print("Escutando no .64. Dispare o standalone pelo .16 agora.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

iface.close()
