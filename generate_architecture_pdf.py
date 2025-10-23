#!/usr/bin/env python3
"""
Generate Architecture PDF from Markdown
Converts the architecture diagrams markdown to a professional PDF
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

def generate_pdf():
    """Generate PDF from architecture markdown"""

    # Read the markdown file
    md_file = Path("SYSTEM_ARCHITECTURE_DIAGRAMS.md")
    output_pdf = Path("SwarmAI_Architecture_Diagrams.pdf")

    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return False

    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert mermaid blocks to text (since PDF can't render them)
    # We'll replace mermaid diagrams with notes about viewing in GitHub
    md_content = md_content.replace('```mermaid', '```\n[Interactive Diagram - View in GitHub]')

    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.toc',
            'markdown.extensions.attr_list'
        ]
    )

    # Create full HTML document with styling
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SwarmAI - System Architecture Diagrams</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
            @bottom-center {{
                content: counter(page);
            }}
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
        }}

        h1 {{
            color: #FF9900;
            border-bottom: 3px solid #FF9900;
            padding-bottom: 10px;
            margin-top: 30px;
            page-break-before: avoid;
        }}

        h2 {{
            color: #232F3E;
            border-bottom: 2px solid #ccc;
            padding-bottom: 8px;
            margin-top: 25px;
            page-break-before: auto;
            page-break-after: avoid;
        }}

        h3 {{
            color: #FF9900;
            margin-top: 20px;
            page-break-after: avoid;
        }}

        pre {{
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            font-size: 12px;
            page-break-inside: avoid;
        }}

        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 90%;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}

        th {{
            background-color: #FF9900;
            color: white;
            font-weight: bold;
        }}

        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}

        li {{
            margin: 8px 0;
        }}

        blockquote {{
            border-left: 4px solid #FF9900;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
            font-style: italic;
        }}

        .cover {{
            text-align: center;
            padding: 100px 0;
            page-break-after: always;
        }}

        .cover h1 {{
            font-size: 48px;
            color: #FF9900;
            margin-bottom: 20px;
            border: none;
        }}

        .cover h2 {{
            font-size: 32px;
            color: #232F3E;
            margin-bottom: 40px;
            border: none;
        }}

        .cover p {{
            font-size: 18px;
            color: #666;
            margin: 10px 0;
        }}

        .diagram-note {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
            color: #856404;
        }}

        .diagram-note::before {{
            content: "📊 Interactive Diagram: ";
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>SwarmAI</h1>
        <h2>System Architecture Diagrams</h2>
        <p><strong>Autonomous Incident Commander</strong></p>
        <p>AI-Powered Multi-Agent System for Zero-Touch Incident Resolution</p>
        <p style="margin-top: 60px; color: #999;">
            Complete AWS AI Integration (8/8 Services)<br>
            Byzantine Fault-Tolerant Architecture<br>
            95.2% MTTR Improvement | $2.8M Annual Savings
        </p>
        <p style="margin-top: 40px; font-size: 14px;">
            Version 1.0 | October 23, 2025
        </p>
    </div>

    <div class="diagram-note" style="margin: 30px 0;">
        <p><strong>Note:</strong> This PDF contains text-based architecture documentation.
        Interactive Mermaid diagrams are best viewed in the GitHub repository at
        <code>SYSTEM_ARCHITECTURE_DIAGRAMS.md</code> where they render as visual flowcharts.</p>
    </div>

    {html_content}
</body>
</html>
"""

    # Generate PDF
    try:
        HTML(string=full_html).write_pdf(
            output_pdf,
            stylesheets=[],
            presentational_hints=True
        )
        print(f"✅ PDF generated successfully: {output_pdf}")
        print(f"📄 File size: {output_pdf.stat().st_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    generate_pdf()
