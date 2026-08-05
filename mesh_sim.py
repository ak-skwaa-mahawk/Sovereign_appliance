import random
import time
import uuid
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Channel Physics Configuration Matrix
CHANNEL_SPECS = {
    'THz_Beam':        {'base_latency_ms': 5,   'bandwidth_mbps': 100.0},
    'Quantum_Optical': {'base_latency_ms': 12,  'bandwidth_mbps': 50.0},
    'Cognitive_UHF':   {'base_latency_ms': 35,  'bandwidth_mbps': 10.0},
    'LoRa_SubGHz':     {'base_latency_ms': 120, 'bandwidth_mbps': 0.25},
    'AM_Groundwave':   {'base_latency_ms': 250, 'bandwidth_mbps': 0.05}
}


class EnvironmentEngine:
    """Simulates dynamic real-world weather and spectrum interference."""
    def __init__(self):
        self.conditions = {
            'DENSE_FOG': False,      # Disrupts Li-Fi & Optical
            'SOLAR_FLARE': False,    # Disrupts AM Groundwave & Satellite
            'URBAN_JAMMING': False   # Disrupts static UHF / LoRa
        }

    def update_weather(self):
        self.conditions['DENSE_FOG'] = random.random() < 0.25
        self.conditions['SOLAR_FLARE'] = random.random() < 0.15
        self.conditions['URBAN_JAMMING'] = random.random() < 0.20


class AdvancedMeshNode:
    def __init__(self, node_id, supported_interfaces):
        self.node_id = node_id
        self.supported_interfaces = supported_interfaces 
        self.connected_nodes = []
        self.seen_messages = set()
        
        # DePIN Reputation Metrics
        self.reputation_score = 100.0
        self.successful_relays = 0
        self.failed_relays = 0

        # Cryptographic Keypair Generation (Ed25519)
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self._private_key.public_key()

    def connect(self, other_node):
        if other_node not in self.connected_nodes:
            self.connected_nodes.append(other_node)
            other_node.connect(self)

    def apply_reputation_decay(self):
        decay_factor = 0.2
        self.reputation_score = max(10.0, self.reputation_score - decay_factor)

    def sign_payload(self, payload_bytes):
        """Asymmetric signature generation using Ed25519 private key."""
        return self._private_key.sign(payload_bytes)

    def _verify_signature(self, sender_public_key, payload_bytes, signature_bytes):
        """Cryptographic signature verification using sender's Ed25519 public key."""
        try:
            sender_public_key.verify(signature_bytes, payload_bytes)
            return True
        except InvalidSignature:
            return False

    def _cognitive_channel_selector(self, neighbor, env):
        shared_interfaces = list(set(self.supported_interfaces) & set(neighbor.supported_interfaces))
        if not shared_interfaces:
            return None, 0.0

        best_channel = None
        best_reliability = 0.0

        for channel in shared_interfaces:
            if channel == 'Quantum_Optical':
                reliability = 0.15 if env.conditions['DENSE_FOG'] else 0.98
            elif channel == 'THz_Beam':
                reliability = 0.30 if env.conditions['DENSE_FOG'] else 0.88
            elif channel == 'Cognitive_UHF':
                reliability = 0.50 if env.conditions['URBAN_JAMMING'] else 0.92
            elif channel == 'AM_Groundwave':
                reliability = 0.20 if env.conditions['SOLAR_FLARE'] else 0.90
            elif channel == 'LoRa_SubGHz':
                reliability = 0.85
            else:
                reliability = 0.70

            if reliability > best_reliability:
                best_reliability = reliability
                best_channel = channel

        return best_channel, best_reliability

    def _calculate_hop_latency(self, channel, payload_size_bytes):
        """Calculates latency in milliseconds based on payload size and physical bandwidth."""
        specs = CHANNEL_SPECS.get(channel, {'base_latency_ms': 50, 'bandwidth_mbps': 1.0})
        # Serialization delay (ms) = (size_bits / bandwidth_bps) * 1000
        bandwidth_bps = specs['bandwidth_mbps'] * 1_000_000
        serialization_delay_ms = ((payload_size_bytes * 8) / bandwidth_bps) * 1000
        # Add random jitter (+/- 10%)
        jitter = random.uniform(0.9, 1.1)
        return (specs['base_latency_ms'] + serialization_delay_ms) * jitter

    def receive_and_relay(self, message_id, payload_bytes, signature, sender, env, telemetry_log, total_latency_ms=0.0, ttl=5):
        if ttl <= 0 or message_id in self.seen_messages:
            return

        self.seen_messages.add(message_id)
        payload_size_bytes = len(payload_bytes)

        # 1. Cryptographic Authentication
        if sender:
            if not self._verify_signature(sender.public_key, payload_bytes, signature):
                log_entry = f"[SECURITY REJECTION] Node {self.node_id}: Invalid Ed25519 signature from Node {sender.node_id}!"
                print(log_entry)
                telemetry_log.append(log_entry)
                return
            sender.reputation_score += 1.5
            sender.successful_relays += 1

        sender_id = sender.node_id if sender else "ORIGIN"
        log_entry = f"  ├─► [RECEPTION] Node {self.node_id:<7} (via {sender_id:<6}) | Size: {payload_size_bytes}B | Latency: {total_latency_ms:.1f}ms | Rep: {self.reputation_score:.1f}"
        print(log_entry)
        telemetry_log.append(log_entry)

        # Re-sign the payload with this node's private key before forwarding
        forward_signature = self.sign_payload(payload_bytes)
        
        # 2. Downstream Relay Loop
        for neighbor in self.connected_nodes:
            if neighbor != sender:
                channel, reliability = self._cognitive_channel_selector(neighbor, env)
                
                if channel and random.random() < reliability:
                    hop_latency = self._calculate_hop_latency(channel, payload_size_bytes)
                    next_total_latency = total_latency_ms + hop_latency
                    
                    link_log = f"  │    ├──[AI LINK] {self.node_id} ──({channel} | +{hop_latency:.1f}ms)──> {neighbor.node_id}"
                    print(link_log)
                    telemetry_log.append(link_log)
                    
                    neighbor.receive_and_relay(
                        message_id, payload_bytes, forward_signature, self, env, telemetry_log,
                        total_latency_ms=next_total_latency, ttl=ttl-1
                    )
                else:
                    reason = "No shared interface" if not channel else f"Attenuated by weather ({channel})"
                    fail_log = f"  │    └──[LINK FAIL] {self.node_id} -x- {neighbor.node_id} [{reason}]"
                    print(fail_log)
                    telemetry_log.append(fail_log)
                    self.failed_relays += 1


def render_network_graph(nodes):
    print("\n" + "="*70)
    print("           NETWORK TOPOLOGY & REPUTATION MATRIX            ")
    print("="*70)
    for n in nodes:
        connections = ", ".join([cn.node_id for cn in n.connected_nodes])
        interfaces = "/".join(n.supported_interfaces)
        print(f"Node {n.node_id:<6} [{interfaces}]")
        print(f"  ├── Status: Rep = {n.reputation_score:.1f} | Success Relays: {n.successful_relays} | Fails: {n.failed_relays}")
        print(f"  └── Links : {connections}")
        print("-" * 70)


if __name__ == "__main__":
    env = EnvironmentEngine()

    nodes = {
        'Alpha':   AdvancedMeshNode("Alpha",   ['Cognitive_UHF', 'THz_Beam']),
        'Beta':    AdvancedMeshNode("Beta",    ['Cognitive_UHF', 'AM_Groundwave', 'LoRa_SubGHz']),
        'Gamma':   AdvancedMeshNode("Gamma",   ['AM_Groundwave', 'Quantum_Optical']),
        'Delta':   AdvancedMeshNode("Delta",   ['Quantum_Optical', 'THz_Beam']),
        'Echo':    AdvancedMeshNode("Echo",    ['LoRa_SubGHz', 'AM_Groundwave']),
        'Foxtrot': AdvancedMeshNode("Foxtrot", ['Cognitive_UHF', 'Quantum_Optical', 'THz_Beam']),
        'Golf':    AdvancedMeshNode("Golf",    ['THz_Beam', 'LoRa_SubGHz']),
        'Hotel':   AdvancedMeshNode("Hotel",   ['AM_Groundwave', 'Cognitive_UHF', 'LoRa_SubGHz'])
    }

    nodes['Alpha'].connect(nodes['Beta'])
    nodes['Alpha'].connect(nodes['Delta'])
    nodes['Beta'].connect(nodes['Echo'])
    nodes['Beta'].connect(nodes['Gamma'])
    nodes['Gamma'].connect(nodes['Delta'])
    nodes['Delta'].connect(nodes['Foxtrot'])
    nodes['Echo'].connect(nodes['Hotel'])
    nodes['Foxtrot'].connect(nodes['Golf'])
    nodes['Golf'].connect(nodes['Hotel'])

    simulation_export = {
        "timestamp": time.time(),
        "cycles": []
    }

    for cycle in range(1, 6):
        env.update_weather()
        print(f"\n===========================================================")
        print(f"   CYCLE {cycle} | ENVIRONMENT STATE: Fog={env.conditions['DENSE_FOG']} | Flare={env.conditions['SOLAR_FLARE']} | Jamming={env.conditions['URBAN_JAMMING']}")
        print(f"===========================================================")

        for n in nodes.values():
            n.apply_reputation_decay()

        # Construct realistic payload with dynamic size (bytes)
        payload_dict = {
            "version": f"{cycle}.0",
            "telemetry_frame": str(uuid.uuid4()),
            "timestamp": time.time(),
            "data_buffer": "x" * random.randint(128, 1024)  # Variable payload size
        }
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        msg_id = str(uuid.uuid4())[:8]

        # Origin Node Alpha signs payload using Ed25519 private key
        origin_signature = nodes['Alpha'].sign_payload(payload_bytes)

        cycle_log = []
        print(f"[BROADCAST INITIATED] Alpha sending {len(payload_bytes)}B packet (ID: {msg_id}) [Ed25519 Signed]")
        nodes['Alpha'].receive_and_relay(
            msg_id, payload_bytes, origin_signature, sender=None,
            env=env, telemetry_log=cycle_log, total_latency_ms=0.0, ttl=6
        )

        simulation_export["cycles"].append({
            "cycle": cycle,
            "environment": env.conditions.copy(),
            "message": {
                "message_id": msg_id,
                "payload_bytes": len(payload_bytes)
            },
            "events": cycle_log
        })

        time.sleep(1)

    render_network_graph(list(nodes.values()))

    simulation_export["final_node_matrix"] = {
        node_id: {
            "reputation": round(node.reputation_score, 2),
            "successful_relays": node.successful_relays,
            "failed_relays": node.failed_relays,
            "supported_interfaces": node.supported_interfaces,
            "connected_neighbors": [cn.node_id for cn in node.connected_nodes]
        }
        for node_id, node in nodes.items()
    }

    output_filename = "mesh_telemetry.json"
    with open(output_filename, "w") as f:
        json.dump(simulation_export, f, indent=2)

    print(f"\n [EXPORTERS]: Simulation telemetry exported to '{output_filename}'")
