"""
game/events/resolver.py
Rolling for events and resolving player choices.
"""

from __future__ import annotations

import random
from typing import List

from game.creatures.creature import Creature
from game.events.event_types import Event, EventChoice, EVENT_POOL


def roll_for_event(wave: int) -> Event | None:
    """Roll for a random event. 30% chance, guaranteed before boss waves."""
    if wave > 0 and (wave + 1) % 5 == 0:
        # Guaranteed event before boss wave
        return random.choice(EVENT_POOL)
    if random.random() < 0.30:
        return random.choice(EVENT_POOL)
    return None


def resolve_choice(player_input: str, event: Event) -> EventChoice:
    """Match player's free-form input to the best event choice via keyword overlap."""
    words = set(player_input.lower().split())
    best_choice = event.choices[0]
    best_score = 0

    for choice in event.choices:
        score = len(words & set(choice.keywords))
        if score > best_score:
            best_score = score
            best_choice = choice

    return best_choice


def apply_event_effect(choice: EventChoice, player_team: List[Creature], db=None):
    """Apply the effect of a chosen event to the player team."""
    eff = choice.effect

    # Heal
    if eff.heal_percent > 0 and player_team:
        for c in player_team:
            heal = int(c.max_hp * eff.heal_percent)
            c.current_hp = min(c.max_hp, c.current_hp + heal)

    # HP cost (applied to lead creature)
    if eff.hp_cost_percent > 0 and player_team:
        cost = int(player_team[0].max_hp * eff.hp_cost_percent)
        player_team[0].current_hp = max(1, player_team[0].current_hp - cost)

    # Stat buffs (applied to lead creature)
    if eff.stat_buff and player_team:
        lead = player_team[0]
        if "atk" in eff.stat_buff:
            lead.base_atk += eff.stat_buff["atk"]
        if "def" in eff.stat_buff:
            lead.base_def += eff.stat_buff["def"]
        if "hp" in eff.stat_buff:
            lead.base_hp += eff.stat_buff["hp"]
            lead.current_hp += eff.stat_buff["hp"]

    # Mutagen reward
    if eff.mutagen_reward > 0 and db:
        db.add_mutagen(eff.mutagen_reward)

    # Mutagen cost
    if eff.mutagen_cost > 0 and db:
        current = db.get_mutagen()
        if current >= eff.mutagen_cost:
            db.spend_mutagen(eff.mutagen_cost)
