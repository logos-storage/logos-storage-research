import numpy as np
import matplotlib.pyplot as plt

# N values
N_values = [1e4, 1e5]
# T values in seconds: 30min and 22hr
T_values = [30*60, 22*60*60] 
T_labels = ["T = 30 min", "T = 22 hr"]

# Age range in weeks (H), and content per community C = H + 1 (index included)
H_weeks = np.arange(1, 513)  # approx 10 years
C_com = H_weeks + 1

# advertise formula:
# Adv_bandwidth_per_provider = (C/T) * (14460 * log2(N) + 3744)  [bytes/sec]
def adv_bandwidth_kb_per_sec(C, N, T):
    return (C / T) * (14460 * np.log2(N) + 3744) / 1024

# plot
fig, ax = plt.subplots(figsize=(10, 6))

curve_labels = [
    "N = 10,000, T = 30 min",
    "N = 10,000, T = 22 hr",
    "N = 100,000, T = 30 min",
    "N = 100,000, T = 22 hr"
]
colors = ["C0", "C1", "C2", "C3"]

for idx, (N, N_label) in enumerate(zip(N_values, [r"N = 10,000", r"N = 100,000"])):
    for j, (T, T_lab) in enumerate(zip(T_values, T_labels)):
        label = f"{N_label}, {T_lab}"
        y = adv_bandwidth_kb_per_sec(C_com, N, T)
        ax.plot(H_weeks, y, lw=2, label=label, color=colors[idx*2 + j])

ax.set_xlabel("Community age H (weeks)")
ax.set_ylabel("Advertise Bandwidth (KB/sec)")
ax.set_title("Advertise Bandwidth vs Community Age (per provider/member)", fontsize=14)
ax.grid(True, linestyle="--", alpha=0.5)
ax.legend()
ax.set_yscale("log", base=10)
ax.set_xscale("log", base=10)
fig.tight_layout()
plt.show()