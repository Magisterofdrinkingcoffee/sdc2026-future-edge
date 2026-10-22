"""Future Edge scoring engine.

Everything here is plain, explainable arithmetic – no black box – so any team
member can explain every number to the judges.

Edge Score (0-100) for a person and a role, at year t and scenario s:

    Edge = 100 * (ai_adjusted_fit(t, s) / BEST_FIT)
               * (W_BASE + W_HUMAN * human_skills + W_RARITY * rarity)
               * job_market(t) * core_gate                      (capped at 100)

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
* core_gate       – 0.5 + 0.5 * your level in the role's CORE specialist skills
                    (weight 3, not human skills). Soft skills alone can't make
                    you a doctor: no core skills -> score halved.
* job_market(t)   – REAL demand data: WEF Future of Jobs 2025 projected net
                    job growth 2025-2030 for the role (Malaysia figure when WEF
                    has one, else global), spread evenly over 5 years:
                    1 + growth% / 100 * t / 5, capped to 0.75x-1.25x.
                    Roles WEF only lists as growing/declining get 1.0x (neutral).

We also show the plain skill match (no AI adjustment) for the skills gap.

How much AI can do a skill (Model 1 + the trend layer):
    Model 1 (exposure_model.py, trained on 19,265 human-rated O*NET tasks) reads the skill's
    task description - and, if available, YOUR OWN CV sentence for that skill - and returns
        E1 = chance an AI chatbot alone can halve the time
        E2 = chance AI can do it once extra tools are built on top
    exposure(t) = E1 + E2 * tools(t)
    tools(t)    = min(1, TOOLS_NOW + t * TOOLS_SPEED[scenario] * (1 + arXiv research growth))
i.e. chatbot-level exposure counts today; tool-level exposure arrives over the next years,
faster in the "fast" scenario and in areas where AI research is growing faster.
Change the trend data and the forecast changes.
"""

W_BASE, W_HUMAN, W_RARITY = 0.60, 0.25, 0.15
TOOLS_NOW = 0.25           # share of "AI + tools" (E2) exposure already real today
TOOLS_SPEED = {"moderate": 0.08, "fast": 0.16}   # per year, before the research-growth boost
PERSONAL_WEIGHT = 0.5      # how much your own CV sentence counts vs. the general skill description
MIN_KNOWN_WORDS = 3        # the model must recognise at least this many words/word pairs in your sentence
YEARS = [0, 1, 2, 3]
SCENARIOS = {
    "moderate": {"label": "Moderate AI disruption", "tools_speed": TOOLS_SPEED["moderate"]},
    "fast": {"label": "Fast AI disruption", "tools_speed": TOOLS_SPEED["fast"]},
}
HUMAN_SKILLS = ("critical_thinking", "ownership")
DEFAULT_HUMAN = 0.3      # used when the assessment has not been taken
STEP_BOOST = 0.3         # proficiency gained by completing one pathway step
HAVE_THRESHOLD = 0.3     # proficiency at which a skill counts as "have"
JOB_READY = 0.7
AT_RISK_EXPOSURE = 0.5
MARKET_CAP = (0.75, 1.25)   # a role is "at risk" if AI can do half of its weighted work by year 3          # proficiency at which a skill gets full credit (and leaves the gap list)
CATEGORIES = ("technical", "data", "domain", "human")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


# ---------------------------------------------------------------- trends
def signal_growth(trends, signal_id, key="growth"):
    """Model 2's yearly research growth for a signal; key = growth | growth_low | growth_high (80% range)."""
    sig = trends.get("signals", {}).get(signal_id)
    if not sig:
        return 0.0
    value = sig.get(key, sig.get("growth"))
    return value if value is not None else 0.0


def tools(year, scenario, growth):
    return min(1.0, TOOLS_NOW + year * TOOLS_SPEED[scenario] * (1 + max(0.0, growth)))


def exposure(skill, year, scenario, trends, key="growth"):
    """Share of this skill's work AI can do in `year` (Model 1 output + Model 2 trend)."""
    m = skill["model"]
    return min(0.98, m["E1"] + m["E2"] * tools(year, scenario, signal_growth(trends, skill["signal"], key)))


def with_personal_exposure(data, evidence):
    """Copy of data where each skill's Model 1 reading blends in the user's own CV sentence."""
    if not evidence:
        return data
    from .exposure_model import predict
    skills = dict(data["skills"])
    for sid, sentence in evidence.items():
        if sid not in skills or not sentence or not sentence.strip():
            continue
        if skills[sid]["category"] == "human":
            continue  # "Responsible for data entry..." describes the context, not the human skill itself
        general, mine = skills[sid]["model"], predict(sentence)
        if mine["known_words"] < MIN_KNOWN_WORDS:
            continue  # e.g. a bare list "Python, SQL, Git": too little for the model to read
        blended = {k: round((1 - PERSONAL_WEIGHT) * general[k] + PERSONAL_WEIGHT * mine[k], 4) for k in ("E0", "E1", "E2")}
        skills[sid] = {**skills[sid], "model": {**blended, "personal": True, "sentence": sentence,
                                                "sentence_reading": {k: mine[k] for k in ("E0", "E1", "E2")},
                                                "top_words": mine["top_words"]}}
    return {**data, "skills": skills}


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
    return {"status": status, "exposure_now": round(e0, 2), "exposure_y3": round(e3, 2),
            "exposure_y3_range": [round(exposure(skill, 3, scenario, trends, "growth_low"), 2),
                                  round(exposure(skill, 3, scenario, trends, "growth_high"), 2)]}


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


def ai_adjusted_fit(role, skills, catalog_skills, year, scenario, trends, key="growth"):
    total = sum(role["skills"].values())
    got = 0.0
    for s, w in role["skills"].items():
        p = skills.get(s, 0.0)
        if p > 0 and s in catalog_skills:
            got += w * credit(p) * (1 - exposure(catalog_skills[s], year, scenario, trends, key))
    return got / total if total else 0.0


def market_growth(role):
    """WEF net growth 2025-2030 in % (Malaysia first), or None if WEF gives only a direction."""
    o = role.get("outlook") or {}
    return o.get("malaysia_net_growth_2030", o.get("net_growth_2030"))


def job_market(role, year):
    g = market_growth(role)
    if g is None:
        return 1.0
    return clamp(1 + g / 100 * year / 5, *MARKET_CAP)


def core_gate(role, skills, catalog_skills):
    core = [s for s, w in role["skills"].items() if w == 3 and catalog_skills[s]["category"] != "human"]
    if not core:
        return 1.0, []
    have = sum(credit(skills.get(s, 0.0)) for s in core) / len(core)
    return 0.5 + 0.5 * have, core


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
def edge_for_role(role, skills, data, scenario, assessed, human_bounds=None):
    """human_bounds: {"low": {...}, "high": {...}} skill overrides from Model 3's range (optional)."""
    cat = data["skills"]
    trends = data["trends"]
    usage = role_usage(data["roles"])
    n_roles = len(data["roles"])
    match = match_score(role, skills)
    rarity, cats = rarity_score(skills, cat, usage, n_roles)
    human = human_score(skills, assessed)
    best = best_fit(data)
    multiplier = W_BASE + W_HUMAN * human + W_RARITY * rarity
    gate, core = core_gate(role, skills, cat)
    def series(sk, mult, key):
        return [min(100.0, 100 * (ai_adjusted_fit(role, sk, cat, t, scenario, trends, key) / best) * mult
                    * job_market(role, t) * gate) for t in YEARS]

    # DATA FUSION RANGE: pessimistic = Model 2's upper research growth (AI arrives faster) + Model 3's
    # lower human-skill bound; optimistic = the opposite. Mid = central estimates.
    def variant(bound):
        if not human_bounds or bound not in human_bounds:
            return skills, multiplier
        sk = {**skills, **human_bounds[bound]}
        return sk, W_BASE + W_HUMAN * human_score(sk, assessed) + W_RARITY * rarity
    lo_sk, lo_mult = variant("low")
    hi_sk, hi_mult = variant("high")
    lows, highs = series(lo_sk, lo_mult, "growth_high"), series(hi_sk, hi_mult, "growth_low")
    timeline = []
    for i, t in enumerate(YEARS):
        fit = ai_adjusted_fit(role, skills, cat, t, scenario, trends)
        market = job_market(role, t)
        edge = min(100.0, 100 * (fit / best) * multiplier * market * gate)
        timeline.append({"year": t, "edge": round(edge, 1), "low": round(min(lows[i], edge), 1),
                         "high": round(max(highs[i], edge), 1), "fit": round(fit, 3), "market": round(market, 3)})

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
        "edge_y3_range": [timeline[-1]["low"], timeline[-1]["high"]],
        "gap": gap,
        "sdgs": role["sdgs"],
        "role_ai_exposure_y3": round(role_exposure_y3, 2),
        "at_risk": _at_risk(role, role_exposure_y3),
        "core_gate": round(gate, 2),
        "description": role.get("description"),
        "status": role.get("status"),
        "ai_tools": role.get("ai_tools", []),
        "outlook": role.get("outlook"),
        "wage": role.get("wage"),
        "mycol": role.get("mycol"),
        "explain": {
            "match": f"You have {have_n} of {len(role['skills'])} skills this role needs (weighted by importance): {round(match * 100)}%.",
            "fit": f"Counting only the part of your skills AI can't do, you cover {round(timeline[0]['fit'] * 100)}% of this role today and {round(timeline[-1]['fit'] * 100)}% in year 3 ({SCENARIOS[scenario]['label'].lower()}).",
            "rarity": f"Your skills cover {len(cats)} of 4 skill types ({', '.join(cats) or 'none'}), which makes your mix {'rare' if rarity >= 0.6 else 'fairly common' if rarity >= 0.4 else 'common'}.",
            "human": "Judgment & responsibility from your Edge Assessment." if assessed else "Assessment not taken yet – using a default estimate.",
            "multiplier": f"Your human skills and rare mix multiply your fit by {multiplier:.2f}x (range 0.60x-1.00x).",
            "market": _market_text(role, timeline[-1]["market"]),
            "core": (f"Core specialist skills for this role: {', '.join(cat[c]['name'] for c in core)}. Your level there gives x{gate:.2f}."
                     if core else "This role has no single core specialist skill."),
            "range": f"Range in year 3: {timeline[-1]['low']:.0f}-{timeline[-1]['high']:.0f}. Low end = AI research grows at the top of Model 2's 80% range and your Catch-the-AI score at the bottom of its range; high end = the opposite.",
            "formula": "Edge = AI-adjusted fit (Model 1 + Model 2) x uniqueness (Model 3 + rare skill mix) x job market (WEF) x core-skill check.",
        },
    }


def _at_risk(role, exposure_y3):
    """Real WEF data wins over our exposure estimate."""
    o = role.get("outlook") or {}
    g = market_growth(role)
    if g is not None:
        return g <= -10
    if o.get("direction"):
        return o["direction"] == "declining"
    return exposure_y3 >= AT_RISK_EXPOSURE


def _market_text(role, m3):
    o = role.get("outlook") or {}
    g = market_growth(role)
    if g is not None:
        where = "in Malaysia" if "malaysia_net_growth_2030" in o else "worldwide"
        return f"Job market: employers expect {'+' if g >= 0 else ''}{g}% net jobs for {o['wef_role']} {where} by 2030 ({o.get('malaysia_source') or o['source']}), so x{m3:.2f} by year 3."
    if o.get("direction"):
        return f"Job market: WEF lists {o['wef_role']} among the fastest-{'growing' if o['direction'] == 'growing' else 'declining'} jobs ({o['source']}), but gives no exact figure, so we keep it neutral (x1.00)."
    return "Job market: no WEF figure for this role, so we keep it neutral (x1.00)."


def human_bounds(assessment):
    """Model 3 range -> skill overrides for the low/high Edge (None if no range)."""
    if not assessment or not assessment.get("judgment_range") or not assessment.get("responsibility_range"):
        return None
    jr, rr = assessment["judgment_range"], assessment["responsibility_range"]
    return {"low": {"critical_thinking": jr[0], "ownership": rr[0]},
            "high": {"critical_thinking": jr[1], "ownership": rr[1]}}


def forecast(profile_skills, data, scenario="moderate", assessment=None, goal_role=None, completed=(), evidence=None):
    data = with_personal_exposure(data, evidence)
    assessed = bool(assessment and assessment.get("judgment") is not None)
    skills = apply_completed(effective_skills(profile_skills, assessment), completed, data["catalog"])
    bounds = human_bounds(assessment)
    roles = [edge_for_role(r, skills, data, scenario, assessed, bounds) for r in data["roles"].values()]
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
            "signal": {"label": sig.get("label", sk["signal"]), "growth": sig.get("growth"),
                       "growth_low": sig.get("growth_low"), "growth_high": sig.get("growth_high")},
            "sdgs": sk["sdgs"],
            "model": {**sk["model"], "task": sk["task"]},
        })
    return {
        "scenario": scenario,
        "scenario_label": SCENARIOS[scenario]["label"],
        "is_estimate": True,
        "roles": roles,
        "skills": skill_rows,
        "trend_source": {
            "model": trends.get("model"),
            "backtest": trends.get("backtest"),
            "source": trends.get("source"),
            "fetched_at": trends.get("fetched_at"),
            "is_sample": trends.get("is_sample", False),
        },
        "exposure_source": data["skills_meta"].get("exposure_source"),
        "model": _model_card(),
    }


def _model_card():
    from .exposure_model import info
    i = info()
    m = i["metrics"]
    return {"name": i["name"], "data": i["data"], "class_meaning": i["class_meaning"],
            "accuracy": m["accuracy"], "baseline_accuracy": m["baseline_accuracy"], "macro_f1": m["macro_f1"],
            "recall_per_class": m["recall_per_class"], "n_tasks": m["n_tasks"], "n_occupations": m["n_occupations"],
            "evaluation": m["evaluation"]}


def one_move_and_pathway(profile_skills, role_id, data, scenario="moderate", assessment=None,
                         completed=(), hours_per_week=6, max_steps=6, evidence=None):
    data = with_personal_exposure(data, evidence)
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
