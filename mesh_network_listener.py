import meshtastic.tcp_interface
import sys

# The standard hardcoded IP address of a Meshtastic module running in AP mode
target_ip = "192.168.42.1"  

print(f"📡 Establishing direct link to off-grid radio AP target: {target_ip}...")
try:
    # Latch a raw socket onto the open network interface
    interface = meshtastic.tcp_interface.TCPInterface(hostname=target_ip)
    
    my_info = interface.getNodes()
    print("\n🔒 Off-Grid Mesh Network Topology Decoded Successfully:")
    print(my_info)
    
    interface.close()
except Exception as e:
    print(f"❌ Connection anomaly: {e}")
