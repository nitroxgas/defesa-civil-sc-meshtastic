"""
Escuta TODOS os pacotes recebidos no nó receptor (192.168.1.16),
mostrando portnum e priority para comparar TEXT_MESSAGE vs ALERT_APP.
Rode este script e depois dispare o standalone no .64 para comparar.
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
    has_bell = '\x07' in text or '\a' in text
    print(f"[RX] from={from_id} ch={channel} portnum={portnum} priority={priority} bell={has_bell}")
    if text:
        print(f"     text={repr(text[:100])}")

pub.subscribe(on_receive, "meshtastic.receive")

iface = meshtastic.tcp_interface.TCPInterface('192.168.1.16')
time.sleep(4)
print(f"Escutando no no receptor 192.168.1.16 (Ctrl+C para parar)...")
print(f"Dispare o standalone no .64 agora.\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

iface.close()
