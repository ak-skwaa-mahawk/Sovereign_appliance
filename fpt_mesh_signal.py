import socket
import json
import time
import math
import random

# Mesh Configuration
MESH_PORT = 9999
BROADCAST_ADDR = "255.255.255.255"

def create_mesh_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return sock

def generate_signal_payload(t):
    """Generates combined Biofeedback + State payload."""
    base_hr = 68 + 10 * math.sin(2 * math.pi * 0.1 * t)
    jitter = random.uniform(-15.0, 15.0)
    rr_ms = (60.0 / base_hr) * 1000.0 + jitter
    hr = int(60000.0 / rr_ms)
    
    # Dynamic Epsilon & Proxy
    v_hrv = min(max(rr_ms / 1000.0, 0.1), 2.0)
    epsilon_d = 0.0417 * v_hrv

    payload = {
        "timestamp": time.time(),
        "signal_type": "FPT_BIO_MESH_JOLT",
        "metrics": {
            "hr_bpm": hr,
            "rr_ms": round(rr_ms, 2),
            "vitality_v": round(v_hrv, 4),
            "epsilon_d_percent": round(epsilon_d * 100, 2)
        },
        "pqc_status": "LOCKED",
        "unified_key_prefix": "0xa03a15722feb"
    }
    return payload

def main():
    sock = create_mesh_socket()
    print(f"\x1b[36m[Mesh Signal Transmitter Live]\x1b[0m Broadcasting on port {MESH_PORT}...")
    t = 0.0
    
    try:
        for _ in range(15):
            payload = generate_signal_payload(t)
            data_bytes = json.dumps(payload).encode('utf-8')
            
            # Broadcast to local mesh network
            sock.sendto(data_bytes, (BROADCAST_ADDR, MESH_PORT))
            
            print(f" \x1b[32m[Signal Sent]\x1b[0m HR: {payload['metrics']['hr_bpm']} | ε_d: {payload['metrics']['epsilon_d_percent']}% | Payload: {len(data_bytes)} bytes")
            t += 0.8
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("\nMesh signal broadcast stopped.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
