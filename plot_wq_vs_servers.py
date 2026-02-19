import matplotlib.pyplot as plt

# Put the MEAN Wq you got from mm1_sim.py, mm2_sim.py, mm3_sim.py here:
Wq_mean_c1 = 2262.230043 # replace
Wq_mean_c2 = 5.032231  # replace
Wq_mean_c3 = 0.299868  # replace

cs = [1, 2, 3]
Wqs = [Wq_mean_c1, Wq_mean_c2, Wq_mean_c3]

plt.plot(cs, Wqs, marker="o")
plt.xticks(cs)
plt.xlabel("Number of servers (c)")
plt.ylabel("Average waiting time in queue (Wq)")
plt.title("Wq vs Number of Servers")
plt.grid(True)
plt.savefig("wq_vs_servers.png", dpi=150, bbox_inches="tight")
print("Saved to wq_vs_servers.png")