"""Future Edge scoring engine.

Everything here is plain, explainable arithmetic – no black box – so any team
member can explain every number to the judges.

Edge Score (0-100) for a person and a role, at year t and scenario s:

    Edge = 100 * (ai_adjusted_fit(t, s) / BEST_FIT)
               * (W_BASE + W_HUMAN * human_skills + W_RARITY * rarity)

* ai_adjusted_fit – the role's skills you have, weighted by importance, where
                    each skill only counts for the part AI CANNOT do at year t.
                    sum(weight * your_level * (1 - AI_exposure(t))) / sum(weight)
                    -> roles whose core work AI is taking over give little edge,
                       and the score drops over time as AI improves.
* BEST_FIT        – fit of a perfect candidate for the most AI-proof role in
                    our catalog today, so 100 = "has everything, in the safest role"
* human_skills    – judgment + responsibility (Edge Assessment, 0-1)
* rarity          – how unusual the person's skill mix is (0-1)
  Human skills and rarity act as a multiplier (0.6x to 1.0x): they make every
  role's fit count for more, which is the "what makes you unique" layer.

We also show the plain skill match (no AI adjustment) for the skills gap.

How exposure grows over time (the link to the trend layer):
    rate     = clamp(RATE_K * research_growth * scenario_multiplier * ai_sensitivity, 0, RATE_CAP)
    exposure(t) = min(0.95, base + (1 - base) * rate * t)
i.e. every year AI closes `rate` of the remaining gap; faster arXiv research
growth in that area -> faster closing. Change the trend data and the forecast
changes.
"""

W_BASE, W_HUMAN, W_RARITY = 0.60, 0.25, 0.15
RATE_K = 0.15
RATE_CAP = 0.30
YEARS = [0, 1, 2, 3]
SCENARIOS = {
    "moderate": {"label": "Moderate AI disruption", "multiplier": 1.0},
    "fast": {"label": "Fast AI disruption", "multiplier": 2.0},
}
HUMAN_SKILLS = ("critical_thinking", "ownership")
DEFAULT_HUMAN = 0.3      # used when the assessment has not been taken
STEP_BOOST = 0.3         # proficiency gained by completing one pathway step
HAVE_THRESHOLD = 0.3     # proficiency at which a skill counts as "have"
JOB_READY = 0.7
AT_RISK_EXPOSURE = 0.5   # a role is "at risk" if AI can do half of its weighted work by year 3          # proficiency at which a skill gets full credit (and leaves the gap list)
CATEGORIES = ("technical", "data", "domain", "human")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------- trends
def signal_growth(trends, signal_id):
    sig = trends.get("signals", {}).get(signal_id)
    return sig["growth"] if sig and sig.get("growth") is not None else 0.0


def exposure(skill, year, scenario, trends):
    g = max(0.0, signal_growth(trends, skill["signal"]))
    mult = SCENARIOS[scenario]["multiplier"]
    rate = clamp(RATE_K * g * mult * skill["ai_sensitivity"], 0.0, RATE_CAP)
    base = skill["base_exposure"]
    return min(0.95, base + (1 - base) * rate * year)


def skill_outlook(skill, scenario, trends, n_roles_using, n_roles):
    """rising / holding / fading label for one skill over 3 years."""
    e0 = exposure(skill, 0, scenario, trends)
    e3 = exposure(skill, 3, scenario, trends)
    demand = n_roles_using / n_roles
    if e3 - e0 >= 0.15 or e3 >= 0.7:
        status = "fading"
    elif e3 < 0.3 and demand >= 0.2:
        status = "rising"
    else:
        status = "holding"
    return {"status": status, "exposure_now": round(e0, 2), "exposure_y3": round(e3, 2)}


# ---------------------------------------------------------------- profile
def effective_skills(profile_skills, assessment=None):
    """Merge CV skills with assessment results (assessment wins for human skills)."""
    skills = dict(profile_skills)
    if assessment:
        if assessment.get("judgment") is not None:
            skills["critical_thinking"] = assessment["judgment"]
        if assessment.get("responsibility") is not None:
            skills["ownership"] = assessment["responsibility"]
    return skills


def score_assessment(questions, answers):
    """answers: {question_id: option_index}. Returns judgment & responsibility in 0-1."""
    j = r = n = 0
    for q in questions:
        idx = answers.get(q["id"])
        if idx is None or not (0 <= idx < len(q["options"])):
            continue
        opt = q["options"][idx]
        j += opt["judgment"]
        r += opt["responsibility"]
        n += 1
    if n == 0:
        return {"judgment": None, "responsibility": None, "answered": 0}
    return {"judgment": round(j / (3 * n), 2), "responsibility": round(r / (3 * n), 2), "answered": n}


# ---------------------------------------------------------------- components
def role_usage(roles):
    usage = {}
    for r in roles.values():
        for s in r["skills"]:
            usage[s] = usage.get(s, 0) + 1
    return usage


def credit(level):
    """0.7 (job-ready) or above = full credit."""
    return min(1.0, level / JOB_READY)


def match_score(role, skills):
    total = sum(role["skills"].values())
    got = sum(w * credit(skills.get(s, 0.0)) for s, w in role["skills"].items())
    return got / total if total else 0.0


def ai_adjusted_fit(role, skills, catalog_skills, year, scenario, trends):
    total = sum(role["skills"].values())
    got = 0.0
    for s, w in role["skills"].items():
        p = skills.get(s, 0.0)
        if p > 0 and s in catalog_skills:
            got += w * credit(p) * (1 - exposure(catalog_skills[s], year, scenario, trends))
    return got / total if total else 0.0


def best_fit(data):
    """Fit of a perfect candidate (all skills at level 1) for the most AI-proof role, at year 0."""
    full = {s: 1.0 for s in data["skills"]}
    return max(ai_adjusted_fit(r, full, data["skills"], 0, "moderate", data["trends"]) for r in data["roles"].values()) or 1.0


def rarity_score(skills, catalog_skills, usage, n_roles):
    have = [s for s, p in skills.items() if p >= HAVE_THRESHOLD and s in catalog_skills]
    if not have:
        return 0.0, []
    rar = [1 - usage.get(s, 0) / n_roles for s in have]
    cats = {catalog_skills[s]["category"] for s in have}
    diversity = len(cats) / len(CATEGORIES)
    return 0.5 * (sum(rar) / len(rar)) + 0.5 * diversity, sorted(cats)


def human_score(skills, assessed):
    vals = [credit(skills.get(s, DEFAULT_HUMAN if not assessed else 0.0)) for s in HUMAN_SKILLS]
    return sum(vals) / len(vals)


# ---------------------------------------------------------------- main API
def edge_for_role(role, skills, data, scenario, assessed):
    cat = data["skills"]
    trends = data["trends"]
    usage = role_usage(data["roles"])
    n_roles = len(data["roles"])
    match = match_score(role, skills)
    rarity, cats = rarity_score(skills, cat, usage, n_roles)
    human = human_score(skills, assessed)
    best = best_fit(data)
    multiplier = W_BASE + W_HUMAN * human + W_RARITY * rarity
    timeline = []
    for t in YEARS:
        fit = ai_adjusted_fit(role, skills, cat, t, scenario, trends)
        edge = 100 * (fit / best) * multiplier
        timeline.append({"year": t, "edge": round(edge, 1), "fit": round(fit, 3)})

    gap = []
    for s, w in sorted(role["skills"].items(), key=lambda kv: -kv[1]):
        p = skills.get(s, 0.0)
        if p < JOB_READY:
            gap.append({"skill": s, "name": cat[s]["name"], "weight": w, "have": round(p, 2)})

    have_n = sum(1 for s in role["skills"] if skills.get(s, 0) >= HAVE_THRESHOLD)
    role_exposure_y3 = sum(w * exposure(cat[s], YEARS[-1], scenario, trends) for s, w in role["skills"].items()) / sum(role["skills"].values())
    return {
        "role_id": role["id"],
        "title": role["title"],
        "field": role["field"],
        "match": round(match, 3),
        "rarity": round(rarity, 3),
        "human": round(human, 3),
        "multiplier": round(multiplier, 3),
        "timeline": timeline,
        "edge_now": timeline[0]["edge"],
        "edge_y3": timeline[-1]["edge"],
        "gap": gap,
        "sdgs": role["sdgs"],
        "role_ai_exposure_y3": round(role_exposure_y3, 2),
        "at_risk": role_exposure_y3 >= AT_RISK_EXPOSURE,
        "explain": {
            "match": f"You have {have_n} of {len(role['skills'])} skills this role needs (weighted by importance): {round(match * 100)}%.",
            "fit": f"Counting only the part of your skills AI can't do, you cover {round(timeline[0]['fit'] * 100)}% of this role today and {round(timeline[-1]['fit'] * 100)}% in year 3 ({SCENARIOS[scenario]['label'].lower()}).",
            "rarity": f"Your skills cover {len(cats)} of 4 skill types ({', '.join(cats) or 'none'}), which makes your mix {'rare' if rarity >= 0.6 else 'fairly common' if rarity >= 0.4 else 'common'}.",
            "human": "Judgment & responsibility from your Edge Assessment." if assessed else "Assessment not taken yet – using a default estimate.",
            "multiplier": f"Your human skills and rare mix multiply your fit by {multiplier:.2f}x (range 0.60x-1.00x).",
            "formula": "Edge = AI-adjusted fit (vs. best possible) x uniqueness multiplier (human skills + rarity).",
        },
    }


def forecast(profile_skills, data, scenario="moderate", assessment=None, goal_role=None, completed=()):
    assessed = bool(assessment and assessment.get("judgment") is not None)
    skills = apply_completed(effective_skills(profile_skills, assessment), completed, data["catalog"])
    roles = [edge_for_role(r, skills, data, scenario, assessed) for r in data["roles"].values()]
    roles.sort(key=lambda r: (r["role_id"] != goal_role, -r["edge_y3"]))

    usage = role_usage(data["roles"])
    n_roles = len(data["roles"])
    trends = data["trends"]
    skill_rows = []
    for s, p in sorted(skills.items(), key=lambda kv: -kv[1]):
        if s not in data["skills"] or p <= 0:
            continue
        sk = data["skills"][s]
        sig = trends.get("signals", {}).get(sk["signal"], {})
        out = skill_outlook(sk, scenario, trends, usage.get(s, 0), n_roles)
        skill_rows.append({
            "skill": s, "name": sk["name"], "category": sk["category"], "level": round(p, 2),
            **out,
            "signal": {"label": sig.get("label", sk["signal"]), "growth": sig.get("growth")},
            "sdgs": sk["sdgs"],
        })
    return {
        "scenario": scenario,
        "scenario_label": SCENARIOS[scenario]["label"],
        "is_estimate": True,
        "roles": roles,
        "skills": skill_rows,
        "trend_source": {
            "source": trends.get("source"),
            "fetched_at": trends.get("fetched_at"),
            "is_sample": trends.get("is_sample", False),
        },
        "exposure_source": data["skills_meta"].get("exposure_source"),
    }


def one_move_and_pathway(profile_skills, role_id, data, scenario="moderate", assessment=None,
                         completed=(), hours_per_week=6, max_steps=6):
    assessed = bool(assessment and assessment.get("judgment") is not None)
    skills = apply_completed(effective_skills(profile_skills, assessment), completed, data["catalog"])
    role = data["roles"][role_id]
    base = edge_for_role(role, skills, data, scenario, assessed)["edge_y3"]

    # Try improving each gap skill (+ human skills) and measure the year-3 Edge gain.
    candidates = {s for s in role["skills"] if skills.get(s, 0) < JOB_READY}
    candidates |= {s for s in HUMAN_SKILLS if skills.get(s, 0) < JOB_READY}
    gains = []
    for s in candidates:
        trial = dict(skills)
        trial[s] = min(1.0, trial.get(s, 0) + STEP_BOOST)
        new = edge_for_role(role, trial, data, scenario, assessed or s in HUMAN_SKILLS)["edge_y3"]
        gains.append((new - base, s))
    gains.sort(reverse=True)

    steps, used = [], set(completed)
    for gain, s in gains:
        if len(steps) >= max_steps or gain <= 0:
            break
        options = [i for i in data["catalog"] if s in i["skills"] and i["id"] not in used]
        # prefer a short course for knowledge, and a project/experience for proof
        options.sort(key=lambda i: (i["type"] != "course", i["hours"]))
        picks = options[:1] + [i for i in options if i["type"] != "course"][:1]
        for item in picks:
            if item["id"] in used or len(steps) >= max_steps:
                continue
            used.add(item["id"])
            steps.append({
                **item,
                "target_skill": s,
                "target_skill_name": data["skills"][s]["name"],
                "edge_gain": round(gain, 1),
                "weeks": round(item["hours"] / hours_per_week, 1),
                "sdgs": sorted(set(["4.4"] + (["4.3"] if item["cost"].startswith("free") else []) + data["skills"][s]["sdgs"])),
            })

    one_move = None
    if gains and gains[0][0] > 0:
        g, s = gains[0]
        one_move = {
            "skill": s,
            "name": data["skills"][s]["name"],
            "edge_gain": round(g, 1),
            "explain": f"Improving {data['skills'][s]['name']} raises your year-3 Edge Score for {role['title']} by about {round(g, 1)} points – more than any other single skill.",
        }
    return {
        "role_id": role_id,
        "role_title": role["title"],
        "scenario": scenario,
        "edge_y3": base,
        "one_move": one_move,
        "steps": steps,
        "total_hours": sum(s["hours"] for s in steps),
        "total_weeks": round(sum(s["hours"] for s in steps) / hours_per_week, 1),
        "hours_per_week": hours_per_week,
        "is_estimate": True,
    }


def apply_completed(skills, completed, catalog):
    """Each completed pathway step raises the skills it teaches by STEP_BOOST."""
    skills = dict(skills)
    by_id = {i["id"]: i for i in catalog}
    for cid in completed:
        item = by_id.get(cid)
        if not item:
            continue
        for s in item["skills"]:
            skills[s] = min(1.0, skills.get(s, 0) + STEP_BOOST)
    return skills
