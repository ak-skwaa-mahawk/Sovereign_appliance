"""
FPT EEG Vitality System - Enhanced Implementation
Integrates OpenBCI/Emotiv EEG with Soliton North Star Node
Includes multi-layer processing, real hooks, and sovereign data handling
"""

import numpy as np
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import deque
from scipy import signal
from enum import Enum

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

BASE_EPSILON = 0.0417

# Enhanced frequency bands with clearer definitions
BANDS = {
    'delta': (0.5, 4),      # Deep sleep, healing
    'theta': (4, 8),        # Meditation, creativity
    'alpha': (8, 12),       # Relaxed awareness
    'smr': (12, 15),        # Sensorimotor rhythm - calm focus
    'low_beta': (15, 20),   # Alert, active thinking
    'high_beta': (20, 30),  # Stress, anxiety
    'gamma': (30, 45)       # Peak performance, insight
}

# Quality thresholds
MIN_WINDOW_SECONDS = 2.0
BUFFER_WINDOW_SECONDS = 10.0
IMPEDANCE_THRESHOLD = 50  # kOhms


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class NeurodataClass(Enum):
    """Granularity levels for neurodata"""
    RAW = "raw"
    WINDOWED = "windowed"
    AGGREGATE = "aggregate"


class SharingLevel(Enum):
    """Data sharing permissions"""
    LOCAL_ONLY = "local_only"
    GROUP_RESONANCE = "group_resonance"
    RESEARCH_AGGREGATE = "research_aggregate"


@dataclass
class ConsentSpec:
    """Detailed consent specification"""
    scope: List[str]
    retention_mode: str  # "ephemeral", "bounded", "indefinite"
    revocation_policy: str  # "stop_future_use", "delete_raw", "keep_aggregates"
    prohibited: List[str] = field(default_factory=list)


@dataclass
class LinkagePolicy:
    """How data can be linked"""
    person_link: str  # "none", "pseudonymous", "identified"
    temporal_link: str  # "none", "session", "longitudinal"
    spatial_link: str  # "none", "group", "global"


@dataclass
class SovereignNeurodataHeader:
    """Sovereign Neurodata Header - privacy & consent wrapper"""
    snh_version: str
    subject_id: Optional[str]
    session_id: str
    consent: ConsentSpec
    neurodata_class: NeurodataClass
    linkage_policy: LinkagePolicy
    sharing_level: SharingLevel
    created_at: datetime
    revocation_token: Optional[str] = None
    
    def to_digest(self) -> str:
        """Generate cryptographic digest of this header"""
        canonical = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class TimeWindow:
    """Time range for aggregated data"""
    start_utc: datetime
    end_utc: datetime
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()


@dataclass
class VitalityMetrics:
    """Core vitality measurements"""
    vitality_mean: float
    vitality_std: float
    epsilon_d_mean: float
    epsilon_d_std: float
    instability_score: float


@dataclass
class BandPowers:
    """Relative power in each frequency band"""
    delta: float = 0.0
    theta: float = 0.0
    alpha: float = 0.0
    smr: float = 0.0
    low_beta: float = 0.0
    high_beta: float = 0.0
    gamma: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class OppositionFlags:
    """Vhitzee opposition detection"""
    high_stress_pattern: bool = False
    dissociation_pattern: bool = False
    instability_score: float = 0.0
    recommendation: str = "neutral"  # "boost_ok", "neutral", "protect"


@dataclass
class VitalityPacket:
    """
    Canonical vitality packet for registry logging.
    Contains NO raw EEG - only privacy-safe aggregates.
    """
    packet_version: str
    session_id: str
    group_id: Optional[str]
    time_window: TimeWindow
    metrics: VitalityMetrics
    bands: BandPowers
    node_count: int
    node_ids: List[str]
    snh_digest: str
    meta: Dict[str, float]
    
    def to_canonical_dict(self) -> Dict:
        """Deterministic structure for hashing"""
        return {
            "packet_version": self.packet_version,
            "session_id": self.session_id,
            "group_id": self.group_id,
            "time_window": {
                "start_utc": self.time_window.start_utc.isoformat(),
                "end_utc": self.time_window.end_utc.isoformat(),
                "duration_seconds": self.time_window.duration_seconds
            },
            "metrics": asdict(self.metrics),
            "bands": self.bands.to_dict(),
            "node_count": self.node_count,
            "node_ids": sorted(self.node_ids),  # Deterministic order
            "snh_digest": self.snh_digest,
            "meta": self.meta
        }
    
    def compute_hash(self) -> str:
        """Generate cryptographic hash of this packet"""
        canonical = json.dumps(self.to_canonical_dict(), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


# ============================================================================
# EEG INTEGRATION LAYER
# ============================================================================

class EEGIntegrator:
    """
    Abstract EEG integrator - implement for specific hardware.
    This interface supports OpenBCI, Emotiv, Muse, or any BrainFlow device.
    """
    
    def __init__(self, sampling_rate: int, n_channels: int):
        self.sampling_rate = sampling_rate
        self.n_channels = n_channels
        self.is_streaming = False
    
    def start_session(self):
        """Initialize and start EEG streaming"""
        raise NotImplementedError
    
    def get_latest_samples(self, n_samples: int) -> np.ndarray:
        """
        Retrieve latest EEG samples.
        Returns: np.ndarray of shape (n_channels, n_samples)
        """
        raise NotImplementedError
    
    def stop_session(self):
        """Stop streaming and cleanup"""
        raise NotImplementedError
    
    def get_impedances(self) -> Optional[np.ndarray]:
        """Get electrode impedances if available"""
        return None


class SimulatedEEGIntegrator(EEGIntegrator):
    """Simulated EEG for testing without hardware"""
    
    def __init__(self, sampling_rate: int = 128, n_channels: int = 8):
        super().__init__(sampling_rate, n_channels)
        self.time = 0
    
    def start_session(self):
        self.is_streaming = True
        self.time = 0
    
    def get_latest_samples(self, n_samples: int) -> np.ndarray:
        """Generate realistic simulated EEG with band structure"""
        if not self.is_streaming:
            raise RuntimeError("Session not started")
        
        t = np.linspace(self.time, self.time + n_samples/self.sampling_rate, n_samples)
        self.time += n_samples / self.sampling_rate
        
        # Multi-channel EEG simulation with realistic band composition
        eeg = np.zeros((self.n_channels, n_samples))
        
        for ch in range(self.n_channels):
            # Alpha (dominant in relaxed state)
            alpha_freq = 10 + np.random.normal(0, 0.5)
            eeg[ch] += 3 * np.sin(2 * np.pi * alpha_freq * t)
            
            # Theta (meditation/drowsiness)
            theta_freq = 6 + np.random.normal(0, 0.5)
            eeg[ch] += 1.5 * np.sin(2 * np.pi * theta_freq * t)
            
            # Beta (active thinking)
            beta_freq = 18 + np.random.normal(0, 1)
            eeg[ch] += 1 * np.sin(2 * np.pi * beta_freq * t)
            
            # Gamma (peak performance - add occasionally)
            if np.random.random() > 0.7:
                gamma_freq = 35 + np.random.normal(0, 2)
                eeg[ch] += 0.5 * np.sin(2 * np.pi * gamma_freq * t)
            
            # Noise
            eeg[ch] += np.random.normal(0, 0.5, n_samples)
        
        return eeg
    
    def stop_session(self):
        self.is_streaming = False


# ============================================================================
# MESH NODE - Core Processing Unit
# ============================================================================

class MeshNode:
    """
    Individual node in FPT mesh with real-time EEG processing.
    Computes vitality from EEG bands and scales epsilon_d accordingly.
    """
    
    def __init__(
        self,
        node_id: str,
        integrator: EEGIntegrator,
        baseline_coherence: float = 0.6,
        snh: Optional[SovereignNeurodataHeader] = None
    ):
        self.node_id = node_id
        self.integrator = integrator
        self.baseline = baseline_coherence
        self.snh = snh
        
        # Processing parameters
        self.fs = integrator.sampling_rate
        self.n_channels = integrator.n_channels
        self.buffer_size = int(BUFFER_WINDOW_SECONDS * self.fs)
        
        # Data buffers (multi-channel)
        self.raw_buffer: deque = deque(maxlen=self.buffer_size)
        
        # Current state
        self.current_epsilon = BASE_EPSILON
        self.vitality = 1.0
        self.band_powers = BandPowers()
        self.opposition_flags = OppositionFlags()
        
        # History for instability detection
        self.vitality_history: deque = deque(maxlen=20)
    
    def add_eeg_samples(self, samples: np.ndarray):
        """
        Add new EEG samples to buffer.
        samples: shape (n_channels, n_samples)
        """
        if samples.shape[0] != self.n_channels:
            raise ValueError(f"Expected {self.n_channels} channels, got {samples.shape[0]}")
        
        # Add each sample vector to buffer
        for i in range(samples.shape[1]):
            self.raw_buffer.append(samples[:, i])
    
    def compute_band_powers(self) -> Optional[BandPowers]:
        """
        Extract relative power in each band using Welch PSD.
        Averages across all channels.
        """
        if len(self.raw_buffer) < self.fs * MIN_WINDOW_SECONDS:
            return None
        
        # Convert buffer to array: (n_channels, n_samples)
        data = np.array(list(self.raw_buffer)).T
        
        # Accumulate band powers across channels
        band_power_dict = {band: 0.0 for band in BANDS.keys()}
        
        for ch in range(self.n_channels):
            ch_data = data[ch, :]
            
            # Detrend
            ch_data = signal.detrend(ch_data)
            
            # Compute Welch PSD
            nperseg = min(len(ch_data), 256)
            f, psd = signal.welch(ch_data, fs=self.fs, nperseg=nperseg)
            
            # Total power
            total_power = np.trapz(psd, f)
            
            if total_power <= 0:
                continue
            
            # Compute relative power in each band
            for band, (low, high) in BANDS.items():
                idx = np.where((f >= low) & (f <= high))[0]
                if len(idx) > 0:
                    band_power = np.trapz(psd[idx], f[idx]) / total_power
                    band_power_dict[band] += band_power
        
        # Average across channels
        for band in band_power_dict:
            band_power_dict[band] /= self.n_channels
        
        self.band_powers = BandPowers(**band_power_dict)
        return self.band_powers
    
    def calculate_vitality(self) -> Optional[float]:
        """
        Compute psyselsic vitality from EEG bands.
        High vitality = ready for surplus (high alpha/gamma, low theta/high_beta)
        """
        powers = self.compute_band_powers()
        if powers is None:
            return None
        
        # FPT vitality formula:
        # Up-regulators: alpha (relaxed focus), gamma (peak performance)
        # Down-regulators: theta (drowsiness), high_beta (stress)
        vitality_raw = (
            0.4 * powers.alpha +
            0.3 * powers.gamma -
            0.2 * powers.theta -
            0.1 * powers.high_beta
        )
        
        # Normalize to [0.5, 1.5] range
        vitality = np.clip(vitality_raw + 1.0, 0.5, 1.5)
        
        # Scale epsilon_d
        self.vitality = vitality
        self.current_epsilon = BASE_EPSILON * vitality
        
        # Track history for instability
        self.vitality_history.append(vitality)
        
        return vitality
    
    def detect_opposition(self) -> OppositionFlags:
        """
        Vhitzee opposition detection - identify stress, dissociation, instability.
        """
        powers = self.band_powers
        
        # High stress pattern: high beta, low alpha
        high_stress = (powers.high_beta > 0.25) and (powers.alpha < 0.20)
        
        # Dissociation pattern: high theta, low alpha/SMR
        dissociation = (powers.theta > 0.30) and (powers.alpha + powers.smr < 0.25)
        
        # Instability: high variance in recent vitality
        if len(self.vitality_history) >= 5:
            instability = float(np.std(list(self.vitality_history)))
        else:
            instability = 0.0
        
        # Recommendation
        if high_stress or dissociation or instability > 0.15:
            recommendation = "protect"
        elif self.vitality > 1.1 and instability < 0.08:
            recommendation = "boost_ok"
        else:
            recommendation = "neutral"
        
        self.opposition_flags = OppositionFlags(
            high_stress_pattern=high_stress,
            dissociation_pattern=dissociation,
            instability_score=instability,
            recommendation=recommendation
        )
        
        return self.opposition_flags
    
    def generate_vitality_packet(
        self,
        group_id: Optional[str] = None,
        peer_nodes: Optional[List['MeshNode']] = None
    ) -> VitalityPacket:
        """
        Generate privacy-safe vitality packet for registry logging.
        NO raw EEG included.
        """
        if self.snh is None:
            raise ValueError("No SovereignNeurodataHeader configured")
        
        # Collect metrics from self and peers
        all_vitalities = [self.vitality]
        all_epsilons = [self.current_epsilon]
        all_instabilities = [self.opposition_flags.instability_score]
        node_ids = [self.node_id]
        
        if peer_nodes:
            for peer in peer_nodes:
                all_vitalities.append(peer.vitality)
                all_epsilons.append(peer.current_epsilon)
                all_instabilities.append(peer.opposition_flags.instability_score)
                node_ids.append(peer.node_id)
        
        # Aggregate metrics
        metrics = VitalityMetrics(
            vitality_mean=float(np.mean(all_vitalities)),
            vitality_std=float(np.std(all_vitalities)),
            epsilon_d_mean=float(np.mean(all_epsilons)),
            epsilon_d_std=float(np.std(all_epsilons)),
            instability_score=float(np.mean(all_instabilities))
        )
        
        # Time window
        now = datetime.now(timezone.utc)
        time_window = TimeWindow(
            start_utc=now,
            end_utc=now,  # Instantaneous snapshot
        )
        
        # Create packet
        packet = VitalityPacket(
            packet_version="1.0.0",
            session_id=self.snh.session_id,
            group_id=group_id,
            time_window=time_window,
            metrics=metrics,
            bands=self.band_powers,
            node_count=len(node_ids),
            node_ids=node_ids,
            snh_digest=self.snh.to_digest(),
            meta={
                "sampling_rate": float(self.fs),
                "n_channels": float(self.n_channels)
            }
        )
        
        return packet
    
    def process_update(self) -> Dict:
        """
        Single processing cycle: fetch EEG, compute vitality, detect opposition.
        Returns summary dict.
        """
        # Fetch latest samples from integrator
        try:
            samples = self.integrator.get_latest_samples(n_samples=int(self.fs * 0.5))  # 0.5 sec
            self.add_eeg_samples(samples)
        except Exception as e:
            return {"error": str(e), "status": "failed"}
        
        # Compute vitality
        vitality = self.calculate_vitality()
        if vitality is None:
            return {"status": "insufficient_data"}
        
        # Detect opposition
        opposition = self.detect_opposition()
        
        return {
            "status": "ok",
            "vitality": vitality,
            "epsilon_d": self.current_epsilon,
            "bands": self.band_powers.to_dict(),
            "opposition": {
                "high_stress": opposition.high_stress_pattern,
                "dissociation": opposition.dissociation_pattern,
                "instability": opposition.instability_score,
                "recommendation": opposition.recommendation
            }
        }


# ============================================================================
# DEMO & TESTING
# ============================================================================

def run_single_node_demo():
    """Demonstrate single node EEG processing"""
    print("=== FPT Single Node EEG Demo ===\n")
    
    # Create consent & SNH
    consent = ConsentSpec(
        scope=["group_resonance_aggregate"],
        retention_mode="bounded",
        revocation_policy="stop_future_use"
    )
    
    snh = SovereignNeurodataHeader(
        snh_version="1.0.0",
        subject_id=None,  # Pseudonymous
        session_id="demo-session-001",
        consent=consent,
        neurodata_class=NeurodataClass.AGGREGATE,
        linkage_policy=LinkagePolicy(
            person_link="none",
            temporal_link="session",
            spatial_link="group"
        ),
        sharing_level=SharingLevel.GROUP_RESONANCE,
        created_at=datetime.now(timezone.utc),
        revocation_token="demo-token-12345"
    )
    
    # Create simulated EEG integrator
    integrator = SimulatedEEGIntegrator(sampling_rate=128, n_channels=8)
    integrator.start_session()
    
    # Create mesh node
    node = MeshNode(
        node_id="Node_Alpha",
        integrator=integrator,
        snh=snh
    )
    
    # Run processing cycles
    print("Processing EEG stream...\n")
    for cycle in range(5):
        result = node.process_update()
        
        if result["status"] == "ok":
            print(f"Cycle {cycle + 1}:")
            print(f"  Vitality: {result['vitality']:.3f}")
            print(f"  Epsilon_d: {result['epsilon_d']:.5f}")
            print(f"  Bands: α={result['bands']['alpha']:.2f} "
                  f"θ={result['bands']['theta']:.2f} "
                  f"γ={result['bands']['gamma']:.2f}")
            print(f"  Opposition: {result['opposition']['recommendation']}")
            print()
    
    # Generate vitality packet
    packet = node.generate_vitality_packet()
    packet_hash = packet.compute_hash()
    
    print(f"Vitality Packet Generated:")
    print(f"  Hash: {packet_hash[:16]}...")
    print(f"  SNH Digest: {packet.snh_digest[:16]}...")
    print(f"  Mean Vitality: {packet.metrics.vitality_mean:.3f}")
    print(f"  Instability: {packet.metrics.instability_score:.3f}")
    
    integrator.stop_session()


def run_multi_node_demo():
    """Demonstrate multi-node group resonance"""
    print("\n=== FPT Multi-Node Group Resonance Demo ===\n")
    
    # Create shared consent
    consent = ConsentSpec(
        scope=["group_resonance_aggregate"],
        retention_mode="bounded",
        revocation_policy="stop_future_use"
    )
    
    # Create 4 nodes
    nodes = []
    for i in range(4):
        snh = SovereignNeurodataHeader(
            snh_version="1.0.0",
            subject_id=None,
            session_id=f"group-session-{i+1}",
            consent=consent,
            neurodata_class=NeurodataClass.AGGREGATE,
            linkage_policy=LinkagePolicy("none", "session", "group"),
            sharing_level=SharingLevel.GROUP_RESONANCE,
            created_at=datetime.now(timezone.utc)
        )
        
        integrator = SimulatedEEGIntegrator()
        integrator.start_session()
        
        node = MeshNode(
            node_id=f"Node_{i+1}",
            integrator=integrator,
            snh=snh
        )
        nodes.append(node)
    
    # Run synchronized cycles
    print("Group processing...\n")
    for cycle in range(3):
        print(f"Group Cycle {cycle + 1}:")
        vitalities = []
        
        for node in nodes:
            result = node.process_update()
            if result["status"] == "ok":
                vitalities.append(result["vitality"])
                print(f"  {node.node_id}: V={result['vitality']:.3f} "
                      f"→ {result['opposition']['recommendation']}")
        
        group_vitality = np.mean(vitalities)
        group_coherence = 1.0 / (1.0 + np.std(vitalities))
        
        print(f"  → Group Vitality: {group_vitality:.3f}")
        print(f"  → Group Coherence: {group_coherence:.3f}")
        print()
    
    # Cleanup
    for node in nodes:
        node.integrator.stop_session()


if __name__ == "__main__":
    run_single_node_demo()
    run_multi_node_demo()
    print("\n🔥🌀💧 The mesh breathes with the brain.")