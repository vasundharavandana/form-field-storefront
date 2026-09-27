from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import markdown
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(__file__).resolve().parent
GUIDE_PATH = DOCS_DIR / "COMPLETE_GUIDE.md"
PDF_PATH = DOCS_DIR / "COMPLETE_GUIDE.pdf"

SOURCE_FILES = [
    ("main.py", "python"),
    ("requirements.txt", "text"),
    ("static/index.html", "html"),
    ("static/styles.css", "css"),
    ("static/app.js", "javascript"),
    ("docs/requirements.txt", "text"),
    ("docs/build_guide.py", "python"),
]


class Element:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []


class MarkdownTreeParser(HTMLParser):
    VOID_TAGS = {"br", "hr", "img", "input", "meta", "link"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs)
        self.stack[-1].children.append(element)
        if tag not in self.VOID_TAGS:
            self.stack.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def plain_text(node):
    if isinstance(node, str):
        return node
    return "".join(plain_text(child) for child in node.children)


def inline_markup(node):
    if isinstance(node, str):
        return escape(node)

    tag = node.tag
    body = "".join(inline_markup(child) for child in node.children)
    if tag in {"strong", "b"}:
        return f"<b>{body}</b>"
    if tag in {"em", "i"}:
        return f"<i>{body}</i>"
    if tag == "code":
        return f'<font name="DejaVuSansMono" size="8">{body}</font>'
    if tag == "a" and "href" in node.attrs:
        return f"<link href={quoteattr(node.attrs['href'])}>{body}</link>"
    if tag == "br":
        return "<br/>"
    return body


def descendants(node, tag):
    return [child for child in node.children if isinstance(child, Element) and child.tag == tag]


def register_fonts():
    fonts = Path("/usr/share/fonts/dejavu")
    pdfmetrics.registerFont(TTFont("DejaVuSans", str(fonts / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(fonts / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(fonts / "DejaVuSansMono.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSansMono-Bold", str(fonts / "DejaVuSansMono-Bold.ttf")))
    pdfmetrics.registerFontFamily(
        "DejaVuSans",
        normal="DejaVuSans",
        bold="DejaVuSans-Bold",
        italic="DejaVuSans",
        boldItalic="DejaVuSans-Bold",
    )


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "GuideTitle", parent=styles["Title"], fontName="DejaVuSans-Bold",
        fontSize=24, leading=29, textColor=colors.HexColor("#262923"),
        alignment=TA_LEFT, spaceAfter=11,
    ))
    styles.add(ParagraphStyle(
        "GuideH1", parent=styles["Heading1"], fontName="DejaVuSans-Bold",
        fontSize=17, leading=21, textColor=colors.HexColor("#262923"),
        spaceBefore=14, spaceAfter=8, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "GuideH2", parent=styles["Heading2"], fontName="DejaVuSans-Bold",
        fontSize=12, leading=15, textColor=colors.HexColor("#397243"),
        spaceBefore=10, spaceAfter=5, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "GuideH3", parent=styles["Heading3"], fontName="DejaVuSans-Bold",
        fontSize=10, leading=13, textColor=colors.HexColor("#262923"),
        spaceBefore=7, spaceAfter=3, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        "GuideBody", parent=styles["BodyText"], fontName="DejaVuSans",
        fontSize=8.7, leading=12, textColor=colors.HexColor("#32342e"),
        spaceAfter=6, splitLongWords=True,
    ))
    styles.add(ParagraphStyle(
        "GuideBullet", parent=styles["GuideBody"], leftIndent=15,
        firstLineIndent=-10, bulletIndent=0, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "GuideCode", fontName="DejaVuSansMono", fontSize=6.1, leading=7.6,
        leftIndent=5, rightIndent=5, borderColor=colors.HexColor("#e1e2db"),
        borderWidth=0.4, borderPadding=5, backColor=colors.HexColor("#f5f5f2"),
        spaceBefore=4, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "GuideTable", parent=styles["GuideBody"], fontSize=7.4,
        leading=9.3, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        "GuideTableHeader", parent=styles["GuideTable"],
        fontName="DejaVuSans-Bold", textColor=colors.HexColor("#262923"),
    ))
    return styles


def add_table(element, story, styles, available_width):
    rows = []
    for row in element.children:
        if not isinstance(row, Element):
            continue
        if row.tag in {"thead", "tbody", "tfoot"}:
            row_elements = [child for child in row.children if isinstance(child, Element) and child.tag == "tr"]
        elif row.tag == "tr":
            row_elements = [row]
        else:
            continue
        for row_element in row_elements:
            cells = [child for child in row_element.children if isinstance(child, Element) and child.tag in {"th", "td"}]
            cell_style = styles["GuideTableHeader"] if cells and cells[0].tag == "th" else styles["GuideTable"]
            rows.append([Paragraph(inline_markup(cell), cell_style) for cell in cells])

    if not rows:
        return

    column_count = max(len(row) for row in rows)
    widths = [available_width / column_count] * column_count
    if column_count == 3:
        widths = [available_width * 0.34, available_width * 0.20, available_width * 0.46]
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff0e8")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#ddded7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([table, Spacer(1, 7)])


def add_list(element, story, styles, depth=0):
    for item in descendants(element, "li"):
        children = [child for child in item.children if not (isinstance(child, Element) and child.tag in {"ul", "ol"})]
        text = "".join(inline_markup(child) for child in children).strip()
        if text:
            style = ParagraphStyle(
                f"GuideBullet{depth}", parent=styles["GuideBullet"],
                leftIndent=15 + 10 * depth, firstLineIndent=-10,
            )
            bullet = "&#8226;" if element.tag == "ul" else f"{descendants(element, 'li').index(item) + 1}."
            story.append(Paragraph(f"{bullet}&nbsp;&nbsp;{text}", style))
        for nested in item.children:
            if isinstance(nested, Element) and nested.tag in {"ul", "ol"}:
                add_list(nested, story, styles, depth + 1)


def build_story(root, styles, available_width):
    story = []
    for node in root.children:
        if isinstance(node, str):
            if node.strip():
                story.append(Paragraph(escape(node.strip()), styles["GuideBody"]))
            continue

        if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            title = plain_text(node)
            if node.tag == "h1" and title.startswith("Appendix:"):
                story.append(PageBreak())
            style_name = "GuideTitle" if node.tag == "h1" and not title.startswith("Appendix:") else {
                "h1": "GuideH1", "h2": "GuideH2", "h3": "GuideH3",
                "h4": "GuideH3", "h5": "GuideH3", "h6": "GuideH3",
            }[node.tag]
            story.append(Paragraph(inline_markup(node), styles[style_name]))
        elif node.tag == "p":
            story.append(Paragraph(inline_markup(node), styles["GuideBody"]))
        elif node.tag in {"ul", "ol"}:
            add_list(node, story, styles)
            story.append(Spacer(1, 3))
        elif node.tag == "pre":
            story.append(Preformatted(
                plain_text(node).rstrip("\n"), styles["GuideCode"], maxLineLength=105,
            ))
        elif node.tag == "table":
            add_table(node, story, styles, available_width)
        elif node.tag == "hr":
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#e1e2db"), spaceBefore=5, spaceAfter=8))

    return story


def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#e1e2db"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.52 * inch, letter[0] - doc.rightMargin, 0.52 * inch)
    canvas.setFont("DejaVuSans", 7)
    canvas.setFillColor(colors.HexColor("#77786e"))
    canvas.drawString(doc.leftMargin, 0.35 * inch, "Form & Field | Complete Project Guide")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main():
    guide = GUIDE_PATH.read_text(encoding="utf-8")
    sections = [guide, "\n# Appendix: Complete Source Files\n\nThese listings are generated directly from the current project files.\n"]
    for relative_path, language in SOURCE_FILES:
        source = (PROJECT_DIR / relative_path).read_text(encoding="utf-8").rstrip()
        sections.extend([
            f"\n## `{relative_path}`\n\n",
            f"```{{.{language}}}\n{source}\n```\n",
        ])

    document_html = markdown.markdown(
        "".join(sections),
        extensions=["fenced_code", "sane_lists", "tables"],
    )
    parser = MarkdownTreeParser()
    parser.feed(document_html)

    register_fonts()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.72 * inch,
        title="Form & Field — Complete Project Guide",
        author="Form & Field Storefront Documentation",
    )
    styles = make_styles()
    available_width = letter[0] - doc.leftMargin - doc.rightMargin
    story = build_story(parser.root, styles, available_width)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

    print(f"Created {PDF_PATH}")


if __name__ == "__main__":
    main()