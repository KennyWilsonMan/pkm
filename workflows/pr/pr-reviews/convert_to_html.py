#!/usr/bin/env python3
"""
Convert Markdown PR review to HTML with rendered PlantUML diagrams.
"""

import re
import base64
import zlib
import urllib.parse
import sys
from pathlib import Path


def plantuml_encode(plantuml_text):
    """Encode PlantUML text for use in PlantUML server URL."""
    # PlantUML encoding: deflate -> base64 -> translate characters
    zlibbed_str = zlib.compress(plantuml_text.encode('utf-8'))
    compressed = zlibbed_str[2:-4]  # Remove zlib header and checksum

    # Custom base64-like encoding used by PlantUML
    plantuml_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    base64_alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    b64 = base64.b64encode(compressed).decode('utf-8')
    encoded = ''
    for char in b64:
        if char in base64_alphabet:
            encoded += plantuml_alphabet[base64_alphabet.index(char)]
        else:
            encoded += char

    return encoded


def extract_and_render_plantuml(markdown_text):
    """Extract PlantUML blocks and replace with rendered images."""

    # Pattern to match PlantUML code blocks
    pattern = r'```plantuml\n(.*?)```'

    def replace_plantuml(match):
        plantuml_code = match.group(1)

        # Encode the PlantUML code
        encoded = plantuml_encode(plantuml_code)

        # Generate URL to PlantUML server (using SVG format)
        plantuml_url = f"https://www.plantuml.com/plantuml/svg/{encoded}"

        # Return HTML img tag
        return f'<img src="{plantuml_url}" alt="PlantUML Diagram" style="max-width: 100%; height: auto;">'

    # Replace all PlantUML blocks
    html_text = re.sub(pattern, replace_plantuml, markdown_text, flags=re.DOTALL)

    return html_text


def markdown_to_html(markdown_text):
    """Convert markdown to HTML with basic formatting."""

    html = markdown_text

    # Headers
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

    # Code blocks with diff highlighting
    def format_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)

        if lang == 'diff':
            # Apply diff-specific formatting
            lines = code.split('\n')
            formatted_lines = []
            for line in lines:
                if line.startswith('+') and not line.startswith('+++'):
                    formatted_lines.append(f'<span style="background-color: #e6ffec; color: #24292e; display: block;">{line}</span>')
                elif line.startswith('-') and not line.startswith('---'):
                    formatted_lines.append(f'<span style="background-color: #ffebe9; color: #24292e; display: block;">{line}</span>')
                elif line.startswith('@@'):
                    formatted_lines.append(f'<span style="color: #0969da; display: block;">{line}</span>')
                else:
                    formatted_lines.append(f'<span style="display: block;">{line}</span>')
            return f'<pre><code class="diff">{"".join(formatted_lines)}</code></pre>'
        else:
            return f'<pre><code class="{lang}">{code}</code></pre>'

    html = re.sub(r'```(\w+)?\n(.*?)```', format_code_block, html, flags=re.DOTALL)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)

    # Lists (basic)
    lines = html.split('\n')
    in_list = False
    result = []

    for line in lines:
        if re.match(r'^\s*[-*]\s+', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = re.sub(r'^\s*[-*]\s+', '', line)
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)

    if in_list:
        result.append('</ul>')

    html = '\n'.join(result)

    # Paragraphs (basic)
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = '<p>' + html + '</p>'
    html = html.replace('<p><h', '<h').replace('</h1></p>', '</h1>')
    html = html.replace('</h2></p>', '</h2>').replace('</h3></p>', '</h3>')
    html = html.replace('</h4></p>', '</h4>')
    html = html.replace('<p><pre>', '<pre>').replace('</pre></p>', '</pre>')
    html = html.replace('<p><ul>', '<ul>').replace('</ul></p>', '</ul>')
    html = html.replace('<p><img', '<img').replace('"></p>', '">')
    html = html.replace('<p></p>', '')

    return html


def create_html_document(title, body_html):
    """Create a complete HTML document with styling."""

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f6f8fa;
            color: #24292e;
        }}

        h1 {{
            border-bottom: 3px solid #0366d6;
            padding-bottom: 10px;
            color: #0366d6;
        }}

        h2 {{
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 8px;
            margin-top: 30px;
            color: #0366d6;
        }}

        h3 {{
            margin-top: 25px;
            color: #24292e;
        }}

        h4 {{
            margin-top: 20px;
            color: #586069;
        }}

        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid #e1e4e8;
            line-height: 1.45;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 12px;
        }}

        pre code.diff {{
            display: block;
        }}

        pre code.diff span {{
            padding: 0 10px;
            margin: 0;
        }}

        a {{
            color: #0366d6;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        ul {{
            padding-left: 30px;
        }}

        li {{
            margin: 8px 0;
        }}

        strong {{
            color: #24292e;
            font-weight: 600;
        }}

        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        hr {{
            border: 0;
            border-top: 2px solid #e1e4e8;
            margin: 30px 0;
        }}

        .critical {{
            color: #d73a49;
        }}

        .warning {{
            color: #f9c513;
        }}

        .info {{
            color: #0366d6;
        }}

        .success {{
            color: #28a745;
        }}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""

    return html_template


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_to_html.py <markdown_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Read markdown file
    print(f"Reading {input_file}...")
    markdown_content = input_file.read_text(encoding='utf-8')

    # Extract title from first header
    title_match = re.search(r'^# (.*)$', markdown_content, re.MULTILINE)
    title = title_match.group(1) if title_match else "PR Review"

    # Process PlantUML diagrams
    print("Processing PlantUML diagrams...")
    html_content = extract_and_render_plantuml(markdown_content)

    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    html_body = markdown_to_html(html_content)

    # Create complete HTML document
    html_document = create_html_document(title, html_body)

    # Write output file
    output_file = input_file.with_suffix('.html')
    print(f"Writing {output_file}...")
    output_file.write_text(html_document, encoding='utf-8')

    print(f"✅ Conversion complete! Output: {output_file}")

    return str(output_file)


if __name__ == "__main__":
    main()
