"""
Verifica uplink/downlink de cada canal no gateway .64
e testa envio de TEXT_MESSAGE e ALERT_APP para comparar recepção.
"""
import meshtastic.tcp_interface
import time, logging
logging.basicConfig(level=logging.WARNING)

iface = meshtastic.tcp_interface.TCPInterface('192.168.1.64')
time.sleep(4)

print("=== CANAIS DO GATEWAY .64 ===")
for ch in iface.localNode.channels:
    name = ch.settings.name or '(primary)'
    print(f"  [{ch.index}] role={ch.role} name='{name}' uplink={ch.settings.uplink_enabled} downlink={ch.settings.downlink_enabled}")

print()
print("Enviando TEXT_MESSAGE_APP no canal 2 (deve chegar normalmente)...")
pkt = iface.sendText("TESTE TEXTO - deve chegar", destinationId="^all", channelIndex=2, wantAck=False)
print(f"  portnum={pkt.decoded.portnum} priority={pkt.priority}")

time.sleep(5)

print()
print("Enviando ALERT_APP no canal 2 (teste se chega)...")
pkt2 = iface.sendAlert("TESTE ALERT_APP - deve chegar com alerta \a", channelIndex=2)
print(f"  portnum={pkt2.decoded.portnum} priority={pkt2.priority}")

time.sleep(5)
iface.close()
print("Pronto. Verifique o receptor .16 quais chegaram e com quais portnums.")
