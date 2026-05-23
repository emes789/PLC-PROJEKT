import time
import random
import math


class MachineDataSimulator:

    PARAMS = {
        "Temperatura": {
            "unit": "°C",
            "mean": 72.0,
            "std": 2.5,
            "alarm_high": 90.0,
            "alarm_low": 50.0,
        },
        "Ciśnienie": {
            "unit": "bar",
            "mean": 5.0,
            "std": 0.25,
            "alarm_high": 7.0,
            "alarm_low": 2.5,
        },
        "Wibracje": {
            "unit": "mm/s",
            "mean": 2.0,
            "std": 0.30,
            "alarm_high": 5.0,
            "alarm_low": 0.1,
        },
        "Prąd": {
            "unit": "A",
            "mean": 12.5,
            "std": 1.0,
            "alarm_high": 18.0,
            "alarm_low": 6.0,
        },
    }

    def __init__(self, anomaly_prob: float = 0.04):
        self.anomaly_prob = anomaly_prob
        self._trend = {k: 0.0 for k in self.PARAMS}
        self._time = 0.0

    def get_reading(self) -> tuple[float, dict[str, float]]:
        timestamp = time.time()
        readings: dict[str, float] = {}
        self._time += 1.0

        for name, cfg in self.PARAMS.items():
            self._trend[name] += random.gauss(0.0, cfg["std"] * 0.08)
            self._trend[name] *= 0.97

            if random.random() < self.anomaly_prob:
                direction = random.choice([-1, 1])
                spike = direction * random.uniform(cfg["std"] * 4, cfg["std"] * 9)
                value = cfg["mean"] + spike
            else:
                value = random.gauss(cfg["mean"] + self._trend[name], cfg["std"])

            readings[name] = round(value, 2)

        return timestamp, readings
