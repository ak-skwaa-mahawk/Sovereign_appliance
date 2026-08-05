import asyncio
import math
import random

# FPT Constants
BASE_EPSILON = 0.0417  # ~4.17% baseline surplus

class FPTBiofeedbackProcessor:
    def __init__(self):
        self.rr_intervals = []

    def process_rr_interval(self, hr: int, rr_ms: float):
        """Processes incoming RR-interval data into FPT metrics."""
        self.rr_intervals.append(rr_ms)
        if len(self.rr_intervals) > 30:  # Sliding window of 30 beats
            self.rr_intervals.pop(0)

        self.evaluate_fpt_coherence(hr)

    def evaluate_fpt_coherence(self, hr: int):
        """Calculates RMSSD, FPT Vitality (v), and Dynamic Epsilon (ε_d)."""
        if len(self.rr_intervals) < 2:
            return

        # Compute RMSSD (Root Mean Square of Successive Differences)
        diffs = [
            (self.rr_intervals[i] - self.rr_intervals[i - 1]) ** 2
            for i in range(1, len(self.rr_intervals))
        ]
        rmssd = (sum(diffs) / len(diffs)) ** 0.5

        # Normalize RMSSD into a 0.0 - 2.0 Vitality Proxy (v_hrv)
        v_hrv = min(max(rmssd / 50.0, 0.1), 2.0)

        # Dynamic Surplus Factor Calculation
        epsilon_d = BASE_EPSILON * v_hrv

        print(f"\n[Bio-Jolt] HR: {hr} BPM | RMSSD: {rmssd:.2f} ms")
        print(f" ├─ Vitality Proxy (v): {v_hrv:.4f}")
        print(f" └─ Dynamic Epsilon (ε_d): {epsilon_d * 100:.2f}%")

        # Actuation Trigger Threshold
        if v_hrv < 0.5:
            print(" \x1b[31m[Vhitzee Correction]: Low coherence detected. Initiating pacing actuation...\x1b[0m")
        elif v_hrv >= 1.2:
            print(" \x1b[32m[Psyselsic Uncoil]: High coherence achieved. Transmitting mesh sync token...\x1b[0m")


async def stream_synthetic_biofeedback(processor: FPTBiofeedbackProcessor):
    """Simulates realistic cardiac vagal wave dynamics in Termux."""
    print("\x1b[36m[FPT Engine]: Termux environment detected. Launching biofeedback simulator...\x1b[0m")
    t = 0.0

    for _ in range(20):  # Run 20 iteration steps
        # Simulate vagal respiratory oscillation (0.1 Hz RSA wave)
        base_hr = 68 + 10 * math.sin(2 * math.pi * 0.1 * t)
        
        # Add slight stochastic micro-fluctuations
        jitter = random.uniform(-15.0, 15.0)
        rr_ms = (60.0 / base_hr) * 1000.0 + jitter
        actual_hr = int(60000.0 / rr_ms)

        processor.process_rr_interval(actual_hr, rr_ms)

        t += 0.8
        await asyncio.sleep(0.8)


async def main():
    processor = FPTBiofeedbackProcessor()
    await stream_synthetic_biofeedback(processor)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBiofeedback loop terminated.")
