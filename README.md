# Future Edge – your career weather forecast for the AI era

> Upload your CV and see, year by year, how AI will change the value of your skills over the next 3 years, which future roles fit you best, and the shortest reskilling path to stay ahead, with every role and skill linked to the UN SDGs.

**Live demo:** https://sdc-2026-future-edge.replit.app  ·  **Domain 1 – Aiversecity Future-Ready Workforce**

---

## Team Information

| Field                  | Details |
| ---------------------- | ------- |
| **Team Name**          | BEBZA |
| **Team Domain**        | Domain 1 – Aiversecity Future-Ready Workforce |
| **SDG Track (1–17)**   | SDG 8 – Decent Work and Economic Growth (targets 8.2, 8.5), with SDG 4 – Quality Education (targets 4.3, 4.4) |
| **Team Leader**        | Azimkhan Bekassyl |
| **University**         | Xiamen University Malaysia (XMUM) |
| **Number of Members**  | 5 |

## Links

| Resource          | Link |
| ----------------- | ---- |
| GitHub Repository | https://github.com/Magisterofdrinkingcoffee/sdc2026-future-edge |
| Replit Project    | https://replit.com/@riotbek07/sdc2026-future-edge |
| Live Demo         | https://sdc-2026-future-edge.replit.app |
| Slide Deck        | [`submission/SDC2026_BEBZA_PitchDeck.pdf`](submission/SDC2026_BEBZA_PitchDeck.pdf) |
| Demo Video        | *YouTube link added by the team before the deadline* |
| Proposal (PRD)    | [`submission/SDC2026_BEBZA_Preliminary.pdf`](submission/SDC2026_BEBZA_Preliminary.pdf) |
| Tech Declaration  | [`submission/SDC2026_BEBZA_TechDeclaration.pdf`](submission/SDC2026_BEBZA_TechDeclaration.pdf) |
| Replit proof of use | [`submission/SDC2026_BEBZA_Replit_POU.pdf`](submission/SDC2026_BEBZA_Replit_POU.pdf) |
| Model cards       | [`docs/MODELS.md`](docs/MODELS.md) |

---

## Overview

### Problem

In Malaysia, 56% of professionals already use AI tools at work but only 26% have had formal training (Hays Asia Salary Guide 2025), and more than 600,000 workers will need reskilling within three to five years (MOSTI). Workers don't know which skills AI will take over, and most career tools give a one-time answer from a static list that is out of date the day it is published.

### Who it is for

The moment we design for: **a person deciding what to learn next**, before AI makes the decision for them. Our five sample users (made-up people, made-up CVs) are a final-year engineering student, an admin executive with 6 years' experience whose data-entry work is shrinking, a fresh CS graduate, a customer-service team lead whose calls are moving to chatbots, and a junior accountant whose bookkeeping is being automated. HR and L&D managers planning a team's reskilling are served by the team view.

### Solution

Future Edge turns a CV into a **3-year career forecast**. It doesn't ask "which job matches your keywords?" – it asks "which of your skills will still be yours in 2029?":

1. **Tell us about yourself** – upload a CV (PDF, Word, photo or text). Personal data (name, email, phone, IC, age, gender) is removed before matching.
2. **See the Future Skills Radar** – each skill is labelled *growing in value / holding steady / at risk from AI*, with how much of it AI can do now and in 2029.
3. **Catch the AI** – instead of a self-rating quiz, the user reviews a short AI-written work sample with planted mistakes. This measures judgment and responsibility, the skills that keep humans in charge of AI.
4. **Get matched** – future roles ranked by an explainable **Edge Score** (0–100, "how hard you'll be to replace"), with a skills gap and real Malaysian job-market data.
5. **Follow a pathway** – an ordered quest map of free or low-cost courses and projects with hours and weeks, starting from the **One Move** that raises your score the most.

### Key Features (the six must-haves)

| Must-have | How Future Edge does it |
|---|---|
| 1. Skills profile intake | CV upload (PDF / Word / photo / .txt) or paste; skills are matched only against our 52-skill catalog, with the CV sentence shown as evidence. The user can adjust every level. |
| 2. AI-trend signal layer | **Model 2**: monthly arXiv paper counts for 10 AI-capability areas (Oct 2023 – Sep 2026), forecast with a damped trend and 80% range. Source and collection date are shown on every screen. A "Refresh trend data" button re-downloads from the arXiv API, and the forecast changes with it. Job demand comes from WEF Future of Jobs 2025 (Malaysia profile), DOSM wages and TalentCorp MyCOL. |
| 3. Future-role matching | 34 roles ranked by Edge Score = AI-adjusted fit × human skills × job market × core-skill check, with a plain-English "why" for every number. |
| 4. Personalised reskilling pathway | Ordered steps (courses + projects) with hours and weeks at the user's hours per week. All 53 resources are real, free or low-cost, link-checked on 24 Oct 2026, and include HRD Corp-claimable training. |
| 5. SDG mapping | Every one of the 52 skills, 34 roles and every pathway step is tagged with at least one SDG target. Each role has a plain line on *how* the work serves its SDG, the forecast shows **which SDG targets your whole path contributes to and why** (role, your skills, each quest), and the user can pick what they want their work to help with (climate & energy, health & food, digital inclusion, fair work & skills) – roles that serve it are surfaced and lifted in the ranking, so the SDG link changes the user's choices. The Edge Score itself is never changed by SDG preferences. |
| 6. Handling uncertainty | Two scenarios (moderate vs fast AI disruption) shown side by side, plus a low–high range from Model 2's 80% interval and Model 3's measurement range. Every result says it is an estimate and never a hiring decision. |

**Good-to-have features included:**

| Good-to-have (Domain 1 brief) | In Future Edge |
|---|---|
| Employer / HR view | **Team view** (🏢 on the home page): skills heatmap of a whole team against a target role, shared gaps, one team reskilling plan with total hours, each person's best future role, and the team's SDG contribution. For training plans only, never hiring. |
| Automatic re-planning when trend data changes | Forecast, role ranking and quest plan are recomputed whenever the arXiv trend data is refreshed or a "what if AI moves faster here" slider is moved. |
| Inclusive design | Interface in **English, Bahasa Malaysia and Chinese** (language switcher on every screen); mobile-friendly layout; free and low-cost courses only. |
| Learner motivation | Quest map, XP, levels, streaks, badges and an Edge Score history. |
| Fairness checks | Name, email, phone, IC number, age, gender, race, religion and marital status are removed before matching, and **every CV is re-read as 12 invented people** with different names, genders, ages, races, religions and marital status – the app shows that the result is identical (also covered by automated tests). |
| SDG contribution for a person / company | Personal "your path contributes to" panel and the team SDG contribution in the HR view. |

### Rules we followed

- **Data:** only public, open or synthetic data. Our sample CVs are made up (`tools/make_sample_cvs.py`).
- **No invented jobs, courses or statistics:** roles, skills and courses come from fixed catalogs with sources; the CV reader can only return catalog skills and quotes the CV sentence it used.
- **Human-centred:** the app supports a person's own career decision. It never ranks candidates for employers and never makes hiring decisions.

### Tech Stack

| Layer         | Technology |
| ------------- | ---------- |
| Frontend      | React 18, Vite, Tailwind CSS |
| Backend       | Python, FastAPI, Uvicorn |
| AI models     | Model 1: TF-IDF + logistic regression (scikit-learn, trained on CPU, exported to plain-Python JSON). Model 2: damped log-linear trend (plain Python). Model 3: exact scoring of a performance task. |
| Data          | JSON catalogs in the repo (no database needed); O*NET / GPTs-are-GPTs, arXiv API, WEF, DOSM, MyCOL |
| CV reading    | pypdf, a built-in Word (.docx) reader, optional Google Gemini API for photos and messy layouts |
| Hosting / Dev | **Replit** (development, Shell, link checking and the live deployment) |
| Compute       | CPU only – no GPU work, so RunPod is not used (Participant Handbook 9.4) |

---

## Project Structure

```
.
├── docs/MODELS.md          # Model cards for Models 1-3 and the Edge Score
├── runpod/handler.py       # template placeholder – no GPU work in this project
├── src/
│   ├── backend/            # FastAPI app, scoring, models, CV reader, data catalogs
│   ├── database/           # raw public datasets (O*NET tasks, arXiv counts, WEF, DOSM, MyCOL)
│   └── frontend/           # React app (wizard, forecast, quest map)
├── submission/             # PRD, Tech Declaration, Replit proof of use, pitch deck (+ editable sources)
├── tests/                  # 55 tests + link checker
├── tools/                  # data collection, training and build scripts
├── .replit, build.sh, start.sh
└── LICENSE                 # Apache 2.0
```

### Architecture

```
Browser (React)  ──►  FastAPI on Replit  ──►  Model 1  AI-exposure (O*NET-trained)   ─┐
   CV upload            /api/profile          Model 2  AI-trend forecast (arXiv)      ├─► Edge Score + range
   forecast             /api/forecast         Model 3  Catch the AI (judgment)       ─┘        │
   quest map            /api/pathway          WEF / DOSM / MyCOL job market ─────────────────┘
                        /api/trends/refresh ──► arXiv API (live refresh)
                        (optional) Gemini API for hard-to-read CVs, personal data removed first
```

---

## How to Run

### Option 1 – Replit (recommended)

1. Open the [Replit project](https://replit.com/@riotbek07/sdc2026-future-edge), or import this repo with **Import → GitHub**.
2. Optional: add `GEMINI_API_KEY` in **Secrets** for photo CVs. Without it the app reads PDF, Word and text CVs offline.
3. Click **Run**. `.replit` runs `bash start.sh`, which builds the frontend once and serves everything on port 8000.

### Option 2 – Locally

```bash
git clone https://github.com/Magisterofdrinkingcoffee/sdc2026-future-edge.git
cd sdc2026-future-edge
bash build.sh        # pip install -r requirements.txt + build the React app
bash start.sh        # http://localhost:8000
```

### Run Tests

```bash
python -m pytest -q          # 55 tests
python -m tests.check_links  # checks every course link (needs internet)
```

---

## How We Use Replit *(Required)*

- **Development and testing:** the team imported the repo into Replit and used its Shell to install dependencies, build the app, run the test suite and check all 53 course links (the checker needs open internet).
- **Hosting:** the live demo is a Replit autoscale deployment, configured in `.replit` (`build.sh` then `start.sh`): https://sdc-2026-future-edge.replit.app
- **Secrets:** the optional `GEMINI_API_KEY` is kept in Replit Secrets, never in the code.

Proof of use: [`submission/SDC2026_BEBZA_Replit_POU.pdf`](submission/SDC2026_BEBZA_Replit_POU.pdf) (also included in the Technical & Tools Declaration).

## How We Use RunPod

Not used. All our models train and run on a normal CPU in seconds (Model 1 trains on 19,265 short task statements), so no work needed a GPU. The Participant Handbook (section 9.4) requires RunPod only for GPU work.

---

## Hardest risks and our fallbacks

| Risk | What we did |
|---|---|
| Reliable, updatable trend data | arXiv API is free and stable; the collector is resumable, and the app keeps the last good snapshot if a refresh fails. |
| Matching quality | Model 1 is validated on occupations it never saw (73.4% accuracy vs 53.2% baseline); Model 2 is backtested (17.2% error vs 22.7% naive). Results in `docs/MODELS.md`. |
| AI inventing jobs or courses | No generative model writes recommendations. Roles, skills and courses come from fixed, cited catalogs. |
| US-based task labels applied to Malaysia | Job-market numbers come from Malaysian sources (WEF Malaysia profile, DOSM, MyCOL); the limitation is stated in the model card. |

## Challenges & Learnings

- A plain exponential trend over-shot because AI research boomed in 2023–24 and is now slowing. A damped trend, with the damping chosen on held-out months only, cut forecast error from 29.5% to 17.2%.
- There is no labelled data for "judgment", so instead of training a model on our own opinions we built a test with known answers (Catch the AI).
- PyMuPDF is AGPL-licensed, so we switched to pypdf to stay compatible with Apache 2.0.

## Future Improvements

- [ ] Translate course descriptions and role details (the interface is already in BM and Chinese)
- [ ] Company / region SDG dashboards built on the team view
- [ ] Job-posting data (e.g. MYFutureJobs) as a second trend signal
- [ ] More Catch-the-AI packs per field

## Team

| Name | Role |
| ---- | ---- |
| Azimkhan Bekassyl | Team leader, product and scoring |
| Alibek Berik | CV reader |
| Elnurken Abdigaparov | Team member |
| Bernar Zholdybek | Team member |
| Shirvanskiy Zeinal | Team member |

---

## Submission Checklist

- [x] Team name, domain and SDG track filled in
- [x] Live demo on Replit
- [x] Replit used, with proof in `submission/SDC2026_BEBZA_Replit_POU.pdf`
- [x] RunPod: not needed (no GPU work)
- [x] PRD and Tech Declaration in `submission/`
- [x] Pitch deck in `submission/`
- [ ] Demo video link added
- [x] "How to Run" steps verified
- [x] No API keys or secrets committed to the repository

## License

This project is licensed under the [Apache License 2.0](LICENSE). Third-party data keeps its own licence: GPTs-are-GPTs labels (MIT, `src/database/LICENSE-gpts-are-gpts.txt`), O*NET (CC BY 4.0).
