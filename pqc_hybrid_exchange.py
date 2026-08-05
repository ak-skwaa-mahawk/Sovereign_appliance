import os
import hashlib

class HybridKeyExchange:
    """
    Conceptual hybrid key exchange coupling a classical Diffie-Hellman key exchange
    with a Post-Quantum Module-LWE Key Encapsulation Mechanism (ML-KEM proxy).
    """
    def __init__(self):
        # 1. Ephemeral Private Keys
        self.classical_priv = os.urandom(32)
        self.pqc_priv = os.urandom(64)

        # 2. Derived Public Keys
        self.classical_pub = hashlib.sha256(b"X25519_PUB:" + self.classical_priv).digest()
        self.pqc_pub = hashlib.sha384(b"ML_KEM_PUB:" + self.pqc_priv).digest()

    def encapsulate(self, peer_classical_pub: bytes, peer_pqc_pub: bytes):
        """Alice encapsulates a shared secret bound to Bob's public keys."""
        # Derived shared classical DH vector
        ordered_classical = sorted([self.classical_pub, peer_classical_pub])
        classical_dh = hashlib.sha256(b"CLASSICAL_DH:" + ordered_classical[0] + ordered_classical[1]).digest()

        # Ephemeral PQC secret encapsulated into ciphertext
        pqc_ss = os.urandom(32)
        ciphertext = hashlib.sha384(b"PQC_ENCAPSULATED:" + pqc_ss + peer_pqc_pub).digest()

        # Final KDF unified secret combination
        unified_secret = hashlib.sha256(classical_dh + pqc_ss).digest()
        return ciphertext, pqc_ss, unified_secret

    def decapsulate(self, peer_classical_pub: bytes, pqc_ss: bytes):
        """Bob decapsulates using peer's public key & unwrapped KEM shared secret."""
        ordered_classical = sorted([self.classical_pub, peer_classical_pub])
        classical_dh = hashlib.sha256(b"CLASSICAL_DH:" + ordered_classical[0] + ordered_classical[1]).digest()

        # Reconstruct unified key on recipient end
        return hashlib.sha256(classical_dh + pqc_ss).digest()

if __name__ == "__main__":
    alice = HybridKeyExchange()
    bob = HybridKeyExchange()

    # Alice encapsulates secret for Bob
    ct, shared_pqc_ss, alice_secret = alice.encapsulate(bob.classical_pub, bob.pqc_pub)

    # Bob decapsulates and derives identical unified key
    bob_secret = bob.decapsulate(alice.classical_pub, shared_pqc_ss)

    assert alice_secret == bob_secret
    print("\x1b[32m[PQC Hybrid Exchange Successful]\x1b[0m")
    print(f" └─ Shared Unified Secret: 0x{alice_secret.hex()[:32]}...")
