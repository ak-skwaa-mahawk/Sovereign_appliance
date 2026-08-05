import numpy as np
from scipy.fft import fft, ifft, fftfreq
import json
import time

# ==============================================================================
# 1. PARAMETERS & DOMAIN SETUP
# ==============================================================================
L = 40.0                 # Spatial domain length [-L/2, L/2]
Nx = 512                 # Spatial grid points (power of 2 for FFT)
dx = L / Nx
x = np.linspace(-L/2, L/2, Nx, endpoint=False)

# Time Discretization & Drive Frequency
f_drive = 79.79          # Parametric drive frequency (Hz)
omega_0 = 2 * np.pi * f_drive
T_period = 1.0 / f_drive  # ~0.01253 seconds
t_final = 10 * T_period   # Simulate 10 full drive cycles
dt = T_period / 200      # 200 time steps per drive period (resolves 79.79 Hz)
Nt = int(t_final / dt)

# PDE Parameters (Forced-Damped Variant)
gamma = -0.05            # Damping parameter (γ < 0 for dissipation)
delta_sq = 0.01          # Third-order dispersion coefficient (δ²)
beta = 0.15              # Dynamic jolt amplitude (β)

# ==============================================================================
# 2. FOURIER MODES & OPERATORS
# ==============================================================================
k = 2 * np.pi * fftfreq(Nx, d=dx)
ik = 1j * k
ik3 = (1j * k)**3

# Linear Operator: L(k) = γ - δ² * (ik)³
L_op = gamma - delta_sq * ik3

# Integrating Factors for Step dt
exp_L_dt2 = np.exp(L_op * (dt / 2.0))
exp_L_dt  = np.exp(L_op * dt)

# 2/3 De-aliasing Mask (Orszag's Rule)
k_max = np.max(np.abs(k))
dealias_mask = (np.abs(k) <= (2.0 / 3.0) * k_max).astype(float)

# ==============================================================================
# 3. INITIAL CONDITIONS (Sech² Soliton Seed)
# ==============================================================================
c_speed = 4.0
a_amp = c_speed / 2.0
b_scale = np.sqrt(c_speed) / 2.0
u0 = a_amp * (1.0 / np.cosh(b_scale * (x + 5.0)))**2

# ==============================================================================
# 4. NONLINEAR RESIDUAL FUNCTION
# ==============================================================================
def compute_N_hat(u_physical, t_curr):
    u_hat = fft(u_physical)
    du_dx = ifft(ik * u_hat).real
    u_eff = u_physical + beta * np.sin(omega_0 * t_curr)
    N_physical = -u_eff * du_dx
    return fft(N_physical) * dealias_mask

# ==============================================================================
# 5. INTEGRATING FACTOR RK4 SOLVER
# ==============================================================================
print(f"🌀 Initializing Soliton Integration Envelope:")
print(f"   Domain L={L}, Grid Nx={Nx}, Drive f={f_drive} Hz")
print(f"   Parameters: γ={gamma}, δ²={delta_sq}, β={beta}")
print(f"   Time Step dt={dt:.6e}s ({Nt} iterations over {t_final:.4f}s)")
print("-" * 65)

u_curr = u0.copy()
t_curr = 0.0
start_wall_time = time.time()

for step in range(Nt):
    u_hat = fft(u_curr)
    
    # RK4 Stage 1
    N1_hat = compute_N_hat(u_curr, t_curr)
    
    # RK4 Stage 2
    u_stage2_hat = exp_L_dt2 * (u_hat + 0.5 * dt * N1_hat)
    u_stage2 = ifft(u_stage2_hat).real
    N2_hat = compute_N_hat(u_stage2, t_curr + 0.5 * dt)
    
    # RK4 Stage 3
    u_stage3_hat = exp_L_dt2 * u_hat + 0.5 * dt * N2_hat
    u_stage3 = ifft(u_stage3_hat).real
    N3_hat = compute_N_hat(u_stage3, t_curr + 0.5 * dt)
    
    # RK4 Stage 4
    u_stage4_hat = exp_L_dt * u_hat + exp_L_dt2 * (dt * N3_hat)
    u_stage4 = ifft(u_stage4_hat).real
    N4_hat = compute_N_hat(u_stage4, t_curr + dt)
    
    # Reassemble RK4 update
    u_hat_next = exp_L_dt * u_hat + (dt / 6.0) * (
        exp_L_dt * N1_hat + 
        2.0 * exp_L_dt2 * N2_hat + 
        2.0 * exp_L_dt2 * N3_hat + 
        N4_hat
    )
    
    u_curr = ifft(u_hat_next).real
    t_curr += dt

elapsed_wall_time = time.time() - start_wall_time

# ==============================================================================
# 6. POST-PROCESSING & TELEMETRY GENERATION
# ==============================================================================
max_amplitude = float(np.max(np.abs(u_curr)))
min_amplitude = float(np.min(u_curr))
total_energy = float(np.sum(u_curr**2) * dx)

print(f"✅ Integration Completed in {elapsed_wall_time:.3f}s")
print(f"   Final State Peak Amplitude: {max_amplitude:.6f}")
print(f"   Final State Minimum Amplitude: {min_amplitude:.6f}")
print(f"   Total Wavefield Energy E: {total_energy:.6f}")

telemetry_data = {
    "simulation_metadata": {
        "drive_frequency_hz": f_drive,
        "gamma": gamma,
        "delta_sq": delta_sq,
        "beta": beta,
        "grid_size": Nx,
        "simulated_time_s": t_final
    },
    "frames": [
        {
            "type": "soliton_pde_state",
            "timestamp": time.time(),
            "max_amplitude": max_amplitude,
            "min_amplitude": min_amplitude,
            "total_energy": total_energy,
            "wavefield_sample": u_curr[::16].tolist()
        }
    ]
}

with open("mesh_telemetry.json", "w") as f:
    json.dump(telemetry_data, f, indent=2)

print("💾 Inscribed simulation payload to 'mesh_telemetry.json'.")
