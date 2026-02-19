import numpy as np
import simpy

# ==========================
# PARAMETERS (EDIT HERE)
# ==========================
LAMBDA = 1.8
MU = 1.0
TSIM = 10000                 # assume 10000 since not given
SEEDS = [235, 284, 893, 895, 394]   # 5 runs (change to [235] for 1 run)

SERVER_COST_PER_HR = 50.0
WAIT_COST_PER_HR = 10.0
# ==========================


# ---------- Time-average tracker for N (system) and Nq (queue) ----------
class AreaTracker:
    def __init__(self):
        self.N = 0       # number in system
        self.Nq = 0      # number waiting in queue
        self.last_t = 0.0
        self.areaN = 0.0
        self.areaNq = 0.0

    def update(self, t):
        dt = t - self.last_t
        if dt > 0:
            self.areaN += self.N * dt
            self.areaNq += self.Nq * dt
            self.last_t = t


# ---------- Customer process ----------
def customer(env, server, mu, tracker, stats, rng, Tsim):
    arrival = env.now

    with server.request() as req:
        yield req
        service_start = env.now

        wait = service_start - arrival
        if wait > 0:
            tracker.update(env.now)
            tracker.Nq -= 1

        service_time = rng.exponential(1.0 / mu)

        # accumulate total busy time across ALL servers
        busy_start = max(0.0, service_start)
        busy_end = min(Tsim, service_start + service_time)
        if busy_end > busy_start:
            stats["busy_time_total"] += (busy_end - busy_start)

        yield env.timeout(service_time)

        # record waiting time sample (for average Wq)
        if env.now <= Tsim:
            stats["waits"].append(wait)

    # departure: customer leaves the system
    tracker.update(env.now)
    tracker.N -= 1


# ---------- Arrival process ----------
def arrivals(env, server, lmbda, mu, tracker, stats, rng, Tsim):
    while True:
        inter_arrival = rng.exponential(1.0 / lmbda)
        yield env.timeout(inter_arrival)

        if env.now > Tsim:
            break

        # arrival: customer enters system
        tracker.update(env.now)
        tracker.N += 1

        # if all servers are busy, customer joins queue
        if server.count >= server.capacity:
            tracker.Nq += 1

        env.process(customer(env, server, mu, tracker, stats, rng, Tsim))


# ---------- One simulation run for M/M/c ----------
def simulate_mmc(lmbda, mu, c, Tsim, seed):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    server = simpy.Resource(env, capacity=c)

    tracker = AreaTracker()
    stats = {"waits": [], "busy_time_total": 0.0}

    env.process(arrivals(env, server, lmbda, mu, tracker, stats, rng, Tsim))
    env.run(until=Tsim)

    # finalize areas up to Tsim
    tracker.update(Tsim)

    # metrics you need
    rho = stats["busy_time_total"] / (c * Tsim)            # utilization
    Wq = float(np.mean(stats["waits"])) if stats["waits"] else float("nan")
    Lq = tracker.areaNq / Tsim                             # time-average queue length

    cost_hr = SERVER_COST_PER_HR * c + WAIT_COST_PER_HR * Lq

    return {"rho": rho, "Wq": Wq, "Lq": Lq, "cost_hr": cost_hr}


# ---------- Printing helpers (tables) ----------
def print_server_table(c, runs):
    print(f"\nTABLE: M/M/{c} (Number of servers = {c})")
    print("Run |  Utilization (rho)  |  Avg wait in queue (Wq)  |  Avg # in queue (Lq)  |  Cost per hour")
    print("-" * 92)

    for i, r in enumerate(runs, start=1):
        print(f"{i:>3} | {r['rho']:>18.6f} | {r['Wq']:>23.6f} | {r['Lq']:>20.6f} | ${r['cost_hr']:>11.2f}")

    # averages (means)
    rho_mean = float(np.mean([r["rho"] for r in runs]))
    Wq_mean  = float(np.mean([r["Wq"] for r in runs]))
    Lq_mean  = float(np.mean([r["Lq"] for r in runs]))
    cost_mean = float(np.mean([r["cost_hr"] for r in runs]))

    print("-" * 92)
    print(f"AVG | {rho_mean:>18.6f} | {Wq_mean:>23.6f} | {Lq_mean:>20.6f} | ${cost_mean:>11.2f}")

    return {"rho_mean": rho_mean, "Wq_mean": Wq_mean, "Lq_mean": Lq_mean, "cost_mean": cost_mean}


def print_comparison_table(summaries):
    print("\nFINAL COMPARISON TABLE (Averages only)")
    print("Servers |  Avg utilization (rho)  |  Avg wait in queue (Wq)  |  Avg # in queue (Lq)  |  Avg cost per hour")
    print("-" * 103)

    for c in [1, 2, 3]:
        s = summaries[c]
        print(f"{c:>7} | {s['rho_mean']:>21.6f} | {s['Wq_mean']:>23.6f} | {s['Lq_mean']:>20.6f} | ${s['cost_mean']:>15.2f}")

    # optimal = minimum average cost per hour
    optimal_c = min([1, 2, 3], key=lambda k: summaries[k]["cost_mean"])
    print("-" * 103)
    print(f"Optimal number of servers (lowest average cost per hour): {optimal_c}")


def main():
    print(f"Parameters: lambda={LAMBDA}, mu={MU}, Tsim={TSIM}, runs per system={len(SEEDS)}")
    print(f"Cost model: server cost = ${SERVER_COST_PER_HR}/hr per server, waiting cost = ${WAIT_COST_PER_HR}/hr per waiting customer")

    summaries = {}

    for c in [1, 2, 3]:
        runs = [simulate_mmc(LAMBDA, MU, c, TSIM, seed) for seed in SEEDS]
        summaries[c] = print_server_table(c, runs)

    print_comparison_table(summaries)


if __name__ == "__main__":
    main()
