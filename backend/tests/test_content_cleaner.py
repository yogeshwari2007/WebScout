import pytest
from app.utils.content_cleaner import clean_html, extract_title


def test_extract_title_priorities():
    """Verifies title is extracted from title tag or fallback meta/headings."""
    html_with_title = "<html><head><title>Page Title - Review</title></head><body><h1>Heading</h1></body></html>"
    title, _ = clean_html(html_with_title)
    assert title == "Page Title - Review"

    html_with_og = '<html><head><meta property="og:title" content="OpenGraph Title" /></head><body></body></html>'
    title, _ = clean_html(html_with_og)
    assert title == "OpenGraph Title"

    html_with_h1 = "<html><body><h1>Main H1 Header</h1></body></html>"
    title, _ = clean_html(html_with_h1)
    assert title == "Main H1 Header"


def test_clean_html_strips_scripts_styles_and_boilerplate():
    """Ensures scripts, styles, navigations, footers, ads, and modals are stripped."""
    sample_html = """
    <html>
      <head>
        <title>Tech Specs</title>
        <style>body { color: red; }</style>
        <script>alert("tracker");</script>
      </head>
      <body>
        <nav><a href="/home">Home</a><a href="/about">About</a></nav>
        <header>Header content</header>
        <div class="cookie-banner-modal">Please accept cookies to continue!</div>
        <div class="ad-container">Buy this product now!</div>
        <main>
          <h1>Apple MacBook Air M3</h1>
          <p>The MacBook Air with M3 chip delivers exceptional performance.</p>
          <div class="newsletter-popup">Subscribe to our newsletter</div>
          <h2>Specifications</h2>
          <ul>
            <li>8-core CPU</li>
            <li>16GB Unified Memory</li>
          </ul>
          <table>
            <tr><th>Component</th><th>Details</th></tr>
            <tr><td>Battery</td><td>18 hours</td></tr>
          </table>
        </main>
        <footer>Copyright 2026. All rights reserved.</footer>
      </body>
    </html>
    """
    title, text = clean_html(sample_html)

    assert title == "Tech Specs"
    # Ensure content is present
    assert "Apple MacBook Air M3" in text
    assert "8-core CPU" in text
    assert "18 hours" in text

    # Ensure unwanted noise is completely stripped
    assert "alert" not in text
    assert "tracker" not in text
    assert "body { color: red; }" not in text
    assert "cookie" not in text.lower()
    assert "newsletter" not in text.lower()
    assert "Home About" not in text
    assert "Copyright 2026" not in text


def test_character_cap_enforcement():
    """Verifies that text exceeding 12,000 characters is cleanly truncated."""
    long_paragraph = "<p>" + ("word " * 3000) + "</p>"
    html = f"<html><head><title>Long Document</title></head><body>{long_paragraph}</body></html>"
    _, text = clean_html(html, max_chars=12000)

    assert len(text) <= 12005
    assert text.endswith("...")


def test_empty_content_handling():
    """Verifies that empty or near-empty HTML returns empty text."""
    _, text = clean_html("<html><body>   </body></html>")
    assert text == ""

    _, text = clean_html("<script>console.log(1);</script>")
    assert text == ""
