import numpy as np
import matplotlib.pyplot as plt

# Parameters
N_values = [1e4, 1e5]

# P buckets (members)
P_buckets = {
    "small (P=10)": 10,
    "mid (P=250)": 250,
    "large (P=1000)": 1000
}

def query_payload_bytes(N, P):
    return 14460.0 * np.log2(N) + 16.0 * (33.0 + 305.0 * P)

# Query rate Q = (P / (7*86400)) * (0.05 + 0.20 / C)
def Q_per_content(C, P):
    W = 7 * 86400.0
    return (P / W) * (0.05 + 0.20 / C)

# Query bandwidth in KB/sec
def BW_query_kb_per_sec(C, P, N):
    Q = Q_per_content(C, P)
    capped_P = min(P, 100)
    # (C * Q * (14460 * np.log2(N) + 528 + 16 * (np.ceil(P/5) * 5 + 300*P))) / (N * 1024)
    return (C * Q * (14460 * np.log2(N) + 528 + 16 * (np.ceil(capped_P/5) * 5 + 300*capped_P))) / (N * 1024)

# Community age (H_weeks) and content counts (C)
H_weeks = np.arange(1, 513)
C_vals = H_weeks + 1

# Plotting 1x2 grid
fig, axs = plt.subplots(1, 2, figsize=(14, 5), sharex=True, sharey=True)
axs = axs.flatten()

for i, N in enumerate(N_values):
    ax = axs[i]
    for label, P in P_buckets.items():
        y = BW_query_kb_per_sec(C_vals, P, N)
        ax.plot(H_weeks, y, label=label, linewidth=2)
    ax.set_xscale("log", base=10)
    ax.set_yscale("log", base=10)
    ax.set_xlabel("Community age H (weeks)")
    ax.set_ylabel("Query Bandwidth (KB/sec)")
    ax.set_title(f"N={int(N):,}")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

plt.tight_layout()
plt.show()