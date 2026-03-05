import simpy
import random

SIM_TIME = 8 * 60 * 60
ARRIVAL_MEAN = 100
SERVICE_MEAN = 270
SERVICE_STD = 60
QUEUE_LIMIT = 20

def customer(env, service, stats):
    if len(service.queue) >= QUEUE_LIMIT:
        stats["rejected"] += 1
        return

    with service.request() as request:
        yield request
        stats["served"] += 1
        service_time = max(0, random.normalvariate(SERVICE_MEAN, SERVICE_STD))
        yield env.timeout(service_time)

def arrival(env, service, stats):
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_MEAN))
        stats["total"] += 1
        env.process(customer(env, service, stats))

def simulate(n_agents):
    env = simpy.Environment()
    service = simpy.Resource(env, capacity=n_agents)
    stats = {"total": 0, "served": 0, "rejected": 0}

    env.process(arrival(env, service, stats))
    env.run(until=SIM_TIME)

    return stats["rejected"] / stats["total"]

if __name__ == "__main__":
    for n in range(1, 11):
        rejection = simulate(n)
        print(f"Agenten: {n}, Abgewiesen: {rejection:.2%}")
