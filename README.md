# Future Edge

**SDC Hackathon 2026 · Domain 1 – Aiversecity Future-Ready Workforce**
SDG focus: 4.3, 4.4, 8.2, 8.5

Future Edge is a career forecast. It shows how AI will change the value of *your* skills over the next 3 years, and the **one move** that keeps you hard to replace. It combines your CV skills with your human strengths (judgment and responsibility) and live AI-trend data, then turns the result into a pathway of courses (knowledge), projects (proof) and experiences (personal skills). You can track that pathway over time.

> All scores are estimates to support the user's own decisions. They are never used for hiring decisions. The demo uses synthetic profiles only.

## User journey
1. **Profile:** pick a sample person or paste a CV. Skills are extracted against our catalog, and the user adjusts their levels.
2. **Edge Assessment:** 5 work scenarios estimate judgment and responsibility.
3. **Career forecast:** Future Edge Score per role for now through +3 years, in two scenarios (moderate vs fast AI disruption). Skills are labelled fading, holding or rising, with trend source and date.
4. **Pathway & progress:** One Move, then ordered steps with time estimates, sources and SDG tags. Ticking a step re-calculates the score.

## How this meets the 6 must-haves
| # | Must-have | Where |
|---|---|---|
| 1 | Skills profile intake | `ProfileStep.jsx`, `POST /api/profile/parse` |
| 2 | AI-trend signal layer (updatable, source + date shown) | `src/backend/trends.py` (arXiv API) → `data/trends.json`; *Refresh trend data* button; what-if sliders |
| 3 | Explainable role matching + skills gap | `scoring.edge_for_role` → `explain` texts, `gap` list |
| 4 | Personalised pathway (ordered, time, free/low-cost) | `scoring.one_move_and_pathway`; only items from `data/pathway_catalog.json` |
| 5 | SDG mapping per role and skill | `sdgs` in `roles.json` / `skills.json`, official targets in `sdgs.json` |
| 6 | Uncertainty (>1 scenario, labelled estimates) | `scoring.SCENARIOS` (moderate ×1, fast ×2) |

## How the Future Edge Score works
```
exposure(skill, t) = base + (1 − base) × rate × t
rate               = clamp(0.15 × arXiv research growth × scenario multiplier × AI sensitivity, 0, 0.30)
AI-adjusted fit(t) = Σ weight × skill credit × (1 − exposure(t)) / Σ weight      (credit: level 0.7 = job-ready = full)
Edge(t)            = 100 × fit(t) / best possible fit × (0.60 + 0.25 × human skills + 0.15 × rarity)
```
The arithmetic is explained in plain English in `src/backend/scoring.py`. Change the trend data and the forecast changes; `tests/test_scoring.py` checks this.

## Run locally
```bash
pip install -r requirements.txt
uvicorn src.backend.main:app --reload --port 8000          # API on :8000
cd src/frontend && npm install && npm run dev               # UI on :5173 (proxies /api)
python -m pytest -q                                         # tests
python -m src.backend.trends                                # fetch live arXiv trend data
python -m tests.check_links                                 # check every course URL
```

## Deploy on Replit (mandatory for the hackathon)
Import this GitHub repo into Replit and press **Run**. `start.sh` builds the frontend and serves everything on one port. For the public link, use **Deploy** (build: `bash build.sh`, run: `bash start.sh`). Put any API keys in **Replit Secrets**, never in the code.

## Repository layout
```
src/backend/       FastAPI app, scoring engine, trend fetcher, JSON data catalogs
src/frontend/      React + Vite + Tailwind + Recharts UI
tests/             pytest suite + link checker
runpod/            RunPod handler (unused – no GPU work)
submission/        PRD, Tech Declaration, proof-of-use PDFs
```

## Data sources
| Data | Source | Status |
|---|---|---|
| AI-trend signals | arXiv API paper counts (last 12 months vs previous 12) | Ships with **sample** values; press *Refresh* on Replit to fetch real data |
| Skill AI-exposure (today) | Team estimate | **Placeholder:** replace with a cited source (e.g. ILO generative-AI exposure study) |
| Roles & skills | Team-curated from ESCO / O*NET | Add ESCO/O*NET URI per role |
| Courses | Public provider pages (Kaggle Learn, freeCodeCamp, Coursera audit, MIT OCW…) | Verify each link (`tests/check_links.py`) |
| SDG targets | United Nations, sdgs.un.org | Check wording before citing |
| Profiles | Synthetic | No real personal data |

## Team TODO before submission
- [ ] Replace placeholder exposure values with a cited source
- [ ] Verify every course link and set `verified: true`
- [ ] Run the arXiv refresh on Replit so `trends.json` holds real data
- [ ] Review and rewrite the assessment scenarios; add field-specific versions
- [ ] Optional: LLM-based CV extraction (restricted to catalog skill ids); declare the model
- [ ] Add the committee GitHub accounts as collaborators; make the repo public before submitting

## AI usage declaration
This starter code was scaffolded with the help of an AI assistant (Claude, Anthropic) on 21 Oct 2026, and the team reviewed and extended it. The idea, product decisions and the Edge Score concept come from the team. All AI tools used must be listed in the Technical & Tools Declaration.

## License
Apache License 2.0. See [LICENSE](LICENSE).
