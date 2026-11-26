"""
Content Cleaning and Extraction Engine.

Extracts page titles, structured headings, readable paragraphs, lists, and tables
from rendered HTML using BeautifulSoup4, while removing scripts, styles, navigations,
ads, cookie overlays, and boilerplate. Enforces a 12,000-character cap.
"""

import re
from typing import Optional, Tuple
from bs4 import BeautifulSoup, Comment, Tag

# Elements to completely strip from DOM
STRIP_TAGS = {
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "svg",
    "canvas",
    "iframe",
    "object",
    "embed",
    "dialog",
    "template",
    "button",
    "input",
    "textarea",
    "select",
    "video",
    "audio",
    "picture",
    "source",
}

# Regex pattern for stripping ads, cookie banners, modals, and overlays by class/id
BOILERPLATE_ATTR_PATTERN = re.compile(
    r"(cookie|consent|banner|advert|ad-|ads-|popup|modal|overlay|newsletter|share-btn|tracking|social-share)",
    re.IGNORECASE,
)

# Common block elements containing actual text
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def extract_title(soup: BeautifulSoup) -> str:
    """
    Extracts the best possible title from the HTML document:
    1. <title>
    2. OpenGraph / Twitter meta tags
    3. First <h1> tag
    """
    if soup.title and soup.title.string:
        clean = soup.title.string.strip()
        if clean:
            return clean

    og_title = soup.find("meta", property="og:title")
    if og_title and isinstance(og_title, Tag) and og_title.get("content"):
        clean = str(og_title["content"]).strip()
        if clean:
            return clean

    twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
    if twitter_title and isinstance(twitter_title, Tag) and twitter_title.get("content"):
        clean = str(twitter_title["content"]).strip()
        if clean:
            return clean

    h1 = soup.find("h1")
    if h1:
        clean = h1.get_text(strip=True)
        if clean:
            return clean

    return "Untitled Document"


def clean_html(html: str, max_chars: int = 12000) -> Tuple[str, str]:
    """
    Cleans raw rendered HTML and extracts structured, readable plain text.

    Args:
        html: Raw or rendered HTML string.
        max_chars: Maximum character length allowed (defaults to 12,000).

    Returns:
        (title: str, cleaned_text: str)
    """
    if not html or not html.strip():
        return "Untitled Document", ""

    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract title before stripping elements
    title = extract_title(soup)

    # 2. Remove all HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 3. Remove non-content tags
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    # 4. Remove elements matching ad/cookie/modal heuristics by class or ID
    for el in soup.find_all(attrs={"class": BOILERPLATE_ATTR_PATTERN}):
        el.decompose()
    for el in soup.find_all(attrs={"id": BOILERPLATE_ATTR_PATTERN}):
        el.decompose()

    # 5. Identify primary content container if available
    root = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )

    # 6. Extract structured content block-by-block
    blocks = []
    seen_texts = set()

    for elem in root.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote"]):
        tag_name = elem.name.lower()
        raw_text = elem.get_text(separator=" ", strip=True)

        if not raw_text or len(raw_text) < 3:
            continue

        # Simple deduplication of identical adjacent sentences or repeated headers
        normalized_check = raw_text.lower()
        if normalized_check in seen_texts:
            continue
        seen_texts.add(normalized_check)

        # Format according to element type
        if tag_name in HEADING_TAGS:
            level = tag_name[1]
            prefix = "#" * int(level)
            blocks.append(f"\n{prefix} {raw_text}\n")
        elif tag_name == "li":
            blocks.append(f"• {raw_text}")
        elif tag_name == "tr":
            cells = [cell.get_text(strip=True) for cell in elem.find_all(["th", "td"])]
            if cells:
                blocks.append(" | ".join(cells))
        elif tag_name == "blockquote":
            blocks.append(f"> {raw_text}")
        else:
            # Paragraph
            blocks.append(raw_text)

    # If structured block extraction found very little, fallback to root get_text
    if len(blocks) < 2:
        raw_text = root.get_text(separator="\n", strip=True)
        blocks = [raw_text]

    # Combine and clean whitespace
    combined = "\n\n".join(blocks)
    # Collapse multiple blank lines
    combined = re.sub(r"\n{3,}", "\n\n", combined)
    # Collapse multiple inline spaces
    combined = re.sub(r"[ \t]+", " ", combined).strip()

    # Apply 12,000 character cap cleanly
    if len(combined) > max_chars:
        # Truncate at last word boundary before cap
        truncated = combined[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.9:
            truncated = truncated[:last_space]
        combined = truncated.strip() + "..."

    return title, combined
