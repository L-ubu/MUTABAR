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
