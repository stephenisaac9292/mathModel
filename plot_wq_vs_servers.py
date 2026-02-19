import matplotlib.pyplot as plt

Wq_mean_c1 = 2092.285117
Wq_mean_c2 = 4.811421
Wq_mean_c3 = 0.299868

cs = [1, 2, 3]
Wqs = [Wq_mean_c1, Wq_mean_c2, Wq_mean_c3]

plt.figure(figsize=(8, 5))
plt.plot(cs, Wqs, marker="o", linewidth=2, markersize=8, color="steelblue")

# Annotate each point with its value
for x, y in zip(cs, Wqs):
    plt.annotate(f"{y:.2f}", xy=(x, y), textcoords="offset points",
                 xytext=(0, 12), ha="center", fontsize=10)

plt.yscale("log")  # log scale so all values are visible
plt.xticks(cs, ["c=1", "c=2", "c=3"])
plt.xlabel("Number of servers (c)", fontsize=12)
plt.ylabel("Average waiting time in queue, Wq (log scale)", fontsize=12)
plt.title("Wq vs Number of Servers (M/M/c Queue Simulation)", fontsize=13)
plt.grid(True, which="both", linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("wq_vs_servers.png", dpi=150, bbox_inches="tight")
print("Saved to wq_vs_servers.png")