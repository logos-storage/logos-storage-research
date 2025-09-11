import numpy as np
import matplotlib.pyplot as plt

# parameters
N_values = [1e4, 1e5]
T_values = [30 * 60, 22 * 3600]  # 30 min, 22 hr (seconds)

# Buckets for providers P
P_buckets = {
    "small (P=10)": 10,
    "mid (P=250)": 250,
    "large (P=1000)": 1000,
}

# Community age H (weeks) and content count C = H + 1 (index included)
H_weeks = np.arange(1, 513)
C_vals = H_weeks + 1

# traffic formulas
def maint_bytes_per_sec(N):
    # 6.67 + 48.2*log2(N)
    return 6.67 + 48.2 * np.log2(N)

def advert_payload_bytes(N):
    # (lookup + K*AddProvider) per advertise event
    # 14460*log2(N) + 3744
    return 14460.0 * np.log2(N) + 3744.0

def query_payload_bytes(N, P):
    # (lookup + GetProviders) per query event
    # 14460*log2(N) + 16*(33 + 305*P)
    return 14460.0 * np.log2(N) + 16.0 * (33.0 + 305.0 * P)

def Q_per_content(C, P):
    # Q(C) = (P / (7*86400)) * (0.05 + 0.20 / C)
    W = 7 * 86400.0
    return (P / W) * (0.05 + 0.20 / C)

def total_bw_bytes_per_sec(N, T, C, P):
    """
    Total bandwidth per provider (bytes/sec) as a function of N, T, C, P:
    BW_total = maintenance + advertise + query
    where:
      maintenance = (6.67 + 48.2*log2(N))
      advertise   = (C/T) * [14460*log2(N) + 3744]
      query       = C * Q(C) * [14460*log2(N) + 16*(33 + 305*P)]
    """
    maint = maint_bytes_per_sec(N)
    advert = (C / T) * advert_payload_bytes(N)
    Qc = Q_per_content(C, P)
    query = C * Qc * query_payload_bytes(N, P)
    return maint + advert + query

# Plotting 2x2 grid (N x T), 3 curves per subplot (P buckets)
fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
axs = axs.flatten()
colors = ["C0", "C1", "C2"]

for i, N in enumerate(N_values):
    for j, T in enumerate(T_values):
        ax = axs[i*2 + j]
        for k, (label, P) in enumerate(P_buckets.items()):
            y = total_bw_bytes_per_sec(N, T, C_vals, P)
            ax.plot(H_weeks, y, color=colors[k % len(colors)], lw=2, label=label)
        ax.set_xlabel("Community age H (weeks)")
        ax.set_ylabel("Total Bandwidth (bytes/sec)")
        ax.set_title(f"N={int(N):,}, T={int(T/3600) if T>=3600 else T//60} {'h' if T>=3600 else 'min'}")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log", base=2)
        ax.legend()

plt.tight_layout()
plt.show()