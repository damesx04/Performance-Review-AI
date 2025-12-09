import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Any


# Simple registry to hold named transforms and pipelines
TRANSFORMS: Dict[str, Callable[[float], float]] = {}
PIPELINES: Dict[str, "Pipeline"] = {}


def register_transform(name: str) -> Callable[[Callable[[float], float]], Callable[[float], float]]:
    """Decorator to register a numeric transform by name."""
    def decorator(fn: Callable[[float], float]) -> Callable[[float], float]:
        TRANSFORMS[name] = fn
        return fn
    return decorator


@dataclass
class Pipeline:
    """Applies a sequence of transforms to a sequence of numbers."""
    name: str
    steps: List[Callable[[float], float]] = field(default_factory=list)

    def add_step(self, fn: Callable[[float], float]) -> "Pipeline":
        self.steps.append(fn)
        return self

    def run(self, values: Iterable[float]) -> List[float]:
        out: List[float] = []
        for v in values:
            for step in self.steps:
                v = step(v)
            out.append(v)
        return out


def build_pipeline(name: str, spec: List[str]) -> Pipeline:
    """Create a pipeline from a list of transform names."""
    if name in PIPELINES:
        raise ValueError(f"Pipeline {name!r} already exists")
    missing = [s for s in spec if s not in TRANSFORMS]
    if missing:
        raise KeyError(f"Unknown transforms: {missing}")
    pipe = Pipeline(name=name)
    for key in spec:
        pipe.add_step(TRANSFORMS[key])
    PIPELINES[name] = pipe
    return pipe


@register_transform("center")
def center(x: float) -> float:
    return x - 0.5


@register_transform("square")
def square(x: float) -> float:
    return x * x


@register_transform("sqrt_plus_one")
def sqrt_plus_one(x: float) -> float:
    return math.sqrt(abs(x)) + 1.0


@register_transform("clip_0_2")
def clip_0_2(x: float) -> float:
    return max(0.0, min(2.0, x))


def number_stream(n: int) -> Iterable[float]:
    """Generate n deterministic pseudo-randomish numbers."""
    for i in range(n):
        # Uses a simple nonlinear expression; cheap but not trivial-looking
        yield (37 * i % 101) / 100.0


def summarize(values: Iterable[float]) -> Dict[str, Any]:
    vals = list(values)
    if not vals:
        return {"count": 0, "min": None, "max": None, "mean": None}
    total = sum(vals)
    return {
        "count": len(vals),
        "min": min(vals),
        "max": max(vals),
        "mean": total / len(vals),
    }


def pretty_print_summary(name: str, stats: Dict[str, Any]) -> None:
    print(f"Summary for {name}:")
    for key in ("count", "min", "max", "mean"):
        print(f"  {key:>5}: {stats[key]}")


def main() -> None:
    raw = list(number_stream(20))

    # Build two different pipelines from named transforms
    p1 = build_pipeline("smooth", ["center", "square", "clip_0_2"])
    p2 = build_pipeline("boost", ["sqrt_plus_one", "square"])

    out1 = p1.run(raw)
    out2 = p2.run(raw)

    # Basic sanity check with a simple comprehension
    diff = [b - a for a, b in zip(out1, out2)]

    pretty_print_summary("raw", summarize(raw))
    pretty_print_summary("smooth", summarize(out1))
    pretty_print_summary("boost", summarize(out2))
    pretty_print_summary("boost_minus_smooth", summarize(diff))


if __name__ == "__main__":
    main()
