import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

NUM_VARS = 6
NUM_CELLS = 18924


residual = np.loadtxt("./solver_data/time_dynamics2.csv")
residual = np.absolute(residual)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
for i in range(0, residual.shape[1], 2):
    ax1.semilogy(residual[:, i], label=f'Mode {i//2+1}')

ax1.set_xlabel("iterations")
ax1.set_ylabel("error norm")
ax1.set_title("convergence prediction of DMD modes")
ax1.grid(True, alpha=0.25, linestyle='--')
ax1.legend(loc='lower left')


theta = np.linspace(0, 2 * np.pi, 100)  # 100 points evenly spaced from 0 to 2*pi
x = np.cos(theta)
y = np.sin(theta)
plt.plot(x, y, c='gray')

amps = np.loadtxt("solver_data/amps.csv", dtype=complex)
amp_real = amps.real
amp_img = amps.imag
for i in range(0, amp_img.shape[0], 2):
    ax2.scatter(x=amp_real[i:i+2], y=amp_img[i:i+2], label=f'Mode {i//2+1}')

ax2.axis('equal')
ax2.set_xlabel('Real')
ax2.set_ylabel("imag")
ax2.grid(True, alpha=0.25, linestyle='--')
ax2.set_title("Amplification factors of dominant DMD modes")
ax2.legend(loc='lower left')

plt.tight_layout()
plt.savefig('results/dmd time-dynamics predicted.png', dpi=300)
