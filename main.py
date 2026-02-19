import math
import numpy as np
import simpy
from scipy.stats import expon, t


# ---------- Theory (lecturer formulas) ----------
def mm1_theory(lmbda, mu):
    if lmbda >= mu:
        raise ValueError("Unstable: need lambda < mu for M/M/1.")
    p = lmbda / mu  # p = rho
    L = p / (1 - p)
    Lq = (p**2) / (1 - p)
    W = 1.0 / (mu - lmbda)
    Wq = p / (mu - lmbda)
    return {"rho": p, "L": L, "Lq": Lq, "W": W, "Wq": Wq}


# ---------- Helpers for mean + 95% CI ----------
def mean_ci(vals, alpha=0.05):
    vals = np.array(vals, dtype=float)
    n = len(vals)
    m = float(vals.mean())
    if n < 2:
        return m, (m, m)
    s = float(vals.std(ddof=1))
    tcrit = float(t.ppf(1 - alpha / 2, df=n - 1))
    half = tcrit * s / math.sqrt(n)
    return m, (m - half, m + half)


# ---------- Time-average tracker for L and Lq ----------
class AreaTracker:
    def __init__(self):
        self.N = 0      # number in system
        self.Nq = 0     # number in queue (waiting, not in service)
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

    # request server
    with server.request() as req:
        yield req
        service_start = env.now

        # if customer had been counted as queued, remove them from queue now
        wait = service_start - arrival
        if wait > 0:
            tracker.update(env.now)
            tracker.Nq -= 1

        # service
        service_time = rng.exponential(1.0 / mu)
        # busy time clipped to [0, Tsim]
        bs = max(0.0, service_start)
        be = min(Tsim, service_start + service_time)
        if be > bs:
            stats["busy_time"] += (be - bs)

        yield env.timeout(service_time)
        depart = env.now

        # only record times if completion happens within Tsim
        if depart <= Tsim:
            stats["waits"].append(wait)                 # Wq samples
            stats["system_times"].append(depart - arrival)  # W samples

    # departure updates N (only when the departure event occurs; env runs to Tsim)
    tracker.update(env.now)
    tracker.N -= 1


# ---------- Arrival process ----------
def arrivals(env, server, lmbda, mu, tracker, stats, rng, Tsim):
    while True:
        ia = rng.exponential(1.0 / lmbda)
        yield env.timeout(ia)
        if env.now > Tsim:
            break

        # arrival updates N
        tracker.update(env.now)
        tracker.N += 1

        # if server is currently busy, this arrival will wait => count into queue
        if server.count >= server.capacity:
            tracker.Nq += 1

        env.process(customer(env, server, mu, tracker, stats, rng, Tsim))


# ---------- One SimPy replication ----------
def simulate_mm1_simpy(lmbda, mu, Tsim, seed):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    server = simpy.Resource(env, capacity=1)

    tracker = AreaTracker()
    stats = {"waits": [], "system_times": [], "busy_time": 0.0}

    env.process(arrivals(env, server, lmbda, mu, tracker, stats, rng, Tsim))
    env.run(until=Tsim)

    # finalize areas up to Tsim
    tracker.update(Tsim)

    # metrics
    rho_sim = stats["busy_time"] / Tsim
    L_sim = tracker.areaN / Tsim
    Lq_sim = tracker.areaNq / Tsim

    # averages from completed customers (by Tsim)
    Wq_sim = float(np.mean(stats["waits"])) if stats["waits"] else float("nan")
    W_sim = float(np.mean(stats["system_times"])) if stats["system_times"] else float("nan")

    return {"rho": rho_sim, "Wq": Wq_sim, "W": W_sim, "Lq": Lq_sim, "L": L_sim}


# ---------- Run 5 reps + print Table 1 & Table 2 ----------
def run_experiment(lmbda=0.9, mu=1.0, Tsim=10000):
    seeds = [235, 284, 893, 895, 394]

    theory = mm1_theory(lmbda, mu)
    print(f"Parameters: lambda={lmbda:.3f}, mu={mu:.3f}, Tsim={Tsim}, replications={len(seeds)}")
    print(f"Seeds: {seeds}\n")

    print("THEORETICAL (M/M/1):")
    for k in ["rho", "W", "Wq", "L", "Lq"]:
        print(f"{k:>3} = {theory[k]:.6f}")
    print()

    runs = []
    print("SIMULATION RUNS:")
    print("Run |   rho_sim |      Wq |       W |      Lq |       L")
    print("-" * 58)
    for i, sd in enumerate(seeds, start=1):
        r = simulate_mm1_simpy(lmbda, mu, Tsim, seed=sd)
        runs.append(r)
        print(f"{i:>3} | {r['rho']:>9.6f} | {r['Wq']:>7.4f} | {r['W']:>7.4f} | {r['Lq']:>7.4f} | {r['L']:>7.4f}")
    print()

    print("SUMMARY (mean ± 95% CI):")
    for k in ["rho", "Wq", "W", "Lq", "L"]:
        vals = [r[k] for r in runs]
        m, (lo, hi) = mean_ci(vals)
        print(f"{k:>3} mean={m:.6f}   95% CI=[{lo:.6f}, {hi:.6f}]")

    return theory, runs


if __name__ == "__main__":
    run_experiment(lmbda=0.9, mu=1.0, Tsim=10000)
