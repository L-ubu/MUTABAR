import pytest
from game.creatures.types import MutationType, get_type_effectiveness


def test_all_eight_types_exist():
    expected = {"FIRE", "WATER", "AIR", "EARTH", "MUTA", "TECH", "COSM", "SHAD"}
    actual = {t.name for t in MutationType}
    assert actual == expected


def test_colors():
    assert MutationType.FIRE.color == (247, 118, 142)
    assert MutationType.WATER.color == (115, 218, 202)
    assert MutationType.AIR.color == (122, 162, 247)
    assert MutationType.EARTH.color == (158, 206, 106)
    assert MutationType.MUTA.color == (224, 175, 104)
    assert MutationType.TECH.color == (169, 177, 214)
    assert MutationType.COSM.color == (187, 154, 247)
    assert MutationType.SHAD.color == (130, 100, 180)


def test_personalities():
    assert MutationType.FIRE.personality == "Passionate and intense"
    assert MutationType.WATER.personality == "Fluid, patient, like the tide"
    assert MutationType.AIR.personality == "Light and playful"
    assert MutationType.EARTH.personality == "Steadfast and immovable"
    assert MutationType.MUTA.personality == "Broken, unhinged, and grotesque"
    assert MutationType.TECH.personality == "Calculated and precise, like a machine"
    assert MutationType.COSM.personality == "Detached and ethereal, cosmic and mystical"
    assert MutationType.SHAD.personality == "Hollow and deathly, nightmarish"


# Cycle 1: FIRE > AIR > EARTH > WATER > FIRE
def test_fire_beats_air():
    assert get_type_effectiveness(MutationType.FIRE, MutationType.AIR) == 1.5


def test_air_beats_earth():
    assert get_type_effectiveness(MutationType.AIR, MutationType.EARTH) == 1.5


def test_earth_beats_water():
    assert get_type_effectiveness(MutationType.EARTH, MutationType.WATER) == 1.5


def test_water_beats_fire():
    assert get_type_effectiveness(MutationType.WATER, MutationType.FIRE) == 1.5


# Reverse of super effective is resisted (cycle 1)
def test_air_resists_fire():
    assert get_type_effectiveness(MutationType.AIR, MutationType.FIRE) == 0.75


def test_earth_resists_air():
    assert get_type_effectiveness(MutationType.EARTH, MutationType.AIR) == 0.75


def test_water_resists_earth():
    assert get_type_effectiveness(MutationType.WATER, MutationType.EARTH) == 0.75


def test_fire_resists_water():
    assert get_type_effectiveness(MutationType.FIRE, MutationType.WATER) == 0.75


# Cycle 2: TECH > MUTA > COSM > SHAD > TECH
def test_tech_beats_muta():
    assert get_type_effectiveness(MutationType.TECH, MutationType.MUTA) == 1.5


def test_muta_beats_cosm():
    assert get_type_effectiveness(MutationType.MUTA, MutationType.COSM) == 1.5


def test_cosm_beats_shad():
    assert get_type_effectiveness(MutationType.COSM, MutationType.SHAD) == 1.5


def test_shad_beats_tech():
    assert get_type_effectiveness(MutationType.SHAD, MutationType.TECH) == 1.5


# Reverse resisted (cycle 2)
def test_muta_resists_tech():
    assert get_type_effectiveness(MutationType.MUTA, MutationType.TECH) == 0.75


def test_cosm_resists_muta():
    assert get_type_effectiveness(MutationType.COSM, MutationType.MUTA) == 0.75


def test_shad_resists_cosm():
    assert get_type_effectiveness(MutationType.SHAD, MutationType.COSM) == 0.75


def test_tech_resists_shad():
    assert get_type_effectiveness(MutationType.TECH, MutationType.SHAD) == 0.75


# Neutral: cross-group matchups
def test_fire_vs_tech_neutral():
    assert get_type_effectiveness(MutationType.FIRE, MutationType.TECH) == 1.0


def test_water_vs_cosm_neutral():
    assert get_type_effectiveness(MutationType.WATER, MutationType.COSM) == 1.0


def test_earth_vs_shad_neutral():
    assert get_type_effectiveness(MutationType.EARTH, MutationType.SHAD) == 1.0


def test_air_vs_muta_neutral():
    assert get_type_effectiveness(MutationType.AIR, MutationType.MUTA) == 1.0


# Same type is neutral
def test_fire_vs_fire_neutral():
    assert get_type_effectiveness(MutationType.FIRE, MutationType.FIRE) == 1.0


def test_tech_vs_tech_neutral():
    assert get_type_effectiveness(MutationType.TECH, MutationType.TECH) == 1.0
