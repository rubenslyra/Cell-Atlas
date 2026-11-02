#!/usr/bin/env python
"""Static checks for the GitHub Pages bundle.

This guard exists because a corrupted docs/index.html (a pasted diff dump) was
once deployed. For every HTML page under docs/ it fails the build on structural
HTML errors, unresolved local assets/anchors, mojibake, inline code that the
page's own Content-Security-Policy would block, and unsafe CSP directives.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

DOCS = Path(__file__).resolve().parents[1] / "docs"

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}

# Tags that are commonly self-closed in HTML5 serialization.
SELF_CLOSING = {
    "path", "circle", "ellipse", "rect", "line", "polyline", "polygon",
    "stop", "use", "g",
}

FORBIDDEN_MARKERS = (
    "# PR Title",
    "diff --git",
    "@@ -",
    "```",
    "\ufffd",
)

# UTF-8 text decoded as Latin-1/cp1252 turns accented Portuguese into sequences
# such as "├º" (ç) or "├ú" (ú). Box-drawing characters alone are legitimate.
MOJIBAKE_SUFFIXES = "ºáàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ"

REMOTE_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "data:")


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.references: list[tuple[str, str, int]] = []
        self.images_without_alt: list[int] = []
        self.has_lang = False
        self.has_csp = False
        self.csp_content = ""
        self.inline_scripts: list[int] = []
        self.inline_handlers: list[tuple[int, str]] = []
        self.style_attrs: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        line = self.getpos()[0]

        if tag == "html" and attributes.get("lang"):
            self.has_lang = True

        if tag == "meta" and (attributes.get("http-equiv") or "").lower() == "content-security-policy":
            self.has_csp = True
            self.csp_content = attributes.get("content") or ""

        if attributes.get("id"):
            self.ids.add(attributes["id"])

        if tag == "script" and not attributes.get("src"):
            self.inline_scripts.append(line)
        for name in attributes:
            if name.startswith("on"):
                self.inline_handlers.append((line, name))
        if "style" in attributes:
            self.style_attrs.append(line)

        if tag == "img" and attributes.get("alt") is None:
            self.images_without_alt.append(line)

        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append((attribute, value, line))

        if tag in VOID_ELEMENTS:
            return
        self.stack.append((tag, line))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "img" and attributes.get("alt") is None:
            self.images_without_alt.append(self.getpos()[0])
        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value:
                self.references.append((attribute, value, self.getpos()[0]))
        # Self-closing non-void elements are only accepted for SVG primitives.
        if tag in VOID_ELEMENTS or tag in SELF_CLOSING:
            return
        self.errors.append(f"line {self.getpos()[0]}: <{tag}/> self-closed but is not void")

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_ELEMENTS:
            return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: unexpected </{tag}>")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return

        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                unclosed = ", ".join(name for name, _ in self.stack[index + 1:])
                self.errors.append(
                    f"line {self.getpos()[0]}: </{tag}> closes while unclosed: {unclosed}"
                )
                del self.stack[index:]
                return

        self.errors.append(f"line {self.getpos()[0]}: </{tag}> without matching opening tag")


def is_local(reference: str) -> bool:
    return not reference.startswith(REMOTE_PREFIXES)


def csp_directives(content: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for part in content.split(";"):
        tokens = part.split()
        if tokens:
            directives[tokens[0].lower()] = tokens[1:]
    return directives


def check_page(page: Path) -> tuple[list[str], int]:
    rel = page.relative_to(DOCS).as_posix()
    raw = page.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"{rel}: not valid UTF-8: {error}"], 0

    parser = DocumentParser()
    parser.feed(text)
    parser.close()

    errors = [f"{rel}: {e}" for e in parser.errors]
    for tag, line in parser.stack:
        errors.append(f"{rel}: line {line}: <{tag}> was never closed")

    for marker in FORBIDDEN_MARKERS:
        if marker in text:
            errors.append(f"{rel}: forbidden artifact: {marker!r}")

    for index, character in enumerate(text):
        following = text[index + 1:index + 2]
        if character == "\u251c" and following and following in MOJIBAKE_SUFFIXES:
            errors.append(f"{rel}: mojibake sequence near character {index}: {text[index:index + 12]!r}")
            break

    if not parser.has_lang:
        errors.append(f"{rel}: <html> is missing the lang attribute")

    if not parser.has_csp:
        errors.append(f"{rel}: missing Content-Security-Policy meta tag")
    else:
        csp = csp_directives(parser.csp_content)
        if "frame-ancestors" in csp:
            errors.append(f"{rel}: frame-ancestors is ignored in <meta>; move it to an HTTP header")
        script_src = csp.get("script-src", csp.get("default-src", []))
        style_src = csp.get("style-src", csp.get("default-src", []))
        for bad in ("'unsafe-inline'", "'unsafe-eval'"):
            if bad in script_src:
                errors.append(f"{rel}: script-src must not allow {bad}")
        for line in parser.inline_scripts:
            errors.append(f"{rel}: line {line}: inline <script> is blocked by CSP; use a file")
        for line, name in parser.inline_handlers:
            errors.append(f"{rel}: line {line}: inline handler {name}= is blocked by CSP")
        if "'unsafe-inline'" not in style_src:
            for line in parser.style_attrs:
                errors.append(f"{rel}: line {line}: style= attribute is blocked by this page's CSP")

    for line in parser.images_without_alt:
        errors.append(f"{rel}: line {line}: <img> without alt attribute")

    for attribute, reference, line in parser.references:
        if not is_local(reference):
            continue
        parsed = urlparse(reference)
        if parsed.scheme or parsed.netloc:
            continue
        if reference.startswith("#"):
            target = unquote(reference[1:])
            if target and target not in parser.ids:
                errors.append(f"{rel}: line {line}: {attribute}={reference!r} points to a missing id")
            continue
        target = unquote(parsed.path)
        if not target:
            continue
        resolved = (page.parent / target).resolve()
        if resolved.is_dir():
            resolved = resolved / "index.html"
        if DOCS.resolve() not in resolved.parents and resolved != DOCS.resolve():
            errors.append(f"{rel}: line {line}: {attribute}={reference!r} escapes docs/")
        elif not resolved.exists():
            errors.append(f"{rel}: line {line}: {attribute}={reference!r} does not exist")

    return errors, len(parser.references)


def main() -> int:
    if not (DOCS / "index.html").is_file():
        print("ERROR: docs/index.html is missing", file=sys.stderr)
        return 1

    pages = sorted(DOCS.rglob("*.html"))
    errors: list[str] = []
    references = 0
    for page in pages:
        page_errors, page_refs = check_page(page)
        errors.extend(page_errors)
        references += page_refs

    if errors:
        print(f"docs check failed ({len(errors)} issue(s)):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"docs check passed: {len(pages)} page(s), {references} references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
