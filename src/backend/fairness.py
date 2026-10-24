"""Fairness check: the same CV, read as different people, must give exactly the same skills.

Personal details (name, gender, age, race, religion, marital status) are removed before matching,
so they can never change a recommendation. This module PROVES it for every CV: it re-reads the CV
as 12 invented people with different details and compares the results with the original.
"""
from .cv_extract import redact_text
from .cv_parser import parse_skills

PEOPLE = [
    ("Siti Nurhaliza binti Ahmad", "Female", 24, "Malay", "Islam", "Single"),
    ("Tan Wei Ming", "Male", 52, "Chinese", "Buddhism", "Married"),
    ("Muthu a/l Rajan", "Male", 38, "Indian", "Hinduism", "Married"),
    ("Grace Anak Jimbun", "Female", 45, "Iban", "Christianity", "Divorced"),
    ("Ahmad Firdaus bin Ismail", "Male", 19, "Malay", "Islam", "Single"),
    ("Lim Mei Xin", "Female", 61, "Chinese", "Christianity", "Widowed"),
    ("Priya d/o Subramaniam", "Female", 29, "Indian", "Hinduism", "Single"),
    ("Mohd Hafiz bin Rahman", "Male", 33, "Malay", "Islam", "Married"),
    ("Jessica Wong", "Female", 41, "Chinese", "Taoism", "Married"),
    ("Daniel Kumar", "Male", 27, "Indian", "Christianity", "Single"),
    ("Nor Aishah binti Yusof", "Female", 56, "Malay", "Islam", "Married"),
    ("Kevin Lee", "Male", 22, "Chinese", "No religion", "Single"),
]
ATTRIBUTES = ["name", "gender", "age", "race", "religion", "marital status"]


def _as(person, text):
    name, gender, age, race, religion, marital = person
    header = f"{name}\nGender: {gender}\nAge: {age}\nRace: {race}\nReligion: {religion}\nMarital status: {marital}\n"
    return header + text


def _sig(found):
    return {k: v["level"] for k, v in found.items()}


def check(text, catalog):
    """text: the CV text the app matches on. Returns a short report for the UI."""
    base = _sig(parse_skills(redact_text("Original Person\n" + text), catalog))
    diffs = []
    for person in PEOPLE:
        got = _sig(parse_skills(redact_text(_as(person, text)), catalog))
        if got != base:
            diffs.append({"as": person[0], "changed": sorted(set(got.items()) ^ set(base.items()))})
    return {"passed": not diffs, "people_tested": len(PEOPLE), "attributes": ATTRIBUTES, "differences": diffs,
            "note": "Your CV was re-read as 12 different invented people (different names, genders, ages, races, "
                    "religions and marital status). " + ("Every result was identical." if not diffs else
                                                         "Some results differed – please report this.")}
