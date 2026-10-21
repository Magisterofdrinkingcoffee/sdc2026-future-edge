"""Build src/backend/data/roles.json from the team dataset + official sources.

    python -m tools.build_roles

Inputs
  src/database/gemini-code-1792564378296.csv   team role dataset (25 roles; titles/skills/SDGs, AI-assisted)
  src/database/wages_occupation.csv            DOSM median monthly wages by occupation group
  WEF Future of Jobs Report 2025 (src/database) growth figures, transcribed below WITH PAGE NUMBERS
  MyCOL 2024/2025 (src/database)               critical-occupation list, transcribed below with MASCO codes

What we deliberately DO NOT use from the team dataset
  moderate_ai_risk / fast_ai_risk / estimated_reskilling_hours / avg_salary_myr:
  these numbers are not in any of the cited sources, so they are not shown as facts.
  AI exposure is computed by our scoring engine instead, and labelled as an estimate.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src" / "database"
OUT = ROOT / "src" / "backend" / "data" / "roles.json"
WEF = "WEF Future of Jobs Report 2025"
WEF_FIG = f"{WEF}, Figures 2.2–2.3 (pp. 19–21)"

# ---------------------------------------------------------------------------
# Job-market outlook. net_growth = WEF projected net growth 2025–2030 (% of current
# jobs), "Global net growth" column of the profile tables. my_net_growth = Malaysia
# economy profile (p. 168). Roles with only a direction are in WEF Fig 2.2/2.3 lists.
# ---------------------------------------------------------------------------
WEF_OUTLOOK = {
    "ai_ml_specialist":        {"wef_role": "AI and Machine Learning Specialists", "net_growth": 82, "page": 112, "my_net_growth": 29},
    "renewable_energy_engineer": {"wef_role": "Renewable Energy Engineers", "net_growth": 38, "page": 254},
    "sustainability_specialist": {"wef_role": "Sustainability Specialists", "net_growth": 33, "page": 114},
    "big_data_specialist":     {"wef_role": "Big Data Specialists", "net_growth": 113, "page": 150},
    "av_ev_specialist":        {"wef_role": "Autonomous and Electric Vehicle Specialists", "net_growth": 48, "page": 280},
    "fintech_engineer":        {"wef_role": "FinTech Engineers", "direction": "growing", "page": 19},
    "environmental_engineer":  {"wef_role": "Environmental Engineers", "direction": "growing", "page": 19},
    "bi_analyst":              {"wef_role": "Business Intelligence Analysts", "net_growth": 18, "page": 116},
    "cybersecurity_specialist": {"wef_role": "Security Management Specialists", "direction": "growing", "page": 19},
    "digital_transformation_specialist": {"wef_role": "Digital Transformation Specialists", "net_growth": 35, "page": 144},
    "network_professional":    {"wef_role": "Database and Network Professionals", "direction": "growing", "page": 21},
    "operations_manager":      {"wef_role": "General and Operations Managers", "net_growth": 4, "page": 112},
    "civil_engineer":          {"wef_role": "Civil Engineers", "net_growth": 13, "page": 258},
    "supply_chain_specialist": {"wef_role": "Supply Chain and Logistics Specialists", "net_growth": 17, "page": 152, "my_net_growth": 12},
    "data_entry_clerk":        {"wef_role": "Data Entry Clerks", "net_growth": -26, "page": 112, "my_net_growth": -28},
    "admin_assistant":         {"wef_role": "Administrative Assistants and Executive Secretaries", "net_growth": -20, "page": 116, "my_net_growth": -17},
    "bookkeeping_clerk":       {"wef_role": "Accounting, Bookkeeping and Payroll Clerks", "net_growth": -18, "page": 114},
    "bank_teller":             {"wef_role": "Bank Tellers and Related Clerks", "direction": "declining", "page": 19},
    "postal_clerk":            {"wef_role": "Postal Service Clerks", "direction": "declining", "page": 19},
    # roles added by us (not in the team CSV), all present in WEF
    "software_developer":      {"wef_role": "Software and Applications Developers", "net_growth": 57, "page": 260},
    "data_analyst":            {"wef_role": "Data Analysts and Scientists", "net_growth": 41, "page": 112},
    "devops_engineer":         {"wef_role": "Devops Engineer", "direction": "growing", "page": 19},
    "iot_specialist":          {"wef_role": "Internet of Things Specialists", "direction": "growing", "page": 19},
    "electrical_engineer":     {"wef_role": "Electrotechnology Engineers", "net_growth": 15, "page": 134},
    "project_manager":         {"wef_role": "Project Managers", "net_growth": 17, "page": 142},
    "product_manager":         {"wef_role": "Product Managers", "direction": "growing", "page": 21},
    "customer_service_worker": {"wef_role": "Client Information and Customer Service Workers", "net_growth": -2, "page": 166},
}

# MyCOL 2024/2025 Table 7 (pp. 10 & 44): critical occupations, MASCO 4-digit codes
MYCOL = {
    "cybersecurity_specialist": ("2531", "Cyber Security Professionals"),
    "network_professional": ("2523", "Computer Network Professionals"),
    "mech_technician": ("3115", "Mechanical Engineering Technicians"),
    "finance_manager": ("1211", "Finance Managers"),
    "agri_rnd_executive": ("2426", "Research and Development Professionals"),
    "medical_specialist": ("2212", "Specialist Medical Practitioners"),
    "civil_engineer": ("2142", "Civil Engineers"),
    "safety_engineer": ("2263", "Environmental and Occupational Health and Hygiene Professionals"),
    "software_developer": ("2512", "Software Developers"),
    "data_analyst": ("2524", "Data Professionals"),
    "electrical_engineer": ("2151", "Electrical Engineers"),
    "electrical_technician": ("3113", "Electrical Engineering Technicians"),
}

# Group small sectors so the role picker stays readable
SECTOR = {"Automotive & Manufacturing": "Manufacturing", "Construction": "Engineering & Construction",
          "Agriculture": "Science, Health & Agriculture", "Healthcare": "Science, Health & Agriculture"}

# MASCO major group -> DOSM wages_occupation.csv group
GROUP_LABEL = {"managers": "Managers", "professionals": "Professionals", "technicians": "Technicians & associate professionals",
               "clerical": "Clerical support workers", "service_sales": "Service & sales workers"}

# Team CSV row -> our id, wage group, and skill weights in our catalog (1 = useful, 3 = core)
FROM_CSV = {
    "ROLE_001": ("ai_ml_specialist", "professionals", {"python": 3, "ml": 3, "deep_learning": 2, "statistics": 2, "llm_apps": 2, "mlops": 1, "ai_ethics": 1, "problem_framing": 2, "critical_thinking": 2}),
    "ROLE_002": ("renewable_energy_engineer", "professionals", {"renewable_energy": 3, "power_systems": 2, "project_management": 2, "data_analysis": 1, "problem_framing": 2, "communication": 1}),
    "ROLE_003": ("sustainability_specialist", "professionals", {"sustainability_esg": 3, "regulatory_compliance": 2, "data_analysis": 2, "communication": 2, "critical_thinking": 1}),
    "ROLE_004": ("big_data_specialist", "professionals", {"data_engineering": 3, "sql": 3, "python": 2, "cloud": 2, "problem_framing": 1}),
    "ROLE_005": ("av_ev_specialist", "professionals", {"ev_battery": 3, "embedded": 3, "circuit_design": 2, "iot": 1, "ml": 1, "problem_framing": 1}),
    "ROLE_006": ("fintech_engineer", "professionals", {"web_dev": 3, "cybersecurity": 2, "financial_analysis": 2, "cloud": 1, "basic_coding": 1, "problem_framing": 1}),
    "ROLE_007": ("environmental_engineer", "professionals", {"environmental_engineering": 3, "cad": 2, "data_analysis": 1, "regulatory_compliance": 1, "problem_framing": 2}),
    "ROLE_008": ("bi_analyst", "professionals", {"data_viz": 3, "sql": 3, "data_analysis": 2, "communication": 2, "excel_reporting": 1, "critical_thinking": 1}),
    "ROLE_009": ("cybersecurity_specialist", "professionals", {"cybersecurity": 3, "networking": 2, "cloud": 1, "critical_thinking": 2, "ownership": 2}),
    "ROLE_010": ("digital_transformation_specialist", "professionals", {"project_management": 3, "problem_framing": 3, "leadership": 2, "communication": 2, "cloud": 1, "llm_apps": 1}),
    "ROLE_011": ("network_professional", "professionals", {"networking": 3, "cybersecurity": 2, "cloud": 1, "ownership": 1}),
    "ROLE_012": ("qa_engineer", "professionals", {"quality_control": 3, "statistics": 2, "problem_framing": 2, "ownership": 2}),
    "ROLE_013": ("mech_technician", "technicians", {"mechanical_maintenance": 3, "plc": 1, "cad": 1, "ownership": 2}),
    "ROLE_014": ("finance_manager", "managers", {"financial_analysis": 3, "regulatory_compliance": 2, "leadership": 2, "communication": 2, "bookkeeping": 1}),
    "ROLE_015": ("agri_rnd_executive", "professionals", {"agronomy": 3, "lab_research": 3, "statistics": 2, "data_analysis": 1}),
    "ROLE_016": ("operations_manager", "managers", {"operations_mgmt": 3, "leadership": 3, "supply_chain": 1, "data_analysis": 1, "ownership": 2}),
    "ROLE_017": ("medical_specialist", "professionals", {"clinical_medicine": 3, "critical_thinking": 3, "communication": 2, "ownership": 3}),
    "ROLE_018": ("civil_engineer", "professionals", {"structural_design": 3, "cad": 2, "project_management": 2, "ownership": 1}),
    "ROLE_019": ("supply_chain_specialist", "professionals", {"supply_chain": 3, "data_analysis": 2, "excel_reporting": 1, "communication": 1}),
    "ROLE_020": ("safety_engineer", "professionals", {"ohs": 3, "critical_thinking": 2, "ownership": 3, "communication": 1}),
    "ROLE_021": ("data_entry_clerk", "clerical", {"data_entry": 3, "excel_reporting": 2, "ownership": 1}),
    "ROLE_022": ("admin_assistant", "clerical", {"scheduling_admin": 3, "communication": 2, "excel_reporting": 1, "data_entry": 1, "ownership": 1}),
    "ROLE_023": ("bookkeeping_clerk", "clerical", {"bookkeeping": 3, "excel_reporting": 2, "data_entry": 1}),
    "ROLE_024": ("bank_teller", "clerical", {"customer_service": 3, "bookkeeping": 1, "data_entry": 1, "communication": 1}),
    "ROLE_025": ("postal_clerk", "clerical", {"customer_service": 2, "supply_chain": 1, "data_entry": 2}),
}

# Roles we add so electrical/IT students and admin workers have realistic targets.
EXTRA = [
    {"id": "software_developer", "title": "Software and Applications Developer", "sector": "Digital & ICT", "wage_group": "professionals",
     "skills": {"web_dev": 3, "basic_coding": 2, "git": 2, "python": 1, "sql": 2, "cloud": 1, "problem_framing": 2},
     "description": "Designs, builds and maintains software applications and services.", "sdgs": {"9.c": "Builds digital services", "8.2": "Technological upgrading"}},
    {"id": "data_analyst", "title": "Data Analyst / Scientist", "sector": "Digital & ICT", "wage_group": "professionals",
     "skills": {"sql": 3, "data_analysis": 3, "data_viz": 2, "statistics": 2, "python": 2, "communication": 2, "critical_thinking": 2},
     "description": "Turns raw data into analysis and insights that guide decisions.", "sdgs": {"8.2": "Data-driven decisions raise productivity"}},
    {"id": "devops_engineer", "title": "DevOps / MLOps Engineer", "sector": "Digital & ICT", "wage_group": "professionals",
     "skills": {"mlops": 3, "cloud": 3, "python": 2, "git": 2, "networking": 1, "ownership": 2},
     "description": "Automates how software and AI models are built, deployed and kept running.", "sdgs": {"9.c": "Reliable digital infrastructure", "9.5": "Keeps AI systems running in production"}},
    {"id": "iot_specialist", "title": "IoT / Embedded Systems Specialist", "sector": "Digital & ICT", "wage_group": "professionals",
     "skills": {"embedded": 3, "iot": 3, "circuit_design": 2, "python": 1, "cloud": 1, "problem_framing": 2},
     "description": "Builds connected devices and sensor systems for factories, buildings and cities.", "sdgs": {"9.4": "Smart, efficient industrial systems", "11.6": "Sensing for cleaner cities"}},
    {"id": "electrical_engineer", "title": "Electrical Engineer (power & smart grids)", "sector": "Energy & Sustainability", "wage_group": "professionals",
     "skills": {"power_systems": 3, "circuit_design": 2, "iot": 1, "python": 1, "data_analysis": 1, "project_management": 1, "ownership": 2},
     "description": "Designs and operates power systems, from substations to smart grids.", "sdgs": {"7.1": "Reliable, modern electricity supply", "9.4": "Upgrades energy infrastructure"}},
    {"id": "electrical_technician", "title": "Electrical Engineering Technician", "sector": "Energy & Sustainability", "wage_group": "technicians",
     "skills": {"electrical_maintenance": 3, "plc": 2, "circuit_design": 1, "ohs": 1, "ownership": 2},
     "description": "Installs, tests and maintains electrical equipment and systems.", "sdgs": {"7.1": "Keeps energy services running", "8.8": "Safe working environments"}},
    {"id": "project_manager", "title": "Project Manager", "sector": "Services", "wage_group": "professionals",
     "skills": {"project_management": 3, "communication": 3, "leadership": 2, "ownership": 3, "scheduling_admin": 1, "problem_framing": 2},
     "description": "Plans and leads projects so teams deliver on time and on budget. A common next step for experienced admin staff.", "sdgs": {"8.5": "A decent-work growth path for admin and support staff", "8.2": "Coordinates teams adopting new technology"}},
    {"id": "product_manager", "title": "Product Manager", "sector": "Digital & ICT", "wage_group": "professionals",
     "skills": {"product_management": 3, "communication": 3, "problem_framing": 3, "data_analysis": 2, "leadership": 2, "llm_apps": 1, "ai_ethics": 1},
     "description": "Decides what a digital product should do and leads the team that builds it.", "sdgs": {"9.b": "Drives local technology innovation", "8.2": "Turns technology into productive products"}},
    {"id": "customer_service_worker", "title": "Customer Service Worker", "sector": "Services", "wage_group": "service_sales",
     "skills": {"customer_service": 3, "communication": 2, "data_entry": 1, "ownership": 1},
     "description": "Answers customer questions and solves problems by phone, chat or in person.", "sdgs": {"8.5": "Decent work – role changing fast with AI chatbots"}},
]


def dosm_wages():
    rows = list(csv.DictReader(open(DB / "wages_occupation.csv", encoding="utf-8")))
    latest = max(r["date"] for r in rows)
    return latest[:4], {r["occupation"]: int(r["wages_median"]) for r in rows if r["date"] == latest and r["sex"] == "both"}


def outlook(role_id):
    o = WEF_OUTLOOK.get(role_id)
    if not o:
        return {"source": None, "note": "Not covered by the WEF Future of Jobs 2025 survey."}
    out = {"wef_role": o["wef_role"], "net_growth_2030": o.get("net_growth"), "direction": o.get("direction")
           or ("growing" if o["net_growth"] > 0 else "declining" if o["net_growth"] < 0 else "stable"),
           "source": f"{WEF}, p. {o['page']}" if "net_growth" in o else WEF_FIG}
    if "my_net_growth" in o:
        out["malaysia_net_growth_2030"] = o["my_net_growth"]
        out["malaysia_source"] = f"{WEF}, Malaysia economy profile, p. 168"
    return out


def malaysia_facts(year, wages):
    lfs = list(csv.DictReader(open(DB / "lfs_month.csv", encoding="utf-8")))[-1]
    month = lfs["date"][:7]
    wef_my = f"{WEF}, Malaysia economy profile"
    return [
        {"id": "analytical", "value": "71%", "text": "of employers in Malaysia say analytical thinking is a core skill today (joint first on their list)",
         "source": f"{wef_my}, p. 168"},
        {"id": "ai_skills", "value": "96%", "text": "of employers in Malaysia expect AI and big data skills to be used more by 2030",
         "source": f"{wef_my}, p. 168"},
        {"id": "data_entry", "value": "−28%", "text": "net change expected in data entry clerk jobs in Malaysia by 2030",
         "source": f"{wef_my}, p. 168"},
        {"id": "ai_jobs", "value": "+29%", "text": "net growth expected in AI and machine learning specialist jobs in Malaysia by 2030",
         "source": f"{wef_my}, p. 168"},
        {"id": "human_tasks", "value": "47% → 33%", "text": "share of work tasks done mainly by people in Malaysia, today vs 2030",
         "source": f"{wef_my}, p. 169"},
        {"id": "unemployment", "value": f"{float(lfs['u_rate']):.1f}%", "text": f"unemployment rate in Malaysia ({month})",
         "source": f"DOSM Labour Force Survey, monthly ({month})"},
        {"id": "wage", "value": f"RM {wages['overall']:,}", "text": f"median monthly wage in Malaysia ({year})",
         "source": f"DOSM Salaries & Wages Survey ({year})"},
    ]


def main():
    year, wages = dosm_wages()
    facts = malaysia_facts(year, wages)
    (OUT.parent / "malaysia_facts.json").write_text(json.dumps({"_meta": {"description": "Real, cited facts shown in the app. Built by tools/build_roles.py."}, "facts": facts}, indent=2, ensure_ascii=False), encoding="utf-8")

    def wage(group):
        return {"group": GROUP_LABEL[group], "median_myr": wages[group], "year": int(year),
                "source": f"DOSM, Salaries & Wages Survey – median monthly wage by occupation group ({year})"}

    def extra_fields(rid, group):
        mc = MYCOL.get(rid)
        return {"outlook": outlook(rid), "wage": wage(group),
                "mycol": {"critical": True, "masco": mc[0], "name": mc[1], "source": "TalentCorp MyCOL 2024/2025, Table 7"} if mc else {"critical": False}}

    roles = []
    for r in csv.DictReader(open(DB / "gemini-code-1792564378296.csv", encoding="utf-8")):
        rid, group, skills = FROM_CSV[r["role_id"]]
        targets = [t.replace("SDG ", "") for t in r["sdg_tags"].split("|") if "." in t]
        roles.append({
            "id": rid, "title": r["role_title"], "field": SECTOR.get(r["sector"], r["sector"]), "status": r["role_status"],
            "description": r["role_description"], "skills": skills,
            "ai_tools": r["emerging_ai_skills"].split("|"),
            "sdgs": {t: r["sdg_impact_description"] for t in targets},
            "difficulty": r["skill_difficulty"], "dataset_id": r["role_id"],
            **extra_fields(rid, group),
        })
    for e in EXTRA:
        roles.append({"id": e["id"], "title": e["title"], "field": e["sector"], "status": None, "description": e["description"],
                      "skills": e["skills"], "ai_tools": [], "sdgs": e["sdgs"], "difficulty": None, "dataset_id": None,
                      **extra_fields(e["id"], e["wage_group"])})

    meta = {
        "description": "Future-role catalog. Built by tools/build_roles.py – edit that script, not this file.",
        "weights": "Skill weight for the role: 1 = useful, 2 = important, 3 = core.",
        "sources": {
            "roles": "Team dataset src/database/gemini-code-1792564378296.csv (AI-assisted) + 9 roles added by the team",
            "outlook": f"{WEF} – projected net job growth 2025–2030 (page numbers per role)",
            "critical": "TalentCorp MyMahir Malaysia Critical Occupations List (MyCOL) 2024/2025",
            "wages": "DOSM Salaries & Wages Survey via src/database/wages_occupation.csv",
        },
        "not_used": "AI-risk, reskilling-hours and salary-range columns of the team dataset (no verifiable source).",
    }
    OUT.write_text(json.dumps({"_meta": meta, "roles": roles}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(roles)} roles -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
