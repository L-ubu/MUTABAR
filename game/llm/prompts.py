"""
game/llm/prompts.py
Prompt builders for LLM-generated battle narration and creature reveal flavor text.
"""

from __future__ import annotations

from typing import List

from game.creatures.creature import Creature
from game.creatures.types import MutationType


def build_battle_prompt(
    attacker: Creature,
    defender: Creature,
    command: str,
    damage: int,
    effectiveness: str,
    is_critical: bool,
) -> str:
    """Build a concise prompt for battle narration."""
    critical_note = " It was a critical hit!" if is_critical else ""
    eff_note = ""
    if effectiveness == "super_effective":
        eff_note = " It's super effective!"
    elif effectiveness == "resisted":
        eff_note = " The attack was resisted."

    prompt = (
        f'{attacker.name} the {attacker.mutation_type.name} creature '
        f'uses "{command}" against {defender.name} the {defender.mutation_type.name} creature. '
        f'{damage} damage dealt.{eff_note}{critical_note} '
        f'Narrate this battle moment.'
    )
    return prompt


def build_cpu_battle_prompt(
    attacker: Creature,
    defender: Creature,
    cpu_command: str,
    damage: int,
    effectiveness: str,
    is_critical: bool,
) -> str:
    """Build a prompt for CPU counterattack narration."""
    critical_note = " It was a critical hit!" if is_critical else ""
    eff_note = ""
    if effectiveness == "super_effective":
        eff_note = " It's super effective!"
    elif effectiveness == "resisted":
        eff_note = " The attack was resisted."

    prompt = (
        f'{attacker.name} the {attacker.mutation_type.name} creature '
        f'counterattacks {defender.name} with "{cpu_command}". '
        f'{damage} damage dealt.{eff_note}{critical_note} '
        f'Narrate the enemy\'s counterattack.'
    )
    return prompt


def build_event_scene_prompt(event, wave: int, player_team: List) -> str:
    """Build a prompt for AI-narrated random event scene."""
    team_info = ", ".join(c.name for c in player_team[:3]) if player_team else "no team"
    choices_hint = " or ".join(
        c.keywords[0] for c in event.choices[:3]
    )
    prompt = (
        f"The player's team ({team_info}) is between battles at wave {wave}. "
        f"They encounter: {event.description_template} "
        f"Narrate this scene dramatically in 2-3 sentences. "
        f"Hint at the choices: {choices_hint}."
    )
    return prompt


def build_event_outcome_prompt(event, player_action: str, choice) -> str:
    """Build a prompt for AI-narrated event outcome."""
    prompt = (
        f'The player chose to "{player_action}" during a {event.event_type.name.replace("_", " ")} event. '
        f"Outcome: {choice.outcome_template} "
        f"Narrate this result in 1-2 dramatic sentences."
    )
    return prompt


def build_reveal_prompt(
    creature_name: str,
    mutation_type: MutationType,
    traits: List[str],
) -> str:
    """Build a prompt for one-sentence creature reveal flavor text."""
    trait_list = ", ".join(traits) if traits else "none"

    prompt = (
        f"Write one sentence of flavor text for {creature_name}, "
        f"a {mutation_type.name}-type creature with traits: {trait_list}."
    )
    return prompt
