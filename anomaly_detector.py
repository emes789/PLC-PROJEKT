from collections import deque
import math


class AnomalyDetector:

    def __init__(self, window: int = 60, z_thresh: float = 3.5):
        self.window = window
        self.z_thresh = z_thresh
        self._buffers: dict[str, deque] = {}

    def check(
        self,
        param: str,
        value: float,
        alarm_high: float,
        alarm_low: float,
    ) -> tuple[bool, str | None]:
        if param not in self._buffers:
            self._buffers[param] = deque(maxlen=self.window)

        buf = self._buffers[param]

        if value > alarm_high:
            buf.append(value)
            return True, f"Przekroczono pr\u00f3g g\u00f3rny: {value:.2f} > {alarm_high:.2f}"
        if value < alarm_low:
            buf.append(value)
            return True, f"Poni\u017cej progu dolnego: {value:.2f} < {alarm_low:.2f}"

        buf.append(value)
        if len(buf) >= 20:
            n = len(buf)
            mean = sum(buf) / n
            variance = sum((x - mean) ** 2 for x in buf) / n
            std = math.sqrt(variance) if variance > 0 else 0.0
            if std > 1e-9:
                z = abs((value - mean) / std)
                if z > self.z_thresh:
                    return True, f"Anomalia statystyczna (Z = {z:.2f})"

        return False, None

    def reset(self, param: str | None = None) -> None:
        if param:
            self._buffers.pop(param, None)
        else:
            self._buffers.clear()