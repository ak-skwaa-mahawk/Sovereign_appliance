import socket
import json
import time

MESH_PORT = 9999

def start_mesh_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", MESH_PORT))

    last_seq = -1
    total_received = 0
    dropped_packets = 0

    print(f"\x1b[36m[S21 Mesh Node v2 Live]\x1b[0m Listening on UDP :{MESH_PORT} (Unicast/Broadcast)...")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            timestamp = time.strftime("%H:%M:%S")
            payload = json.loads(data.decode('utf-8', errors='replace'))

            metrics = payload.get("metrics", {})
            seq = payload.get("seq", 0)
            hr = metrics.get("hr_bpm")
            epsilon = metrics.get("epsilon_d_percent")
            key_prefix = payload.get("unified_key_prefix")

            # Detect sequence gaps caused by Wi-Fi packet drops
            if last_seq != -1 and seq > last_seq + 1:
                gap = seq - last_seq - 1
                dropped_packets += gap
                print(f" \x1b[31m[Frame Gap Detected]\x1b[0m Missed {gap} packet(s) between seq {last_seq} and {seq}")

            last_seq = seq
            total_received += 1

            print(f" [{timestamp}] \x1b[32m[Jolt #{seq} from {addr[0]}]\x1b[0m HR: {hr} BPM | ε_d: {epsilon}% | Key: {key_prefix}")

    except KeyboardInterrupt:
        print(f"\nReceiver stopped. Total Received: {total_received} | Total Dropped: {dropped_packets}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_mesh_listener()
