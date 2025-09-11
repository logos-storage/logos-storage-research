import numpy as np
import matplotlib.pyplot as plt

# Range of N values
N = np.linspace(1e4, 1e5, 500)

# Maintenance bandwidth formula
bandwidth_maint = 6.67 + 48.2 * np.log2(N)

# Plot
plt.figure(figsize=(8,5))
plt.plot(N, bandwidth_maint, label=r'Maintenance Bandwidth')
plt.xlabel('N (number of DHT nodes)')
plt.ylabel('Maintenance Bandwidth (bytes/sec)')
plt.title('Maintenance Cost For Varying Number of Nodes')
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.show()