import numpy as np
import matplotlib.pyplot as plt

# Range of N values
N = np.linspace(1e4, 1e5, 500)

# Maintenance bandwidth per second (bytes/s)
bandwidth_per_sec = 6.67 + 48.2 * np.log2(N)

# Convert to KB per day
bandwidth_per_day_KB = bandwidth_per_sec * 86400 / 1e3

# Plot
plt.figure(figsize=(8,5))
plt.plot(N, bandwidth_per_day_KB, color='navy', label=r'Maintenance Bandwidth (KB/day)')
plt.xlabel('N (number of DHT nodes)')
plt.ylabel('Maintenance Bandwidth (KB/day)')
plt.title('Maintenance Cost For Varying Number of Nodes (per day, KB)')
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.show()