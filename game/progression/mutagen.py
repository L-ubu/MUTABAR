def calculate_wave_mutagen(wave: int, super_effective_kill: bool = False, crit_kill: bool = False) -> int:
    base = wave * 10
    if base == 0:
        return 0
    mult = 1.0
    if super_effective_kill:
        mult *= 1.5
    if crit_kill:
        mult *= 1.25
    return round(base * mult)
