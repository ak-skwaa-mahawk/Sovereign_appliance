import socket
import json

MESH_PORT = 9999

def start_mesh_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to all interfaces to catch subnet broadcasts from the primary node
    sock.bind(("", MESH_PORT))
    
    print("\x1b[36m[S21 Mesh Node Active]\x1b[0m Listening for primary node waves on port 9999...")
    
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            payload = json.loads(data.decode('utf-8', errors='replace'))
            
            metrics = payload.get("metrics", {})
            hr = metrics.get("hr_bpm")
            epsilon = metrics.get("epsilon_d_percent")
            key_prefix = payload.get("unified_key_prefix")
            
            print(f" \x1b[32m[Jolt Intercepted from {addr[0]}]\x1b[0m HR: {hr} BPM | ε_d: {epsilon}% | PQC Key: {key_prefix}")
            
    except KeyboardInterrupt:
        print("\nS21 Mesh Listener stopped.")
    finally:
        sock.close()

if __name__ == "__main__":
    start_mesh_listener()
