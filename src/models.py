from dataclasses import dataclass


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


# Purpose color key -> (Japanese label, hex color for a table row background).
# "none" has no hex value: it renders as the table's default (white) background.
PURPOSE_COLORS: dict[str, tuple[str, str | None]] = {
    "none": ("なし", None),
    "red": ("赤", "#F6C6C9"),
    "orange": ("橙", "#FAD9BF"),
    "yellow": ("黄", "#FBEFC0"),
    "green": ("緑", "#CDEBD6"),
    "blue": ("青", "#CBD9E8"),
    "indigo": ("藍", "#CFCBEA"),
    "violet": ("紫", "#E4CFF2"),
}


@dataclass
class Task:
    title: str
    urgency: float = 5.0
    importance: float = 5.0
    resolution: float = 5.0
    done: bool = False
    purpose: str | None = None  # a Purpose's name, or None if unassigned

    @property
    def score(self) -> float:
        return self.importance ** 2 * (self.urgency + 0.5 * (10 - self.resolution))


@dataclass
class Purpose:
    name: str
    color: str = "none"  # a key into PURPOSE_COLORS
