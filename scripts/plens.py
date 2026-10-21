#!/usr/bin/env python3
"""paper-lens command line tool.

Single entry point for every mechanical step of the paper-lens pipeline.
Zero config, cross platform, and it picks whichever PDF backend is available.

    plens.py init     --root DIR           scaffold a library
    plens.py fetch    ARXIV_ID --venue ..  download + validate + file a paper
    plens.py text     PDF -o OUT           dump full text (grep-able)
    plens.py toc      PDF                  list every section heading
    plens.py figures  PDF -o DIR           crop figures via caption anchors
    plens.py check    HTML                 validate tags / images / anchors

Backend notes
    pymupdf  -> text, toc (with font heuristics), figures      recommended
    pypdf    -> text, toc (regex only)                         text only

Only ASCII is printed, so this stays safe on GBK Windows consoles.
"""

import argparse
import os
import re
import sys
import urllib.request

# --------------------------------------------------------------------------
# backend detection
# --------------------------------------------------------------------------

try:
    import pymupdf  # type: ignore
    HAVE_FITZ = True
except ImportError:
    try:
        import fitz as pymupdf  # type: ignore
        HAVE_FITZ = True
    except ImportError:
        pymupdf = None
        HAVE_FITZ = False

try:
    from pypdf import PdfReader  # type: ignore
    HAVE_PYPDF = True
except ImportError:
    PdfReader = None
    HAVE_PYPDF = False


def need(flag, what):
    if not flag:
        sys.exit(
            "ERROR: %s requires PyMuPDF. Install it with:\n"
            "    pip install pymupdf\n"
            "(pypdf can only dump text, not figures or font-aware headings.)" % what
        )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def parse_pages(spec, total):
    """'3,4-7' -> [3,4,5,6,7] as 1-based page numbers, clamped to total."""
    if not spec:
        return list(range(1, total + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    seen, uniq = set(), []
    for p in out:
        if 1 <= p <= total and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def open_pdf(path):
    """Return (doc, closer). Raises SystemExit with a friendly message."""
    if not os.path.exists(path):
        sys.exit("ERROR: file not found: %s" % path)
    if HAVE_FITZ:
        try:
            return pymupdf.open(path)
        except Exception as exc:
            sys.exit("ERROR: cannot open PDF (%s)" % exc.__class__.__name__)
    if HAVE_PYPDF:
        try:
            return PdfReader(path)
        except Exception as exc:
            sys.exit("ERROR: cannot open PDF (%s)" % exc.__class__.__name__)
    sys.exit("ERROR: no PDF backend. Run: pip install pymupdf")


def find_root(explicit):
    """--root > $PL_ROOT > nearest profile.md going upwards > error."""
    if explicit:
        return os.path.abspath(explicit)
    env = os.environ.get("PL_ROOT")
    if env:
        return os.path.abspath(env)
    cur = os.getcwd()
    while True:
        if os.path.exists(os.path.join(cur, "profile.md")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    sys.exit(
        "ERROR: cannot locate the library root.\n"
        "Pass --root <dir>, or set PL_ROOT, or run from inside a library "
        "that contains profile.md."
    )


def safe_name(title):
    """Strip characters Windows forbids in directory names."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")
    return cleaned or "untitled"


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------

def cmd_text(args):
    pages_wanted = None
    if HAVE_FITZ:
        doc = open_pdf(args.pdf)
        total = doc.page_count
        pages = parse_pages(args.pages, total)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            for pno in pages:
                fh.write("===== PDF page %d =====\n" % pno)
                fh.write(doc[pno - 1].get_text("text"))
                fh.write("\n")
        doc.close()
        print("OK: wrote %d page(s) of %d -> %s" % (len(pages), total, args.out))
        return 0

    if HAVE_PYPDF:
        reader = PdfReader(args.pdf)
        total = len(reader.pages)
        pages = parse_pages(args.pages, total)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            for pno in pages:
                fh.write("===== PDF page %d =====\n" % pno)
                fh.write(reader.pages[pno - 1].extract_text() or "")
                fh.write("\n")
        print("OK: wrote %d page(s) of %d -> %s" % (len(pages), total, args.out))
        return 0

    sys.exit("ERROR: no PDF backend. Run: pip install pymupdf")


# --------------------------------------------------------------------------
# toc
# --------------------------------------------------------------------------

# Headings come in two flavours: numbered ("1 Introduction", "A.2 Details",
# "III. METHOD") and unnumbered, where size or weight carries the level instead
# (AAAI and some NeurIPS templates do this). Both have to work.
RE_NUMBERED = re.compile(
    r"^(\d+(?:\.\d+){0,3}|[A-Z](?:\.\d+){0,3}|[IVX]{1,5})[.)]?\s+(\S.{1,78})$")
RE_TRAILING_PUNCT = re.compile(r"[.;:,]\s*$")
RE_MOSTLY_DIGITS = re.compile(r"^[\d\s.,%()\-+/=]+$")
RE_CITATION_LINE = re.compile(
    r"^\[\d+\]|In Proceedings of|arXiv preprint|pp\.\s*\d+"
    r"|International Conference|Conference on|Workshop on|Journal of")
RE_YEAR = re.compile(r"\b(19|20)\d{2}\b")

# things that are bold and set apart but are definitely not headings
RE_MATH_CHARS = re.compile(r"[=∥⊙∑∫√≈≤≥±×÷→←↔∂∇ˆ~^_{}\\∈∀∃]")
RE_URL = re.compile(r"://|www\.|\S@\S")
RE_PAREN_HEAD = re.compile(r"^[（(\[]")
RE_CODE_LINE = re.compile(r"^\d+\s*:")          # pseudocode labels: "12: else"
RE_ARTICLE_HEAD = re.compile(
    r"^(the|a|an|as|in|we|this|these|it|but|however|for|to|on|at)\b", re.I)
RE_WEAK_END = re.compile(
    r"\b(to|of|and|the|in|for|with|is|are|was|were|that|which|by|as|on|at"
    r"|from|or|but|a|an|this|these|we|our)$", re.I)

# font names that carry emphasis: Nimbus/URW use "Medi" for medium weight,
# and many templates use SemiBold / Demi / Black instead of plain Bold.
BOLD_HINTS = ("bold", "medi", "black", "semibold", "demi", "heavy", "-b-")


def is_bold(font_name):
    low = (font_name or "").lower()
    return any(hint in low for hint in BOLD_HINTS)


def plausible_title(title):
    if not title:
        return False
    title = title.strip()
    if len(title) < 2 or len(title) > 80:
        return False
    if RE_TRAILING_PUNCT.search(title):
        return False
    if RE_MOSTLY_DIGITS.match(title):
        return False
    if RE_CITATION_LINE.search(title):
        return False
    if RE_MATH_CHARS.search(title):
        return False
    if RE_URL.search(title):
        return False
    if RE_PAREN_HEAD.match(title):
        return False
    if RE_CODE_LINE.match(title):
        return False
    if RE_ARTICLE_HEAD.match(title):   # "As the model can only ..." reads like body text
        return False
    if title.count(",") >= 2:          # author lists, keyword lines
        return False
    if RE_WEAK_END.search(title):      # a body sentence that happens to start bold
        return False
    if title.endswith("-"):            # a broken word at a line wrap
        return False
    if RE_YEAR.search(title):          # bibliography entries almost always carry one
        return False
    if title[0].islower():
        return False
    if sum(ch.isdigit() for ch in title) > len(title) * 0.3:
        return False
    return True


def heading_level(number):
    if re.fullmatch(r"\d+(?:\.\d+)*", number):
        return number.count(".") + 1
    if re.fullmatch(r"[A-Z](?:\.\d+)*", number):
        return number.count(".") + 1
    return 1


def body_font_size(doc):
    """Char-weighted mode of span sizes: the size most of the text uses."""
    counts = {}
    for pno in range(min(doc.page_count, 8)):
        for block in doc[pno].get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        key = round(span["size"], 1)
                        counts[key] = counts.get(key, 0) + len(text)
    return max(counts, key=counts.get) if counts else None


def scan_headings_fitz(doc, body_size):
    rows = []
    for pno in range(doc.page_count):
        page = doc[pno]
        image_boxes = []
        try:
            image_boxes = [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
        except Exception:
            pass
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(s.get("text", "") for s in spans).strip()
                if not text:
                    continue
                bbox = pymupdf.Rect(line["bbox"])
                # labels inside figures are bold too, but they are not headings
                if any(box.contains(bbox) for box in image_boxes):
                    continue
                biggest = max((s.get("size", 0) for s in spans), default=0)
                bold = any(is_bold(s.get("font", "")) for s in spans)

                level = None
                numbered = RE_NUMBERED.match(text)
                if numbered and plausible_title(numbered.group(2)):
                    level = heading_level(numbered.group(1))
                elif body_size is not None and plausible_title(text):
                    if biggest >= body_size + 1.6:
                        level = 1
                    elif biggest >= body_size + 0.5:
                        level = 1
                    elif bold and biggest >= body_size - 0.1:
                        level = 2
                if level is not None:
                    rows.append((level, text, pno + 1))
    return rows


def scan_headings_pypdf(reader):
    rows = []
    for pno in range(len(reader.pages)):
        for line in (reader.pages[pno].extract_text() or "").splitlines():
            line = line.strip()
            match = RE_NUMBERED.match(line)
            if match and plausible_title(match.group(2)):
                rows.append((heading_level(match.group(1)), line, pno + 1))
    return rows


def cmd_toc(args):
    need(HAVE_FITZ or HAVE_PYPDF, "toc")
    doc = open_pdf(args.pdf)

    if HAVE_FITZ:
        # 1. the embedded outline is authoritative when the PDF has one
        try:
            outline = doc.get_toc(simple=True)
        except Exception:
            outline = []
        if outline:
            rows = [(lvl, title.strip(), page) for lvl, title, page in outline]
            doc.close()
            print("# source: embedded outline")
            return emit_toc(rows, args)
        # 2. no outline: infer from size and weight
        rows = scan_headings_fitz(doc, body_font_size(doc))
        doc.close()
        print("# source: font heuristic (this PDF has no outline)")
    else:
        rows = scan_headings_pypdf(doc)
        print("# source: regex only (pypdf exposes no font info)")

    # running heads repeat the same text on every page
    seen, uniq = set(), []
    for level, title, page in rows:
        key = re.sub(r"\s+", " ", title.lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append((level, title, page))

    return emit_toc(uniq, args)


def emit_toc(rows, args):
    if not rows:
        print("no headings found.")
        print("this usually means a scanned PDF, or headings rendered as images.")
        print("fall back to: grep -n '^[0-9]\\+ \\|^[A-Z] ' on the text dump")
        return 1
    for level, title, page in rows:
        indent = "  " * max(0, level - 1)
        print("%s[%d] %s   (p.%d)" % (indent, level, title, page))
    print("\ntotal headings: %d" % len(rows))
    print("check this list before reading in chunks -- a heading can hide")
    print("in the gap between two chunk reads, which makes you misjudge")
    print("the paper's structure (e.g. missing a Limitations appendix).")
    return 0


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------

RE_CAPTION = re.compile(r"^\s*(?:Figure|Fig\.?)\s*(\d+)\s*[.:]")


def cmd_figures(args):
    need(HAVE_FITZ, "figures")
    doc = open_pdf(args.pdf)
    os.makedirs(args.out, exist_ok=True)
    total = 0

    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = page.get_text("blocks")
        header_bottom = 60.0  # never crop into the running head
        for block in blocks:
            head = block[4]
            if "Published as a conference paper" in head or "Proceedings of" in head:
                header_bottom = max(header_bottom, block[3])

        captions = []
        for block in blocks:
            match = RE_CAPTION.match(block[4])
            if match:
                captions.append((int(match.group(1)), block))
        if not captions:
            continue
        captions.sort(key=lambda c: c[1][1])

        graphics = [d["rect"] for d in page.get_drawings()]
        try:
            graphics += [
                pymupdf.Rect(i["bbox"]) for i in page.get_image_info()
                if (i["bbox"][3] - i["bbox"][1]) > 12 and (i["bbox"][2] - i["bbox"][0]) > 12
            ]
        except Exception:
            pass

        prev_bottom = header_bottom + 2
        for figno, caption in captions:
            cap_top, cap_bottom = caption[1], caption[3]
            candidates = [
                r for r in graphics
                if r.y1 <= cap_top + 2 and r.y0 >= prev_bottom and r.height > 3
            ]
            top = min((r.y0 for r in candidates), default=cap_top - 200)
            x0, x1 = caption[0], caption[2]
            for block in blocks:
                if block[1] >= top - 2 and block[3] <= cap_bottom + 2:
                    x0 = min(x0, block[0])
                    x1 = max(x1, block[2])
            for rect in candidates:
                x0 = min(x0, rect.x0)
                x1 = max(x1, rect.x1)
            clip = pymupdf.Rect(x0 - 4, top - 4, x1 + 4, cap_bottom + 2)
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(args.scale, args.scale), clip=clip)
            pix.save(os.path.join(args.out, "fig%02d.png" % figno))
            print("fig %-2d page %-3d clip %dx%d" % (
                figno, pno + 1, round(clip.width), round(clip.height)))
            total += 1
            prev_bottom = cap_bottom + 4

    doc.close()
    print("ok figures=%d -> %s" % (total, args.out))
    if total:
        print("inspect every PNG: auto-cropping can swallow body text")
        print("or clip half a subplot. Re-run with --scale 5 for denser figures.")
    return 0 if total else 1


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

class HtmlValidator(argparse.Action):
    pass


def validate_html(path):
    from html.parser import HTMLParser

    class V(HTMLParser):
        VOID = {"meta", "img", "br", "hr", "link", "input", "source", "col"}

        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.errors = [], []
            self.imgs, self.anchors, self.hrefs = [], set(), []

        def handle_starttag(self, tag, attrs):
            if tag in self.VOID:
                for key, val in attrs:
                    if tag == "img" and key == "src" and val:
                        self.imgs.append(val)
                return
            self.stack.append(tag)
            for key, val in attrs:
                if key == "id" and val:
                    self.anchors.add(val)
                if key == "href" and val and val.startswith("#"):
                    self.hrefs.append(val[1:])

        def handle_endtag(self, tag):
            if tag in self.VOID:
                return
            if not self.stack or self.stack[-1] != tag:
                top = self.stack[-1] if self.stack else "none"
                self.errors.append("%s@line%d(top=%s)" % (tag, self.getpos()[0], top))
            else:
                self.stack.pop()

    base = os.path.dirname(os.path.abspath(path))
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    validator = V()
    validator.feed(source)
    validator.close()

    missing = [
        src for src in validator.imgs
        if not os.path.exists(os.path.join(base, src.replace("/", os.sep)))
    ]
    broken = [href for href in validator.hrefs if href not in validator.anchors]

    print("unclosed_tags=%d" % len(validator.stack))
    print("mismatch_errors=%d" % len(validator.errors))
    print("imgs=%d missing=%d" % (len(validator.imgs), len(missing)))
    print("anchors_broken=%d" % len(broken))
    if validator.errors:
        print("detail %s" % ",".join(validator.errors[:5]))
    if missing:
        print("missing_detail %s" % ",".join(missing[:5]))
    if broken:
        print("broken_detail %s" % ",".join(broken[:5]))

    ok = not validator.stack and not validator.errors and not missing and not broken
    print("RESULT %s" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def cmd_check(args):
    if not os.path.exists(args.html):
        sys.exit("ERROR: file not found: %s" % args.html)
    return validate_html(args.html)


# --------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------

def cmd_fetch(args):
    root = find_root(args.root)
    venue = safe_name(args.venue)
    title = safe_name(args.title)
    target_dir = os.path.join(root, "papers", venue, title)
    os.makedirs(target_dir, exist_ok=True)

    file_id = args.arxiv_id + (args.version or "")
    url = "https://arxiv.org/pdf/%s" % file_id
    dest = os.path.join(target_dir, file_id + ".pdf")

    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; paper-lens)"})
    print("GET %s" % url)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    except Exception as exc:
        sys.exit("FAIL %s (%s)" % (url, exc.__class__.__name__))

    with open(dest, "wb") as fh:
        fh.write(data)

    size = len(data)
    header_ok = data[:5] == b"%PDF-"
    eof_ok = b"%%EOF" in data[-1024:]
    if size > 10000 and header_ok and eof_ok:
        print("OK   %s  (%d bytes)" % (dest, size))
        print("next: fill info.md from assets/info-template.md")
        return 0

    print("FAIL %s  size=%d hdr=%s eof=%s" % (
        dest, size, data[:5].decode("latin-1", "replace"), eof_ok))
    print("the file was kept so you can inspect it, but it is not a valid PDF")
    return 1


# --------------------------------------------------------------------------
# init
# --------------------------------------------------------------------------

REGISTRY_STUB = """# Registry -- full index of every paper

One row per paper. Register immediately after reading, do not batch it up.
The "last check" column is the only column you may update automatically.

| round | # | short | venue year | summary file | grade | score | sections ok | last check |
|---|---|---|---|---|---|---|---|---|
"""

CASE_LIBRARY_STUB = """# Case library -- scoring anchors

Read the last 10 rows before scoring to calibrate your scale.
Dedupe key = short + venue. Re-scoring overwrites the old row, tagged `[redo YYYY-MM-DD]`.

| short | venue year | novelty | evidence | repro | reuse | honesty | total | grade | one-line reason | key anchor |
|---|---|---|---|---|---|---|---|---|---|---|
"""

CHANGELOG_STUB = """# Changelog

Record every framework change here: what changed, why, and which paper or
session triggered it. Anchor changes matter most -- they move historical scores.

| date | what | why | trigger |
|---|---|---|---|
"""


def cmd_init(args):
    root = os.path.abspath(args.root)
    os.makedirs(root, exist_ok=True)
    made = []
    for sub in ("papers", "rounds", "ledger"):
        path = os.path.join(root, sub)
        if not os.path.isdir(path):
            os.makedirs(path)
            made.append(sub + "/")

    stubs = {
        os.path.join("ledger", "registry.md"): REGISTRY_STUB,
        os.path.join("ledger", "case-library.md"): CASE_LIBRARY_STUB,
        os.path.join("ledger", "changelog.md"): CHANGELOG_STUB,
    }
    for rel, content in stubs.items():
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            made.append(rel)

    profile_path = os.path.join(root, "profile.md")
    if not os.path.exists(profile_path):
        with open(profile_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(
                "# Profile\n\n"
                "## research\n"
                "- topic: <one line>\n"
                "- keywords: <three terms>\n"
                "- main question: <the question this paper should help with>\n\n"
                "## venues\n"
                "- accept: <Conference A, Conference B>\n"
                "- accept_journal: <Journal A>\n"
                "- reject: workshop, findings, challenge, symposium\n\n"
                "## paths\n"
                "- root: %s\n"
                "- topic_grouping: []\n\n"
                "## preferences\n"
                "- language: zh\n"
                "- date_format: \"%%Y-%%m-%%d\"\n" % root)
        made.append("profile.md")

    print("root: %s" % root)
    if made:
        print("created: %s" % ", ".join(made))
        print("next: fill profile.md, then run `plens.py text` on one PDF to verify")
    else:
        print("already initialised, nothing to do")
    return 0


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="plens",
        description="paper-lens: mechanical steps of the paper reading pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="backend: pymupdf=%s  pypdf=%s" % (HAVE_FITZ, HAVE_PYPDF),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="scaffold a library")
    p.add_argument("--root", required=True)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("fetch", help="download + validate + file a paper")
    p.add_argument("arxiv_id")
    p.add_argument("--venue", required=True, help='e.g. "ICLR 2025"')
    p.add_argument("--title", required=True, help="full title, colons removed")
    p.add_argument("--version", default="", help="e.g. v2")
    p.add_argument("--root", default=None)
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("text", help="dump text, page by page")
    p.add_argument("pdf")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--pages", default="", help="e.g. 3,4-7")
    p.set_defaults(func=cmd_text)

    p = sub.add_parser("toc", help="list every section heading")
    p.add_argument("pdf")
    p.set_defaults(func=cmd_toc)

    p = sub.add_parser("figures", help="crop figures by caption anchors")
    p.add_argument("pdf")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--scale", type=float, default=3.0)
    p.set_defaults(func=cmd_figures)

    p = sub.add_parser("check", help="validate an HTML deliverable")
    p.add_argument("html")
    p.set_defaults(func=cmd_check)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
