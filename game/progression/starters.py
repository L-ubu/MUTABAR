from game.creatures.database import get_creature_by_name

_STARTERS = [
    ("Wolf", "FIRE"),
    ("Crab", "WATER"),
    ("Hawk", "AIR"),
]


def seed_starters_if_needed(db) -> None:
    if db.load_all_monsters():
        return
    for name, mutation_type in _STARTERS:
        tmpl = get_creature_by_name(name)
        if tmpl:
            import json
            db.save_creature(
                name=tmpl.name, species=tmpl.name, category=tmpl.category.value.upper(),
                mutation_type=mutation_type, base_hp=tmpl.base_hp, base_atk=tmpl.base_atk,
                base_def=tmpl.base_def, traits_json=json.dumps([t.name for t in tmpl.traits]),
                is_shiny=0,
            )
