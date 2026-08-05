import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend for Termux
import matplotlib.pyplot as plt

# Domain and Grid Setup
N = 256
L = 2.0 * np.pi
x = np.linspace(0, L, N, endpoint=False)
k = np.fft.fftfreq(N, d=L/(2*np.pi*N))

# Physical Parameters
f_drive = 79.79           # Structural drive frequency (Hz)
omega_0 = 2 * np.pi * f_drive
gamma = 0.05              # Small linear growth (surplus)
delta2 = 1e-4             # Dispersion scale
beta = 1.04               # Dynamic lead modulation

# Initial condition (Gaussian perturbation)
u0 = np.exp(-(x - np.pi)**2 / 0.2)
u_hat = np.fft.fft(u0)

dt = 1e-4
steps = 2000
history = np.zeros((steps, N))

def pde_rhs(u_h, t):
    u = np.fft.ifft(u_h).real
    du_dx = np.fft.ifft(1j * k * u_h).real
    nonlinear = -u * du_dx
    drive = -beta * np.sin(omega_0 * t) * du_dx
    linear_dispersion = (gamma - 1j * delta2 * (k**3)) * u_h
    return np.fft.fft(nonlinear + drive) + linear_dispersion

# Runge-Kutta 4 Integrator
t = 0.0
for i in range(steps):
    history[i, :] = np.fft.ifft(u_hat).real

    k1 = pde_rhs(u_hat, t)
    k2 = pde_rhs(u_hat + 0.5 * dt * k1, t + 0.5 * dt)
    k3 = pde_rhs(u_hat + 0.5 * dt * k2, t + 0.5 * dt)
    k4 = pde_rhs(u_hat + dt * k3, t + dt)

    u_hat += (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    t += dt

# Plot and save image cleanly
plt.figure(figsize=(9, 5))
plt.imshow(history, extent=[0, L, steps*dt, 0], aspect='auto', cmap='magma')
plt.colorbar(label='Field Amplitude u(x,t)')
plt.xlabel('Spatial Coordinate x')
plt.ylabel('Time t (seconds)')
plt.title(f'Forced Dispersive Wave PDE Propagation (f = {f_drive} Hz)')
plt.tight_layout()
plt.savefig('soliton_surface.png')
print("✅ PDE Solved! Surface plot saved to soliton_surface.png")
