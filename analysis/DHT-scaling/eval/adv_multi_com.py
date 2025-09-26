import numpy as np
import matplotlib.pyplot as plt

# Parameters 
N_list = [1e4, 1e5]       # DHT nodes
T_list = [30*60, 22*60*60]  # advertise intervals: 30 minutes, 22 hours
weeks = np.arange(1, 513)  # global time approx 10 years
M_list = [1, 3, 10, 30]  # number of communities per provider


# Constants for adv formula
K_LOOKUP = 14460         # multiplier for log2(N)
K_CONST  = 3744          # constant term
def adv_bw(C_all, N, T):
    return (C_all / T) * (K_LOOKUP * np.log2(N) + K_CONST)  # bytes/sec

# Compute and plot
fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
colors = ["C0", "C1", "C2", "C3", "C4", "C5"]

for i, N in enumerate(N_list):
    for j, T in enumerate(T_list):
        ax = axs[i, j]
        for k, M in enumerate(M_list):
            per_comm = weeks + 1
            C_all = M * per_comm
            y = adv_bw(C_all, N, T) / 1e3  # convert bytes/sec to KB/sec
            label = f"M={M} communities"
            ax.plot(weeks, y, lw=2, color=colors[k % len(colors)], label=label)

        ax.set_title(f"N={int(N):,}, T={int(T/3600) if T>=3600 else T//60} {'h' if T>=3600 else 'min'}")
        ax.set_xlabel("Global time t (weeks)")
        ax.set_ylabel("Advertise Bandwidth (KB/sec)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        ax.set_yscale("log", base=10)
        ax.set_xscale("log", base=10)
plt.suptitle("Advertise Bandwidth vs Time (per provider) for various (N, T)")
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()