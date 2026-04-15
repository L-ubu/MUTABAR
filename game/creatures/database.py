"""
game/creatures/database.py
Creature roster database for MUTABAR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from game.creatures.creature import CreatureCategory
from game.creatures.traits import Trait


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _t(name: str, desc: str, kw: List[str]) -> Trait:
    """Shorthand factory for a Trait."""
    return Trait(name=name, description=desc, keywords=kw)


# ---------------------------------------------------------------------------
# CreatureTemplate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CreatureTemplate:
    name: str
    category: CreatureCategory
    traits: List[Trait]
    base_hp: int
    base_atk: int
    base_def: int


# ---------------------------------------------------------------------------
# CREATURE_ROSTER
# ---------------------------------------------------------------------------

CREATURE_ROSTER: List[CreatureTemplate] = [
    # ------------------------------------------------------------------ ANIMALS (40)
    CreatureTemplate(
        name="Wolf",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Pack Hunter", "Bonus when allies assist", ["pack", "howl", "hunt"]),
            _t("Feral Bite", "Savage tearing bite", ["bite", "tear", "fang"]),
        ],
        base_hp=70, base_atk=14, base_def=8,
    ),
    CreatureTemplate(
        name="Tiger",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Pounce", "Leaps at prey from concealment", ["pounce", "leap", "spring"]),
            _t("Raking Claws", "Deep claw rakes", ["claw", "rake", "slash"]),
        ],
        base_hp=80, base_atk=16, base_def=9,
    ),
    CreatureTemplate(
        name="Hawk",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Talon Strike", "Diving talon attack", ["talon", "dive", "strike"]),
            _t("Keen Sight", "Spots weakness from afar", ["sight", "watch", "spot"]),
        ],
        base_hp=50, base_atk=13, base_def=6,
    ),
    CreatureTemplate(
        name="Bear",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Crushing Swipe", "Massive paw swipe", ["swipe", "crush", "maul"]),
            _t("Thick Hide", "Tough fur and fat absorb blows", ["hide", "tough", "fur"]),
        ],
        base_hp=120, base_atk=15, base_def=14,
    ),
    CreatureTemplate(
        name="Squid",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Ink Cloud", "Blinds opponents with ink", ["ink", "blind", "cloud"]),
            _t("Tentacle Wrap", "Constricts and holds", ["tentacle", "constrict", "wrap"]),
        ],
        base_hp=60, base_atk=11, base_def=7,
    ),
    CreatureTemplate(
        name="Eagle",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Aerial Dive", "High-speed aerial attack", ["dive", "aerial", "swoop"]),
            _t("Razor Beak", "Sharp beak jab", ["beak", "jab", "pierce"]),
        ],
        base_hp=55, base_atk=14, base_def=7,
    ),
    CreatureTemplate(
        name="Snake",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Venom Bite", "Injects paralytic toxin", ["venom", "bite", "poison"]),
            _t("Constrict", "Squeezes the life out", ["constrict", "squeeze", "wrap"]),
        ],
        base_hp=55, base_atk=13, base_def=6,
    ),
    CreatureTemplate(
        name="Shark",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Feeding Frenzy", "Multiple rapid bites", ["bite", "frenzy", "blood"]),
            _t("Cartilage Frame", "Flexible body reduces impact", ["flex", "dodge", "swim"]),
        ],
        base_hp=95, base_atk=17, base_def=10,
    ),
    CreatureTemplate(
        name="Crocodile",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Death Roll", "Spins violently to tear prey", ["roll", "spin", "tear"]),
            _t("Armored Scales", "Bony scutes deflect attacks", ["scale", "armor", "shield"]),
        ],
        base_hp=110, base_atk=16, base_def=16,
    ),
    CreatureTemplate(
        name="Mantis Shrimp",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Sonic Strike", "Club-like punch breaks shells", ["punch", "shatter", "sonic"]),
            _t("Color Vision", "Sees ultraviolet weaknesses", ["sight", "uv", "detect"]),
        ],
        base_hp=45, base_atk=18, base_def=5,
    ),
    CreatureTemplate(
        name="Octopus",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Camouflage", "Changes color to hide", ["hide", "camouflage", "blend"]),
            _t("Ink Burst", "Blinds and escapes", ["ink", "escape", "burst"]),
            _t("Multi-arm Grab", "Grabs with multiple arms", ["grab", "arm", "wrap"]),
        ],
        base_hp=60, base_atk=11, base_def=8,
    ),
    CreatureTemplate(
        name="Gorilla",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Chest Pound", "Intimidating display", ["pound", "intimidate", "chest"]),
            _t("Brute Force", "Raw strength attacks", ["strength", "brute", "smash"]),
        ],
        base_hp=130, base_atk=17, base_def=12,
    ),
    CreatureTemplate(
        name="Panther",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Shadow Stalk", "Hunts from darkness", ["shadow", "stalk", "dark"]),
            _t("Silent Pounce", "Near-silent ambush leap", ["pounce", "silent", "ambush"]),
        ],
        base_hp=75, base_atk=16, base_def=10,
    ),
    CreatureTemplate(
        name="Elephant",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Trample", "Charges and stomps", ["trample", "stomp", "charge"]),
            _t("Tusks", "Goring tusk strike", ["tusk", "gore", "impale"]),
            _t("Thick Skin", "Massive body absorbs hits", ["thick", "skin", "tough"]),
        ],
        base_hp=150, base_atk=15, base_def=20,
    ),
    CreatureTemplate(
        name="Vulture",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Scavenger", "Heals from fallen foes", ["scavenge", "feast", "dead"]),
            _t("Vomit Acid", "Projectile stomach acid", ["acid", "vomit", "burn"]),
        ],
        base_hp=60, base_atk=10, base_def=7,
    ),
    CreatureTemplate(
        name="Scorpion",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Stinger Tail", "Venomous tail strike", ["sting", "venom", "tail"]),
            _t("Pincer Grip", "Clamps tight with claws", ["pincer", "clamp", "claw"]),
        ],
        base_hp=50, base_atk=14, base_def=9,
    ),
    CreatureTemplate(
        name="Rhino",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Horn Charge", "Levels target with its horn", ["horn", "charge", "ram"]),
            _t("Ironclad Hide", "Near-impenetrable hide", ["hide", "tough", "armor"]),
        ],
        base_hp=140, base_atk=15, base_def=18,
    ),
    CreatureTemplate(
        name="Owl",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Silent Wings", "Attacks without sound", ["silent", "wing", "quiet"]),
            _t("Night Vision", "Sees perfectly in darkness", ["night", "sight", "dark"]),
        ],
        base_hp=48, base_atk=11, base_def=5,
    ),
    CreatureTemplate(
        name="Wolverine",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Berserker Fury", "Attacks with unrestrained rage", ["rage", "fury", "berserk"]),
            _t("Musk Spray", "Sprays foul musk to disorient", ["musk", "spray", "stink"]),
        ],
        base_hp=80, base_atk=16, base_def=11,
    ),
    CreatureTemplate(
        name="Jellyfish",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Nematocyst Sting", "Paralyzing stinging cells", ["sting", "paralyze", "shock"]),
            _t("Translucent Body", "Hard to target clearly", ["transparent", "dodge", "evade"]),
        ],
        base_hp=40, base_atk=8, base_def=4,
    ),
    CreatureTemplate(
        name="Cobra",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Spit Venom", "Spits blinding venom", ["spit", "venom", "blind"]),
            _t("Hood Flare", "Spreads hood to intimidate", ["hood", "intimidate", "flare"]),
        ],
        base_hp=55, base_atk=13, base_def=6,
    ),
    CreatureTemplate(
        name="Mole",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Burrow", "Digs underground to ambush", ["burrow", "dig", "underground"]),
            _t("Claw Slash", "Sharp digging claws slash", ["claw", "slash", "dig"]),
        ],
        base_hp=45, base_atk=9, base_def=7,
    ),
    CreatureTemplate(
        name="Bobbit Worm",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Lightning Lunge", "Explosive burst from underground", ["lunge", "burst", "ambush"]),
            _t("Scissor Jaws", "Powerful snapping mandibles", ["jaw", "snap", "scissor"]),
        ],
        base_hp=65, base_atk=17, base_def=7,
    ),
    CreatureTemplate(
        name="Pangolin",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Scale Ball", "Rolls into armored ball", ["roll", "scale", "ball"]),
            _t("Sticky Tongue", "Long sticky tongue snaps prey", ["tongue", "sticky", "snap"]),
        ],
        base_hp=70, base_atk=9, base_def=19,
    ),
    CreatureTemplate(
        name="Piranha",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Feeding Frenzy", "Rapid relentless biting", ["bite", "frenzy", "blood"]),
            _t("Razor Teeth", "Teeth cut through bone", ["teeth", "razor", "cut"]),
        ],
        base_hp=40, base_atk=14, base_def=4,
    ),
    CreatureTemplate(
        name="Tortoise",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Shell Retreat", "Retreats into impenetrable shell", ["shell", "retreat", "defend"]),
            _t("Slow Chomp", "Steady powerful bite", ["bite", "chomp", "slow"]),
        ],
        base_hp=100, base_atk=8, base_def=20,
    ),
    CreatureTemplate(
        name="Chameleon",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Camouflage", "Blends perfectly with surroundings", ["camouflage", "hide", "blend"]),
            _t("Tongue Lash", "Projectile sticky tongue", ["tongue", "lash", "snap"]),
        ],
        base_hp=50, base_atk=10, base_def=7,
    ),
    CreatureTemplate(
        name="Komodo Dragon",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Bacterial Bite", "Bite causes deadly infection", ["bite", "infect", "bacteria"]),
            _t("Tail Whip", "Heavy tail sweeps legs", ["tail", "whip", "sweep"]),
        ],
        base_hp=105, base_atk=15, base_def=13,
    ),
    CreatureTemplate(
        name="Bat",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Echolocation", "Navigates perfectly in darkness", ["echo", "sound", "dark"]),
            _t("Dive Screech", "Disorienting sonic screech dive", ["screech", "sonic", "dive"]),
        ],
        base_hp=44, base_atk=10, base_def=5,
    ),
    CreatureTemplate(
        name="Honey Badger",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Fearless", "Never backs down regardless of odds", ["fearless", "brave", "stand"]),
            _t("Loose Skin", "Skin twists free from grips", ["skin", "twist", "escape"]),
        ],
        base_hp=75, base_atk=15, base_def=12,
    ),
    CreatureTemplate(
        name="Frog",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Poison Skin", "Toxic skin deters attackers", ["poison", "skin", "toxic"]),
            _t("Tongue Whip", "Fast sticky tongue strike", ["tongue", "whip", "snap"]),
        ],
        base_hp=42, base_atk=9, base_def=5,
    ),
    CreatureTemplate(
        name="Crab",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Claw Crush", "Powerful claw crush", ["claw", "crush", "grip"]),
            _t("Exoskeleton", "Hard shell blocks damage", ["shell", "armor", "block"]),
        ],
        base_hp=65, base_atk=12, base_def=15,
    ),
    CreatureTemplate(
        name="Dolphin",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Sonar Pulse", "Disorienting echolocation blast", ["sonar", "pulse", "echo"]),
            _t("Ram Charge", "High-speed underwater ram", ["ram", "charge", "speed"]),
        ],
        base_hp=80, base_atk=13, base_def=9,
    ),
    CreatureTemplate(
        name="Lion",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Roar", "Paralyzes foes with fear", ["roar", "fear", "intimidate"]),
            _t("Mane Guard", "Thick mane deflects neck attacks", ["mane", "block", "guard"]),
        ],
        base_hp=110, base_atk=17, base_def=12,
    ),
    CreatureTemplate(
        name="Raven",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Mimic", "Copies enemy tactic", ["mimic", "copy", "trick"]),
            _t("Eye Peck", "Targets the eyes", ["peck", "eye", "blind"]),
        ],
        base_hp=45, base_atk=10, base_def=5,
    ),
    CreatureTemplate(
        name="Stingray",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Barb Sting", "Venomous serrated barb", ["barb", "sting", "venom"]),
            _t("Glide Dodge", "Graceful underwater evasion", ["glide", "dodge", "swim"]),
        ],
        base_hp=65, base_atk=13, base_def=8,
    ),
    CreatureTemplate(
        name="Wasp",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Swarm Sting", "Calls swarm for repeated stings", ["swarm", "sting", "swarm"]),
            _t("Mandible Bite", "Sharp mandible cut", ["bite", "mandible", "cut"]),
        ],
        base_hp=40, base_atk=12, base_def=4,
    ),
    CreatureTemplate(
        name="Hippo",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Gape Crush", "Opens massive jaws to crush", ["jaw", "crush", "chomp"]),
            _t("Bloat Body", "Enormous mass absorbs impact", ["bulk", "body", "tough"]),
        ],
        base_hp=145, base_atk=16, base_def=17,
    ),
    CreatureTemplate(
        name="Cheetah",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Sprint", "Fastest land speed burst", ["sprint", "speed", "run"]),
            _t("Trip Bite", "Bites leg to topple prey", ["bite", "trip", "leg"]),
        ],
        base_hp=65, base_atk=15, base_def=6,
    ),
    CreatureTemplate(
        name="Moose",
        category=CreatureCategory.ANIMAL,
        traits=[
            _t("Antler Slam", "Batters foes with huge antlers", ["antler", "slam", "ram"]),
            _t("Charge", "Full-speed charge", ["charge", "trample", "run"]),
        ],
        base_hp=130, base_atk=14, base_def=13,
    ),

    # ------------------------------------------------------------------ MYTHOLOGICALS (10)
    CreatureTemplate(
        name="Dragon",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Fire Breath", "Scorching cone of flame", ["fire", "breath", "burn"]),
            _t("Dragon Scales", "Near-impenetrable scales", ["scale", "armor", "block"]),
            _t("Wing Gale", "Wings blast a wind shockwave", ["wing", "gale", "wind"]),
        ],
        base_hp=180, base_atk=18, base_def=15,
    ),
    CreatureTemplate(
        name="Phoenix",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Rebirth Flame", "Rises from ashes once per battle", ["rebirth", "flame", "rise"]),
            _t("Solar Burst", "Blinds and burns with solar energy", ["solar", "burst", "burn"]),
            _t("Feather Embers", "Feathers ignite on impact", ["feather", "ember", "fire"]),
        ],
        base_hp=120, base_atk=16, base_def=11,
    ),
    CreatureTemplate(
        name="Griffin",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Eagle Dive", "Airborne talon strike", ["dive", "talon", "aerial"]),
            _t("Lion Mauling", "Powerful lion-body maul", ["maul", "claw", "rend"]),
        ],
        base_hp=130, base_atk=17, base_def=13,
    ),
    CreatureTemplate(
        name="Kraken",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Tentacle Crush", "Multiple tentacles crush hull", ["tentacle", "crush", "wrap"]),
            _t("Whirlpool", "Creates drowning vortex", ["vortex", "drown", "spin"]),
            _t("Deep Ink", "Blackens entire area", ["ink", "dark", "blind"]),
        ],
        base_hp=170, base_atk=17, base_def=14,
    ),
    CreatureTemplate(
        name="Hydra",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Multi-Head Bite", "Several heads bite at once", ["bite", "multi", "fang"]),
            _t("Regeneration", "Severed heads regrow stronger", ["regen", "heal", "grow"]),
            _t("Acid Spit", "Acidic breath from every head", ["acid", "spit", "burn"]),
        ],
        base_hp=160, base_atk=16, base_def=12,
    ),
    CreatureTemplate(
        name="Kitsune",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Fox Fire", "Blue illusion flames confuse", ["fox", "fire", "illusion"]),
            _t("Nine Tails", "Whips multiple tails to strike", ["tail", "whip", "multi"]),
            _t("Shape Shift", "Transforms to evade or trick", ["shift", "transform", "trick"]),
        ],
        base_hp=100, base_atk=15, base_def=10,
    ),
    CreatureTemplate(
        name="Basilisk",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Petrifying Gaze", "Turns targets to stone", ["gaze", "stone", "petrify"]),
            _t("Lethal Venom", "Most potent venom known", ["venom", "poison", "lethal"]),
        ],
        base_hp=110, base_atk=15, base_def=11,
    ),
    CreatureTemplate(
        name="Thunderbird",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Lightning Strike", "Calls lightning from wings", ["lightning", "strike", "thunder"]),
            _t("Storm Shroud", "Cloaks itself in storm clouds", ["storm", "cloud", "shroud"]),
            _t("Gale Feathers", "Feathers shred like razors in wind", ["feather", "gale", "slash"]),
        ],
        base_hp=130, base_atk=17, base_def=12,
    ),
    CreatureTemplate(
        name="Cerberus",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Triple Bite", "All three heads bite simultaneously", ["bite", "triple", "fang"]),
            _t("Hellfire Breath", "Breathes infernal fire", ["fire", "breath", "hell"]),
            _t("Guardian Fury", "Rage mode when guarding gate", ["guard", "rage", "fury"]),
        ],
        base_hp=150, base_atk=18, base_def=13,
    ),
    CreatureTemplate(
        name="Leviathan",
        category=CreatureCategory.MYTHOLOGICAL,
        traits=[
            _t("Tidal Crush", "Body slam creates tidal wave", ["tidal", "wave", "crush"]),
            _t("Abyssal Roar", "Deep-sea pressure shockwave", ["roar", "abyss", "pressure"]),
            _t("Swallow Whole", "Engulfs opponent in one bite", ["swallow", "engulf", "bite"]),
        ],
        base_hp=180, base_atk=17, base_def=16,
    ),

    # ------------------------------------------------------------------ FAMOUS MONSTERS — EPIC (15)
    CreatureTemplate(
        name="Werewolf",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Moonrage", "Power surges under moonlight", ["moon", "rage", "transform"]),
            _t("Savage Claws", "Rends flesh with cursed claws", ["claw", "curse", "rend"]),
        ],
        base_hp=120, base_atk=18, base_def=11,
    ),
    CreatureTemplate(
        name="Vampire",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Blood Drain", "Drains life to heal self", ["drain", "blood", "heal"]),
            _t("Bat Swarm", "Dissolves into a swarm of bats", ["bat", "swarm", "evade"]),
            _t("Hypnotic Gaze", "Mesmerizes the weak-willed", ["hypnotic", "gaze", "stun"]),
        ],
        base_hp=110, base_atk=16, base_def=12,
    ),
    CreatureTemplate(
        name="Minotaur",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Labyrinth Charge", "Charges blindly with massive horns", ["charge", "horn", "ram"]),
            _t("Axe Cleave", "Brutal overhead axe swing", ["axe", "cleave", "smash"]),
        ],
        base_hp=150, base_atk=19, base_def=14,
    ),
    CreatureTemplate(
        name="Cyclops",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Boulder Hurl", "Throws massive rocks", ["boulder", "throw", "crush"]),
            _t("Eye Beam", "Focused energy from single eye", ["beam", "eye", "blast"]),
        ],
        base_hp=170, base_atk=20, base_def=13,
    ),
    CreatureTemplate(
        name="Medusa",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Stone Gaze", "Petrifies those who look", ["stone", "gaze", "petrify"]),
            _t("Snake Hair", "Venomous serpents strike from her head", ["snake", "venom", "bite"]),
        ],
        base_hp=90, base_atk=17, base_def=10,
    ),
    CreatureTemplate(
        name="Golem",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Stone Fist", "Devastating rocky punch", ["stone", "fist", "smash"]),
            _t("Earthen Shell", "Nearly indestructible stone body", ["stone", "armor", "shell"]),
        ],
        base_hp=200, base_atk=14, base_def=22,
    ),
    CreatureTemplate(
        name="Banshee",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Death Wail", "Piercing scream damages all", ["wail", "scream", "sonic"]),
            _t("Ghostly Phase", "Phases through attacks", ["ghost", "phase", "evade"]),
        ],
        base_hp=80, base_atk=18, base_def=6,
    ),
    CreatureTemplate(
        name="Chimera",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Triple Maw", "Lion, goat and snake heads attack", ["bite", "triple", "maw"]),
            _t("Flame Breath", "Goat head breathes fire", ["fire", "breath", "burn"]),
            _t("Tail Venom", "Snake tail injects poison", ["venom", "tail", "poison"]),
        ],
        base_hp=140, base_atk=18, base_def=13,
    ),
    CreatureTemplate(
        name="Manticore",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Tail Spikes", "Launches venomous tail spikes", ["spike", "tail", "venom"]),
            _t("Lion Fury", "Savage lion body attacks", ["fury", "claw", "maul"]),
        ],
        base_hp=130, base_atk=19, base_def=12,
    ),
    CreatureTemplate(
        name="Yeti",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Frost Slam", "Icy fist shatters bone", ["frost", "slam", "ice"]),
            _t("Blizzard Roar", "Summons freezing winds", ["blizzard", "roar", "cold"]),
        ],
        base_hp=160, base_atk=17, base_def=16,
    ),
    CreatureTemplate(
        name="Mothman",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Red Eyes", "Hypnotic crimson stare", ["eyes", "red", "hypnotic"]),
            _t("Wing Gust", "Massive wings create shockwave", ["wing", "gust", "wind"]),
            _t("Omen Aura", "Presence causes dread", ["omen", "dread", "fear"]),
        ],
        base_hp=100, base_atk=15, base_def=11,
    ),
    CreatureTemplate(
        name="Wendigo",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Hunger Frenzy", "Insatiable hunger drives attacks", ["hunger", "frenzy", "bite"]),
            _t("Frost Aura", "Freezing presence slows foes", ["frost", "aura", "slow"]),
        ],
        base_hp=130, base_atk=20, base_def=10,
    ),
    CreatureTemplate(
        name="Frankenstein",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Lightning Rod", "Absorbs electricity to power up", ["lightning", "absorb", "power"]),
            _t("Brute Slam", "Massive fists pound the ground", ["slam", "brute", "smash"]),
        ],
        base_hp=180, base_atk=16, base_def=15,
    ),
    CreatureTemplate(
        name="Nessie",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Deep Dive", "Vanishes beneath the waves", ["dive", "deep", "evade"]),
            _t("Tidal Slam", "Massive tail creates waves", ["tidal", "slam", "wave"]),
        ],
        base_hp=160, base_atk=14, base_def=18,
    ),
    CreatureTemplate(
        name="Chupacabra",
        category=CreatureCategory.FAMOUS,
        traits=[
            _t("Blood Siphon", "Drains blood to restore health", ["blood", "drain", "heal"]),
            _t("Night Ambush", "Strikes from darkness", ["night", "ambush", "stealth"]),
        ],
        base_hp=95, base_atk=18, base_def=9,
    ),

    # ------------------------------------------------------------------ ORIGINALS — LEGENDARY (5)
    CreatureTemplate(
        name="Snorerelax",
        category=CreatureCategory.ORIGINAL,
        traits=[
            _t("Deep Slumber", "Sleeps through nearly any attack", ["sleep", "slumber", "rest"]),
            _t("Crushing Weight", "Falls onto foes using sheer mass", ["weight", "crush", "fall"]),
            _t("Dream Pulse", "Emits calming dream energy to disorient", ["dream", "pulse", "calm"]),
        ],
        base_hp=200, base_atk=10, base_def=18,
    ),
    CreatureTemplate(
        name="Glitchfang",
        category=CreatureCategory.ORIGINAL,
        traits=[
            _t("Data Rend", "Corrupts enemy data with claws", ["data", "corrupt", "rend"]),
            _t("Pixel Shift", "Teleports via digital glitch", ["glitch", "teleport", "shift"]),
            _t("Error Cascade", "Triggers cascading system errors", ["error", "cascade", "crash"]),
        ],
        base_hp=85, base_atk=17, base_def=8,
    ),
    CreatureTemplate(
        name="Voidmaw",
        category=CreatureCategory.ORIGINAL,
        traits=[
            _t("Devour", "Consumes matter and energy alike", ["devour", "consume", "eat"]),
            _t("Void Surge", "Expands the void to engulf foes", ["void", "surge", "darkness"]),
            _t("Event Horizon", "Nothing escapes its gravitational pull", ["gravity", "pull", "horizon"]),
        ],
        base_hp=110, base_atk=16, base_def=14,
    ),
    CreatureTemplate(
        name="King Kong",
        category=CreatureCategory.ORIGINAL,
        traits=[
            _t("Primal Smash", "Devastating double-fist ground pound", ["smash", "fist", "pound"]),
            _t("Chest Roar", "Terrifying war cry shakes the earth", ["roar", "shake", "fear"]),
            _t("Tower Climb", "Scales anything for aerial advantage", ["climb", "aerial", "height"]),
        ],
        base_hp=220, base_atk=22, base_def=16,
    ),
    CreatureTemplate(
        name="Godzilla",
        category=CreatureCategory.ORIGINAL,
        traits=[
            _t("Atomic Breath", "Nuclear energy beam annihilates", ["atomic", "breath", "nuke"]),
            _t("Titan Stomp", "Earthquake-inducing footfall", ["stomp", "earthquake", "titan"]),
            _t("Radiation Aura", "Passive radiation damages nearby foes", ["radiation", "aura", "burn"]),
        ],
        base_hp=250, base_atk=24, base_def=20,
    ),

    # ------------------------------------------------------------------ HYBRIDS — MUTAGEN (12)
    CreatureTemplate(
        name="Crococrow",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Death Roll Dive", "Aerial spin tears prey apart", ["roll", "dive", "tear"]),
            _t("Beak Snap", "Crocodile-strength beak bite", ["beak", "snap", "crush"]),
            _t("Swamp Wings", "Murky wings conceal approach", ["wing", "swamp", "stealth"]),
        ],
        base_hp=120, base_atk=19, base_def=14,
    ),
    CreatureTemplate(
        name="Dragophoenix",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Eternal Flame", "Fire that never dies", ["flame", "eternal", "burn"]),
            _t("Rebirth Scales", "Dragon scales regenerate from ash", ["rebirth", "scale", "heal"]),
            _t("Solar Dragon Breath", "Sun-powered fire stream", ["solar", "breath", "fire"]),
        ],
        base_hp=160, base_atk=21, base_def=14,
    ),
    CreatureTemplate(
        name="Sharkbear",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Land Jaws", "Shark bite on bear body", ["jaw", "bite", "crush"]),
            _t("Frenzy Maul", "Berserker shark-bear rampage", ["frenzy", "maul", "rage"]),
            _t("Amphibious Charge", "Attacks from land or water", ["charge", "amphibious", "rush"]),
        ],
        base_hp=170, base_atk=22, base_def=15,
    ),
    CreatureTemplate(
        name="Wolfspider",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Web Pack", "Web traps coordinated with pack", ["web", "pack", "trap"]),
            _t("Venom Fangs", "Wolf jaws with spider venom", ["venom", "fang", "bite"]),
            _t("Eight-Leg Pounce", "Eight legs for explosive speed", ["pounce", "speed", "leg"]),
        ],
        base_hp=100, base_atk=20, base_def=11,
    ),
    CreatureTemplate(
        name="Eaglesnake",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Sky Constrict", "Wraps prey mid-flight", ["constrict", "sky", "wrap"]),
            _t("Venom Talon", "Talons drip with venom", ["venom", "talon", "poison"]),
        ],
        base_hp=90, base_atk=21, base_def=9,
    ),
    CreatureTemplate(
        name="Octolion",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Tentacle Mane", "Eight tentacles replace mane", ["tentacle", "mane", "grab"]),
            _t("Ink Roar", "Blinding ink blast with deafening roar", ["ink", "roar", "blind"]),
            _t("Deep Pride", "Commands respect from the abyss", ["pride", "abyss", "fear"]),
        ],
        base_hp=150, base_atk=19, base_def=15,
    ),
    CreatureTemplate(
        name="Scorpiorilla",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Venom Pound", "Stinger tail on gorilla body", ["venom", "pound", "sting"]),
            _t("Pincer Fist", "Gorilla punch with scorpion claws", ["pincer", "fist", "smash"]),
        ],
        base_hp=160, base_atk=21, base_def=16,
    ),
    CreatureTemplate(
        name="Batshark",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Sonar Frenzy", "Echolocation-guided feeding frenzy", ["sonar", "frenzy", "bite"]),
            _t("Night Fin", "Flies through air like water", ["fin", "fly", "night"]),
            _t("Blood Scent", "Tracks prey by blood from miles away", ["blood", "scent", "track"]),
        ],
        base_hp=110, base_atk=20, base_def=10,
    ),
    CreatureTemplate(
        name="Tigerhawk",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Striped Dive", "Tiger pounce from the sky", ["dive", "pounce", "stripe"]),
            _t("Claw Storm", "Talons and tiger claws shred together", ["claw", "storm", "rend"]),
        ],
        base_hp=105, base_atk=22, base_def=10,
    ),
    CreatureTemplate(
        name="Frogmantis",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Tongue Scythe", "Sticky tongue with mantis blade", ["tongue", "scythe", "cut"]),
            _t("Leap Strike", "Explosive leap into mantis slash", ["leap", "strike", "slash"]),
            _t("Toxic Molt", "Sheds poisonous skin", ["toxic", "molt", "poison"]),
        ],
        base_hp=80, base_atk=23, base_def=7,
    ),
    CreatureTemplate(
        name="Rhinocobra",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Venom Horn", "Horn charge delivers neurotoxin", ["venom", "horn", "charge"]),
            _t("Hood Shield", "Cobra hood as armored shield", ["hood", "shield", "block"]),
        ],
        base_hp=155, base_atk=19, base_def=18,
    ),
    CreatureTemplate(
        name="Owlpanther",
        category=CreatureCategory.HYBRID,
        traits=[
            _t("Silent Shadow", "Owl silence with panther stealth", ["silent", "shadow", "stealth"]),
            _t("Night Rend", "Nocturnal ambush tears prey apart", ["night", "rend", "ambush"]),
            _t("Wisdom Fury", "Calculates the perfect strike", ["wisdom", "fury", "precise"]),
        ],
        base_hp=100, base_atk=20, base_def=12,
    ),
]


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------

def get_creature_by_name(name: str) -> CreatureTemplate | None:
    """Return the creature whose name matches (case-insensitive), or None."""
    name_lower = name.lower()
    for creature in CREATURE_ROSTER:
        if creature.name.lower() == name_lower:
            return creature
    return None


def get_creatures_by_category(category: CreatureCategory) -> List[CreatureTemplate]:
    """Return all creatures belonging to the given category."""
    return [c for c in CREATURE_ROSTER if c.category == category]
