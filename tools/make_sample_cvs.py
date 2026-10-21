"""Generate the synthetic sample CV PDFs from data/profiles.json.

    pip install reportlab
    python -m tools.make_sample_cvs
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

DATA = Path(__file__).resolve().parents[1] / "src" / "backend" / "data"
OUT = DATA / "sample_cvs"


def main():
    OUT.mkdir(exist_ok=True)
    styles = getSampleStyleSheet()
    for p in json.loads((DATA / "profiles.json").read_text(encoding="utf-8"))["profiles"]:
        story = [Paragraph(p["name"], styles["Title"]),
                 Paragraph(p["headline"], styles["Heading3"]),
                 Paragraph("<i>SYNTHETIC SAMPLE CV – invented person for the SDC Hackathon 2026 demo.</i>", styles["Normal"]),
                 Spacer(1, 12)]
        for section, body in p["cv"].items():
            story += [Paragraph(section, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 6)]
        SimpleDocTemplate(str(OUT / f"{p['id']}.pdf"), pagesize=A4, title=f"{p['name']} – sample CV").build(story)
        print("wrote", OUT / f"{p['id']}.pdf")


if __name__ == "__main__":
    main()
