import math

output_file = "tables.md"

N_values = [1e4, 1e5]
T_values = [30*60, 22*3600]  # 30 min, 22hr
P_buckets = {
    "small (P=10)": 10,
    "mid (P=250)": 250,
    "large (P=1000)": 1000,
}
H_samples = [26, 52, 104, 208, 416]   # some random weeks

# formulas
def maint_bytes_per_sec(N):
    # 6.67 + 48.2 * log2(N)
    return 6.67 + 48.2 * math.log2(N)

def advert_payload_bytes(N):
    # (lookup + K*AddProvider) per advertise event: 14460*log2(N) + 3744
    return 14460.0 * math.log2(N) + 3744.0

def query_payload_bytes(N, p_msg):
    # (lookup + GetProviders) per query event: 14460*log2(N) + 16*(33 + 305*p_msg)
    return 14460.0 * math.log2(N) + 16.0 * (33.0 + 305.0 * p_msg)

def Q_per_content(C, P):
    # Q(C) = (P / (7*86400)) * (0.05 + 0.20 / C)
    W = 7 * 86400.0
    return (P / W) * (0.05 + 0.20 / C)


def fmt(x):
    # format bytes/sec in a nicer way
    if x == 0: return "0"
    if x >= 1e9:  return f"{x/1e9:.3f}e9"
    if x >= 1e6:  return f"{x/1e6:.3f}e6"
    if x >= 1e3:  return f"{x/1e3:.3f}e3"
    return f"{x:.3f}"

# Compute and collect tables in markdown

lines = []

for N in N_values:
    for T in T_values:
        lines.append(f"\n### N = {int(N):,}, T = {int(T/3600) if T>=3600 else T//60} {'h' if T>=3600 else 'min'}\n")
        for bucket, P in P_buckets.items():
            lines.append(f"\n**{bucket}**\n")
            lines.append("| H (weeks) | C (=H+1) | Total (B/s) | Maint % | Adv % | Query % |\n")
            lines.append("|---:|---:|---:|---:|---:|---:|\n")
            M = maint_bytes_per_sec(N)  # constant over H in a given (N)
            Adv_payload = advert_payload_bytes(N)
            for H in H_samples:
                C = H + 1
                # traffic categories:
                maint = M
                advert = (C / T) * Adv_payload
                Qc = Q_per_content(C, P)
                query = C * Qc * query_payload_bytes(N, p_msg=P)
                total = maint + advert + query
                # percentages:
                maint_pct = (maint / total) * 100.0 if total > 0 else 0.0
                advert_pct = (advert / total) * 100.0 if total > 0 else 0.0
                query_pct = (query / total) * 100.0 if total > 0 else 0.0
                lines.append(f"| {H:>3d} | {C:>3d} | {fmt(total)} | {maint_pct:6.2f}% | {advert_pct:6.2f}% | {query_pct:6.2f}% |\n")

with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Wrote {output_file}")