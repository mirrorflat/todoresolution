from dataclasses import dataclass


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


@dataclass
class Task:
    title: str
    urgency: float = 5.0
    importance: float = 5.0
    resolution: float = 5.0

    @property
    def score(self) -> float:
        return self.importance ** 2 * (self.urgency + 0.5 * (10 - self.resolution))
