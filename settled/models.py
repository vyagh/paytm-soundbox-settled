from dataclasses import dataclass, field

KINDS = ("haan", "na", "unsure", "question", "no answer")
OUTCOMES = ("call", "ask again", "charged", "held", "not charged")


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    price: int
    demo: bool = True


@dataclass
class Shop:
    id: str
    name: str
    owner: str | None
    signup: dict | None
    delivery: dict | None
    returned: dict | None
    plans: list[Plan] = field(default_factory=list)
    language: str = "hi"

    def plan(self, plan_id):
        return next((p for p in self.plans if p.id == plan_id), None)


@dataclass
class Answer:
    kind: str
    words: str = ""
    reason: str | None = None
    plan: str | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown answer kind: {self.kind!r}")


@dataclass
class Decision:
    outcome: str
    rule: str
    plan: Plan | None = None

    def __post_init__(self):
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome: {self.outcome!r}")
