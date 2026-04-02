import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from game.creatures.creature import Creature
from game.creatures.traits import compute_trait_bonus
from game.battle.damage import calculate_damage, DamageResult
from game.battle.status_effects import (
    StatusEffect,
    StatusType,
    apply_tick,
    apply_damage_modifier,
)
from game.battle.cpu_ai import CpuDifficulty, generate_cpu_command


class BattleState(Enum):
    ACTIVE     = "ACTIVE"
    PLAYER_WIN = "PLAYER_WIN"
    CPU_WIN    = "CPU_WIN"


@dataclass
class TurnResult:
    player_command: str
    damage_dealt: int
    damage_received: int
    player_damage_result: Optional[DamageResult]
    cpu_damage_result: Optional[DamageResult]
    player_dot_damage: int = 0
    cpu_dot_damage: int = 0
    cpu_command: str = ""
    status_applied: Optional[StatusType] = None


class Battle:
    def __init__(
        self,
        player_team: List[Creature],
        cpu_team: List[Creature],
    ) -> None:
        self.player_team = player_team
        self.cpu_team = cpu_team

        self.player_active: Creature = self._first_alive(player_team)
        self.cpu_active: Creature = self._first_alive(cpu_team)

        self.player_active_effects: List[StatusEffect] = []
        self.cpu_active_effects: List[StatusEffect] = []

        self.state: BattleState = BattleState.ACTIVE
        self.turn_number: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_player_turn(self, command: str) -> TurnResult:
        """
        Execute one full turn:
          1. Player attacks CPU (unless stunned/frozen)
          2. Tick all status effects (DoT applied to respective targets)
          3. Clean expired effects
          4. Check if CPU active fainted → swap or PLAYER_WIN
          5. CPU attacks player (unless stunned/frozen)
          6. Check if player active fainted → swap or CPU_WIN
          7. Return TurnResult
        """
        self.turn_number += 1

        player_dmg_result: Optional[DamageResult] = None
        damage_dealt = 0

        # Step 1: Player attacks CPU
        if not self._check_skip(self.player_active_effects):
            if not self._check_dodge(self.cpu_active_effects):
                trait_bonus = compute_trait_bonus(command, self.player_active.traits)
                dmg_result = calculate_damage(
                    self.player_active,
                    self.cpu_active,
                    command,
                    trait_bonus=trait_bonus,
                )
                raw_damage = dmg_result.damage
                # Apply status modifiers: attacker side (player), defender side (cpu)
                modified = apply_damage_modifier(
                    raw_damage, self.player_active_effects, is_attacker=True
                )
                modified = apply_damage_modifier(
                    modified, self.cpu_active_effects, is_attacker=False
                )
                self.cpu_active.take_damage(modified)
                damage_dealt = modified
                player_dmg_result = DamageResult(
                    damage=modified,
                    is_critical=dmg_result.is_critical,
                    is_miss=False,
                    effectiveness=dmg_result.effectiveness,
                    trait_bonus=dmg_result.trait_bonus,
                )

        # Step 2: Tick all status effects, collect DoT
        player_dot = self._tick_effects(self.player_active_effects, self.player_active)
        cpu_dot = self._tick_effects(self.cpu_active_effects, self.cpu_active)

        # Step 3: Clean expired effects
        self.player_active_effects = [
            e for e in self.player_active_effects if not e.is_expired
        ]
        self.cpu_active_effects = [
            e for e in self.cpu_active_effects if not e.is_expired
        ]

        # Step 4: CPU active fainted?
        if self.cpu_active.is_fainted:
            swapped = self._swap_active(self.cpu_team, exclude=self.cpu_active)
            if swapped is not None:
                self.cpu_active = swapped
                self.cpu_active_effects = []
            else:
                self.state = BattleState.PLAYER_WIN
                return TurnResult(
                    player_command=command,
                    damage_dealt=damage_dealt,
                    damage_received=0,
                    player_damage_result=player_dmg_result,
                    cpu_damage_result=None,
                    player_dot_damage=player_dot,
                    cpu_dot_damage=cpu_dot,
                )

        # Step 5: CPU attacks player
        cpu_command = self._generate_cpu_command()
        cpu_dmg_result: Optional[DamageResult] = None
        damage_received = 0

        if not self._check_skip(self.cpu_active_effects):
            if not self._check_dodge(self.player_active_effects):
                cpu_trait_bonus = compute_trait_bonus(cpu_command, self.cpu_active.traits)
                c_dmg = calculate_damage(
                    self.cpu_active,
                    self.player_active,
                    cpu_command,
                    trait_bonus=cpu_trait_bonus,
                )
                raw_cpu = c_dmg.damage
                modified_cpu = apply_damage_modifier(
                    raw_cpu, self.cpu_active_effects, is_attacker=True
                )
                modified_cpu = apply_damage_modifier(
                    modified_cpu, self.player_active_effects, is_attacker=False
                )
                self.player_active.take_damage(modified_cpu)
                damage_received = modified_cpu
                cpu_dmg_result = DamageResult(
                    damage=modified_cpu,
                    is_critical=c_dmg.is_critical,
                    is_miss=False,
                    effectiveness=c_dmg.effectiveness,
                    trait_bonus=c_dmg.trait_bonus,
                )

        # Step 6: Player active fainted?
        if self.player_active.is_fainted:
            swapped = self._swap_active(self.player_team, exclude=self.player_active)
            if swapped is not None:
                self.player_active = swapped
                self.player_active_effects = []
            else:
                self.state = BattleState.CPU_WIN

        return TurnResult(
            player_command=command,
            damage_dealt=damage_dealt,
            damage_received=damage_received,
            player_damage_result=player_dmg_result,
            cpu_damage_result=cpu_dmg_result,
            player_dot_damage=player_dot,
            cpu_dot_damage=cpu_dot,
            cpu_command=cpu_command,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_cpu_command(self) -> str:
        """Simple random command from trait-based TACTICAL difficulty."""
        return generate_cpu_command(self.cpu_active, CpuDifficulty.TACTICAL)

    def _tick_effects(
        self, effects: List[StatusEffect], target: Creature
    ) -> int:
        """Tick each effect, apply DoT damage to target, return total DoT."""
        total_dot = 0
        for effect in effects:
            if not effect.is_expired:
                dot = apply_tick(effect)
                if dot > 0:
                    target.take_damage(dot)
                    total_dot += dot
        return total_dot

    def _check_skip(self, effects: List[StatusEffect]) -> bool:
        """
        Return True if the creature should skip its attack.
        STUN always skips; FREEZE skips 30% of the time.
        """
        for effect in effects:
            if effect.is_expired:
                continue
            if effect.status_type == StatusType.STUN:
                return True
            if effect.status_type == StatusType.FREEZE:
                if random.random() < 0.30:
                    return True
        return False

    def _check_dodge(self, defender_effects: List[StatusEffect]) -> bool:
        """Return True if the defender dodges (PHASE: 25% chance)."""
        for effect in defender_effects:
            if effect.is_expired:
                continue
            if effect.status_type == StatusType.PHASE:
                if random.random() < 0.25:
                    return True
        return False

    @staticmethod
    def _first_alive(team: List[Creature]) -> Creature:
        for c in team:
            if not c.is_fainted:
                return c
        raise ValueError("No alive creature in team")

    @staticmethod
    def _swap_active(
        team: List[Creature], exclude: Creature
    ) -> Optional[Creature]:
        """Return the first alive creature in team that is not the excluded one."""
        for c in team:
            if c is not exclude and not c.is_fainted:
                return c
        return None
