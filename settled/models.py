from dataclasses import dataclass, field

KINDS = ("haan", "na", "unsure", "question", "no answer")
OUTCOMES = ("call", "ask again", "charged", "held", "not charged", "cancelled")
STEPS = ("identity", "ask", "readback", "followup", "done")


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
    say: dict = field(default_factory=dict)
    mobile: str | None = None
    born: int | None = None

    def plan(self, plan_id):
        return next((p for p in self.plans if p.id == plan_id), None)

    def cheaper(self, plan):
        return min((p for p in self.plans if p.price < plan.price), key=lambda p: p.price, default=None)


@dataclass
class Answer:
    kind: str
    words: str = ""
    reason: str | None = None
    speaker: str = "shopkeeper"

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


@dataclass
class CallState:
    """What the board shows about a call in progress. call is the id of the call's "due" row."""
    step: str | None = None
    call: int | None = None
