"""
game/events/event_types.py
Data definitions for random between-wave events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List


class EventType(Enum):
    HEALING_SPRING = auto()
    MYSTERIOUS_TRADER = auto()
    WILD_CREATURE = auto()
    ABANDONED_LAB = auto()
    SHRINE = auto()


@dataclass
class EventEffect:
    heal_percent: float = 0.0
    stat_buff: dict = field(default_factory=dict)  # {"atk": 3, "def": 1}
    hp_cost_percent: float = 0.0
    mutagen_reward: int = 0
    mutagen_cost: int = 0


@dataclass
class EventChoice:
    keywords: List[str]
    outcome_template: str
    effect: EventEffect


@dataclass
class Event:
    event_type: EventType
    description_template: str
    choices: List[EventChoice]


EVENT_POOL: List[Event] = [
    Event(
        event_type=EventType.HEALING_SPRING,
        description_template=(
            "You stumble upon a glowing spring hidden between twisted roots. "
            "The water shimmers with restorative energy. "
            "You could rest here and heal, or press onward."
        ),
        choices=[
            EventChoice(
                keywords=["rest", "heal", "drink", "spring", "water", "bathe", "sit"],
                outcome_template="The spring's energy washes over your team. Everyone feels restored.",
                effect=EventEffect(heal_percent=0.5),
            ),
            EventChoice(
                keywords=["leave", "go", "push", "skip", "ignore", "continue", "onward"],
                outcome_template="You press on, leaving the spring behind. No time to waste.",
                effect=EventEffect(),
            ),
        ],
    ),
    Event(
        event_type=EventType.MYSTERIOUS_TRADER,
        description_template=(
            "A cloaked figure emerges from the shadows, carrying a bag of strange vials. "
            "'Trade your vitality for power,' they whisper. "
            "You could accept the deal or decline."
        ),
        choices=[
            EventChoice(
                keywords=["trade", "accept", "deal", "yes", "buy", "vial", "power", "take"],
                outcome_template="The trader injects a vial into your lead creature. It hurts, but power surges through.",
                effect=EventEffect(hp_cost_percent=0.2, stat_buff={"atk": 3}),
            ),
            EventChoice(
                keywords=["decline", "no", "refuse", "leave", "walk", "ignore", "pass"],
                outcome_template="You wave the trader away. They vanish into the mist.",
                effect=EventEffect(),
            ),
        ],
    ),
    Event(
        event_type=EventType.WILD_CREATURE,
        description_template=(
            "A wild creature blocks your path, snarling but not attacking. "
            "It seems curious rather than hostile. "
            "You could try to befriend it or scare it off for a mutagen bounty."
        ),
        choices=[
            EventChoice(
                keywords=["befriend", "friend", "pet", "tame", "calm", "gentle", "approach", "feed"],
                outcome_template="The creature calms down and nuzzles your hand. It joins your team temporarily.",
                effect=EventEffect(heal_percent=0.25),
            ),
            EventChoice(
                keywords=["scare", "fight", "attack", "chase", "shoo", "roar", "threaten", "hit"],
                outcome_template="The creature flees, dropping a small cache of mutagen behind.",
                effect=EventEffect(mutagen_reward=15),
            ),
        ],
    ),
    Event(
        event_type=EventType.ABANDONED_LAB,
        description_template=(
            "You find an abandoned laboratory filled with bubbling equipment. "
            "A half-finished experiment sits on the table. "
            "You could try the experiment on your lead creature, or leave it alone."
        ),
        choices=[
            EventChoice(
                keywords=["experiment", "try", "inject", "test", "use", "lab", "science", "apply"],
                outcome_template="The experiment surges through your creature! Its stats shift unpredictably.",
                effect=EventEffect(stat_buff={"atk": 2, "def": 2}),
            ),
            EventChoice(
                keywords=["leave", "go", "ignore", "skip", "walk", "no", "dangerous", "pass"],
                outcome_template="You wisely leave the unstable lab behind.",
                effect=EventEffect(),
            ),
        ],
    ),
    Event(
        event_type=EventType.SHRINE,
        description_template=(
            "An ancient shrine pulses with faint energy. "
            "An inscription reads: 'Offer mutagen for the blessing of resilience.' "
            "You could make an offering or simply pray."
        ),
        choices=[
            EventChoice(
                keywords=["offer", "sacrifice", "mutagen", "pay", "give", "donate"],
                outcome_template="The shrine absorbs your offering. A protective aura surrounds your whole team.",
                effect=EventEffect(mutagen_cost=30, stat_buff={"def": 2}),
            ),
            EventChoice(
                keywords=["pray", "meditate", "kneel", "worship", "hope", "wish", "ask"],
                outcome_template="A warm light envelops you as you pray. Minor healing flows through your team.",
                effect=EventEffect(heal_percent=0.2),
            ),
        ],
    ),
]
