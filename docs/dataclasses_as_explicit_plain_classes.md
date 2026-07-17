# docs/dataclasses_as_explicit_plain_classes.md

## Overview: 

This is a technical architectural guide for python's dataclass.

This guide details the transition from `dataclass` to an explicit plain class. 
The goal is to frames the architectural trade-offs objectively for developers navigating the coffeeplot codebase and who may also implement explicit plain classes in favor of using dataclass decorator features.

# Architectural Case Study: Dataclasses vs. Explicit Plain Classes

This document analyzes the evolution of the `SeriesMemory` class in `pipeline-eds`. It traces why the implementation transitioned from a standard `@dataclass` definition to a plain Python class utilizing explicit `__init__` and `__slots__` definitions.

## The Objective
`SeriesMemory` is an in-memory storage unit representing a single telemetry sequence (`SeriesDefinition`) and its associated chronological array of data (`list[Observation]`). 

---

## Implementation Comparison

### Approach A: The `@dataclass` Pattern (Deprecated)
The initial design leveraged Python's standard `dataclass` library to minimize boilerplate code.

```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class SeriesMemory:
    """
    A series with an observation attribute held in memory.
    """
    definition: SeriesDefinition
    observations: list[Observation] = field(default_factory=list)
    
    def consume_observation(self, observation: Observation) -> None:
        """The rich man's append."""
        self.observations.append(observation)

```

#### Structural Risks of the Dataclass Approach for This Use Case:

1. **Mutable Defaults & Side Effects:** Standard dataclasses require `field(default_factory=list)` to avoid the notorious "shared mutable list" trap. While safe, this syntax adds cognitive overhead for developers unfamiliar with the distinction between class-level defaults and instantiation-time factories.
2. **Post-Initialization Fragility:** Custom setups or safety validations require overriding `__post_init__`. This splits the instantiation path across two separate, magic procedures.
3. **Implicit Method Generation:** The decorator generates `__eq__`, `__repr__`, and comparison methods automatically. For memory buffers storing thousands of temporal observations, default value-equality checks (`__eq__`) can cause severe performance penalties by deep-comparing entire lists of child objects.

---

### Approach B: The Plain Class Pattern with Explicit Slots (Adopted)

The production implementation converts `SeriesMemory` to a clean, explicit standard Python class.

```python
class SeriesMemory:
    __slots__ = ("definition", "observations")  # Memory efficiency

    def __init__(self, definition: SeriesDefinition, observations: list[Observation] = None) -> None:
        self.definition = definition
        # Explicit evaluation avoids default mutable traps cleanly
        self.observations = observations if observations is not None else []
        self.__post_init__()

    def __post_init__(self) -> None:
        # Internal configuration hooks run transparently
        logger.debug(f"Initialized SeriesMemory for: {self.definition.label}")

    def __repr__(self) -> str:
        return f"SeriesMemory(definition={self.definition!r}, observations={self.observations!r})"
    
    def consume_observation(self, observation: Observation) -> None:
        """The rich man's append."""
        logger.debug(f"{self.definition=}")
        logger.debug(f"{observation=}")
        self.observations.append(observation)

```

#### Architectural Advantages:

* **Memory Optimization:** Explicit use of `__slots__` bypasses the creation of an underlying instance dictionary (`__dict__`). For high-throughput telemetry pipelines processing thousands of metric series, this dramatically lowers memory overhead.
* **Safer Default Initializers:** The idiom `observations = None` evaluated in a standard Python `__init__` is an explicit, standard pattern widely understood across all levels of Python competency.
* **Control Over Behavior:** The class explicitly defines only what it needs (`__repr__`), intentionally avoiding implicit comparison methods (`__eq__`) that could silently degrade performance during object comparison.

---

## Summary of Decision Matrix

| Characteristic | `@dataclass(slots=True)` | Standard Class + `__slots__` |
| --- | --- | --- |
| **Primary Use Case** | Cold, static data containers | Dynamic operational state containers with methods |
| **Default Instantiation** | Automated, implicit | Manual, explicit, easy to debug |
| **Comparison Behavior** | Deep-compares structural values | Identity-based pointer comparison (Default) |
| **Brevity** | High (Minimal boilerplates) | Moderate (Requires explicit `__init__`) |
| **Memory Footprint** | Low (When using `slots=True`) | Low |


---
