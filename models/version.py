from dataclasses import dataclass, field


@dataclass
class TeslaVersion:
    version_id: str
    release_date: str
    features: list[dict] = field(default_factory=list)
    fleet_pct: float | None = None
    source_url: str = ""
