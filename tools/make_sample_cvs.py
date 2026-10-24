"""Generate the synthetic sample CV PDFs from data/profiles.json.

    pip install reportlab
    python -m tools.make_sample_cvs
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

DATA = Path(__file__).resolve().parents[1] / "src" / "backend" / "data"
OUT = DATA / "sample_cvs"
ACCENT = colors.HexColor("#3b4fb8")


def main():
    OUT.mkdir(exist_ok=True)
    ss = getSampleStyleSheet()
    name = ParagraphStyle("name", parent=ss["Title"], alignment=0, fontSize=22, spaceAfter=2, textColor=ACCENT)
    head = ParagraphStyle("head", parent=ss["Normal"], fontSize=11.5, textColor=colors.HexColor("#333333"), spaceAfter=2)
    small = ParagraphStyle("small", parent=ss["Normal"], fontSize=9, textColor=colors.HexColor("#555555"))
    sec = ParagraphStyle("sec", parent=ss["Heading2"], fontSize=12, textColor=ACCENT, spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=10, leading=13.5)
    for p in json.loads((DATA / "profiles.json").read_text(encoding="utf-8"))["profiles"]:
        story = [Paragraph(p["name"], name), Paragraph(p["headline"], head)]
        if p.get("contact"):
            story.append(Paragraph(p["contact"], small))
        story += [Paragraph("<i>Synthetic sample CV – invented person for the SDC Hackathon 2026 demo.</i>", small),
                  Spacer(1, 4), HRFlowable(width="100%", thickness=1, color=ACCENT), Spacer(1, 2)]
        for section, content in p["cv"].items():
            story.append(Paragraph(section, sec))
            if isinstance(content, list):
                story.append(ListFlowable([ListItem(Paragraph(x, body), leftIndent=10) for x in content],
                                          bulletType="bullet", start="•", leftIndent=10, bulletFontSize=8))
            else:
                story.append(Paragraph(content, body))
        SimpleDocTemplate(str(OUT / f"{p['id']}.pdf"), pagesize=A4, title=f"{p['name']} – sample CV",
                          leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm).build(story)
        print("wrote", OUT / f"{p['id']}.pdf")


if __name__ == "__main__":
    main()
