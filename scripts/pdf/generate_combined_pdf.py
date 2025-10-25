#!/usr/bin/env python3
"""
Generate Combined PDF - Judge Instructions + Architecture Diagrams
Creates a comprehensive submission document with all materials
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import re
import base64

def render_mermaid_to_image(mermaid_code):
    """Convert Mermaid code to image using Mermaid.ink API"""
    try:
        # Encode mermaid code for URL
        encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')

        # Use mermaid.ink service to render diagram
        img_url = f"https://mermaid.ink/img/{encoded}"

        return img_url
    except Exception as e:
        print(f"⚠️  Warning: Could not render mermaid diagram: {e}")
        return None

def process_mermaid_diagrams(md_content):
    """Extract and replace mermaid diagrams with rendered images"""

    # Pattern to match mermaid code blocks
    mermaid_pattern = r'```mermaid\n(.*?)```'

    diagram_counter = 0

    def replace_mermaid(match):
        nonlocal diagram_counter
        diagram_counter += 1

        mermaid_code = match.group(1)
        img_url = render_mermaid_to_image(mermaid_code)

        if img_url:
            return f'<div class="mermaid-diagram"><img src="{img_url}" alt="Architecture Diagram {diagram_counter}" style="max-width: 100%; height: auto;"/></div>'
        else:
            # Fallback to code block if rendering fails
            return f'<pre class="mermaid-code">{mermaid_code}</pre>'

    # Replace all mermaid blocks
    processed_content = re.sub(mermaid_pattern, replace_mermaid, md_content, flags=re.DOTALL)

    if diagram_counter > 0:
        print(f"📊 Processed {diagram_counter} Mermaid diagrams")

    return processed_content

def generate_combined_pdf():
    """Generate combined PDF from judge instructions and architecture diagrams"""

    # Read both markdown files
    instructions_file = Path("JUDGE_REVIEW_INSTRUCTIONS.md")
    architecture_file = Path("SYSTEM_ARCHITECTURE_DIAGRAMS.md")
    output_pdf = Path("SwarmAI_Complete_Submission.pdf")

    if not instructions_file.exists():
        print(f"Error: {instructions_file} not found")
        return False

    if not architecture_file.exists():
        print(f"Error: {architecture_file} not found")
        return False

    # Read markdown content
    print("📖 Reading judge instructions...")
    with open(instructions_file, 'r', encoding='utf-8') as f:
        instructions_content = f.read()

    print("📖 Reading architecture diagrams...")
    with open(architecture_file, 'r', encoding='utf-8') as f:
        architecture_content = f.read()

    # Process mermaid diagrams in architecture content
    print("🔄 Processing Mermaid diagrams...")
    architecture_content = process_mermaid_diagrams(architecture_content)

    # Convert both to HTML
    instructions_html = markdown.markdown(
        instructions_content,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.toc',
            'markdown.extensions.attr_list'
        ]
    )

    architecture_html = markdown.markdown(
        architecture_content,
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
    <title>SwarmAI - Complete Submission Package</title>
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
            font-size: 11px;
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
            font-size: 12px;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
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

        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }}

        .section-divider {{
            page-break-before: always;
            text-align: center;
            padding: 80px 0;
            background: linear-gradient(135deg, #232F3E 0%, #FF9900 100%);
            color: white;
            margin: 0 -2.5cm;
            padding-left: 2.5cm;
            padding-right: 2.5cm;
        }}

        .section-divider h1 {{
            color: white;
            border: none;
            font-size: 42px;
            margin: 0;
        }}

        .section-divider p {{
            color: #fff;
            font-size: 20px;
            margin-top: 20px;
        }}

        .mermaid-diagram {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            page-break-inside: avoid;
        }}

        .mermaid-diagram img {{
            max-width: 100%;
            height: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .mermaid-code {{
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            font-size: 11px;
            page-break-inside: avoid;
        }}

        /* Checkbox styling */
        input[type="checkbox"] {{
            margin-right: 8px;
        }}

        /* Alert boxes */
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            page-break-inside: avoid;
        }}

        /* Code blocks in lists */
        li > code {{
            white-space: normal;
        }}

        /* TOC styling */
        .toc {{
            background-color: #f8f9fa;
            border: 2px solid #FF9900;
            border-radius: 8px;
            padding: 30px;
            margin: 40px 0;
            page-break-inside: avoid;
        }}

        .toc h2 {{
            color: #FF9900;
            border: none;
            margin-top: 0;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>SwarmAI</h1>
        <h2>Complete Submission Package</h2>
        <p><strong>Autonomous Incident Commander</strong></p>
        <p>AI-Powered Multi-Agent System for Zero-Touch Incident Resolution</p>
        <p style="margin-top: 60px; color: #999;">
            Complete AWS AI Integration (8/8 Services)<br>
            Byzantine Fault-Tolerant Architecture<br>
            95.2% MTTR Improvement | $2.8M Annual Savings
        </p>
        <p style="margin-top: 40px; font-size: 16px; color: #FF9900;">
            <strong>Judge Review Instructions + System Architecture</strong>
        </p>
        <p style="margin-top: 40px; font-size: 14px;">
            Version 1.0 | October 23, 2025
        </p>
    </div>

    <div class="toc">
        <h2>📋 Document Contents</h2>
        <h3>Part 1: Judge Review Instructions</h3>
        <ul>
            <li>Executive Summary & Key Highlights</li>
            <li>Quick Start Options (4 Methods)</li>
            <li>System Architecture Review</li>
            <li>Technical Evaluation Guide</li>
            <li>Business Value Assessment</li>
            <li>Interactive Demo Scenarios</li>
            <li>AWS AI Integration Verification</li>
            <li>Evaluation Checklist</li>
            <li>Prize Category Eligibility</li>
        </ul>
        <h3>Part 2: System Architecture Diagrams</h3>
        <ul>
            <li>High-Level System Architecture</li>
            <li>Multi-Agent Coordination Flow</li>
            <li>AWS AI Services Integration</li>
            <li>Data Flow Architecture</li>
            <li>Deployment Architecture</li>
            <li>Security Architecture</li>
            <li>Business Impact Visualization</li>
        </ul>
    </div>

    <!-- Part 1: Judge Review Instructions -->
    {instructions_html}

    <!-- Section Divider -->
    <div class="section-divider">
        <h1>Part 2</h1>
        <p>System Architecture Diagrams</p>
    </div>

    <!-- Part 2: Architecture Diagrams -->
    {architecture_html}

</body>
</html>
"""

    # Generate PDF
    try:
        print("📄 Generating combined PDF...")
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
    generate_combined_pdf()
