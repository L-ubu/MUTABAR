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
    """
    Build a prompt for vivid 2-3 sentence battle narration.

    Includes:
    - Attacker type personality in the style instruction
    - Both creature names, types, and trait names
    - Player's command text
    - Damage dealt, effectiveness text, critical hit flag
    """
    attacker_traits = ", ".join(t.name for t in attacker.traits) if attacker.traits else "none"
    defender_traits = ", ".join(t.name for t in defender.traits) if defender.traits else "none"

    critical_note = " This was a critical hit!" if is_critical else ""

    prompt = (
        f"You are narrating a creature battle. "
        f"Write in the voice of a {attacker.mutation_type.personality} creature.\n\n"
        f"Attacker: {attacker.name} (type: {attacker.mutation_type.name}, traits: {attacker_traits})\n"
        f"Defender: {defender.name} (type: {defender.mutation_type.name}, traits: {defender_traits})\n"
        f"Player command: \"{command}\"\n"
        f"Damage dealt: {damage}\n"
        f"Effectiveness: {effectiveness}{critical_note}\n\n"
        f"Write 2-3 vivid sentences narrating this battle moment. "
        f"Reference the attacker's personality, the specific attack, and the impact on the defender."
    )
    return prompt


def build_reveal_prompt(
    creature_name: str,
    mutation_type: MutationType,
    traits: List[str],
) -> str:
    """
    Build a prompt for one-sentence creature reveal flavor text.

    Includes:
    - Type personality
    - Creature name and trait names
    """
    trait_list = ", ".join(traits) if traits else "none"

    prompt = (
        f"You are writing flavor text for a creature card game. "
        f"Write in the voice of a {mutation_type.personality} creature.\n\n"
        f"Creature: {creature_name} (type: {mutation_type.name}, traits: {trait_list})\n\n"
        f"Write exactly one sentence of vivid flavor text that captures this creature's essence, "
        f"incorporating its {mutation_type.name} nature and traits."
    )
    return prompt
