#!/usr/bin/env python3
"""
Convert combined markdown to PDF with Mermaid diagram rendering
"""

import sys
import os
import re
import subprocess
import tempfile

def render_mermaid_to_png(mermaid_code: str, output_path: str) -> bool:
    """Render Mermaid diagram to PNG using mmdc CLI"""
    try:
        # Create temporary file for mermaid code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            f.write(mermaid_code)
            mmd_file = f.name

        # Render using mermaid-cli (mmdc)
        result = subprocess.run(
            ['npx', '-y', '@mermaid-js/mermaid-cli', '-i', mmd_file, '-o', output_path, '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )

        os.unlink(mmd_file)

        if result.returncode == 0:
            return True
        else:
            print(f"Warning: Mermaid rendering failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Warning: Could not render Mermaid diagram: {e}")
        return False

def process_mermaid_diagrams(md_content: str, temp_dir: str) -> str:
    """Replace Mermaid code blocks with PNG images"""
    diagram_count = 0

    def replace_mermaid(match):
        nonlocal diagram_count
        diagram_count += 1
        mermaid_code = match.group(1)

        png_path = os.path.join(temp_dir, f"mermaid_diagram_{diagram_count}.png")

        if render_mermaid_to_png(mermaid_code, png_path):
            # Convert to base64 for embedding
            import base64
            with open(png_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            return f'<img src="data:image/png;base64,{img_data}" style="max-width: 100%; height: auto;" />'
        else:
            # Fallback to code block if rendering fails
            return f'```\n{mermaid_code}\n```'

    # Replace Mermaid code blocks
    pattern = r'```mermaid\s*\n(.*?)```'
    processed_content = re.sub(pattern, replace_mermaid, md_content, flags=re.DOTALL)

    print(f"✅ Processed {diagram_count} Mermaid diagrams")
    return processed_content

def convert_markdown_to_pdf(input_md: str, output_pdf: str):
    """Convert markdown file to PDF with Mermaid support"""
    try:
        import markdown2
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        # Read markdown content
        with open(input_md, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Create temp directory for Mermaid diagrams
        temp_dir = tempfile.mkdtemp()

        # Process Mermaid diagrams
        print("🎨 Processing Mermaid diagrams...")
        md_content = process_mermaid_diagrams(md_content, temp_dir)

        # Convert markdown to HTML
        print("📄 Converting Markdown to HTML...")
        html_content = markdown2.markdown(
            md_content,
            extras=[
                'fenced-code-blocks',
                'tables',
                'break-on-newline',
                'header-ids',
                'code-friendly',
                'cuddled-lists'
            ]
        )

        # Add CSS styling for better PDF appearance
        css_content = """
        @page {
            size: letter;
            margin: 0.75in;
            @bottom-right {
                content: "Page " counter(page);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #333;
        }

        h1 {
            color: #0066cc;
            font-size: 22pt;
            margin-top: 20pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 5pt;
        }

        h2 {
            color: #0066cc;
            font-size: 16pt;
            margin-top: 16pt;
            margin-bottom: 8pt;
            page-break-after: avoid;
        }

        h3 {
            color: #333;
            font-size: 13pt;
            margin-top: 12pt;
            margin-bottom: 6pt;
            page-break-after: avoid;
        }

        h4 {
            color: #333;
            font-size: 11pt;
            margin-top: 10pt;
            margin-bottom: 5pt;
            page-break-after: avoid;
        }

        code {
            background-color: #f5f5f5;
            padding: 1px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
        }

        pre {
            background-color: #f8f8f8;
            padding: 8px;
            border-radius: 4px;
            border-left: 3px solid #0066cc;
            overflow-x: auto;
            font-size: 8pt;
            line-height: 1.4;
            margin: 10px 0;
            page-break-inside: avoid;
        }

        pre code {
            background-color: transparent;
            padding: 0;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
        }

        th {
            background-color: #0066cc;
            color: white;
            font-weight: bold;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        blockquote {
            border-left: 4px solid #0066cc;
            padding-left: 12px;
            margin-left: 0;
            color: #666;
            font-style: italic;
            margin: 10px 0;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        ul, ol {
            margin: 8px 0;
            padding-left: 25px;
        }

        li {
            margin: 4px 0;
        }

        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 15px 0;
        }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px auto;
            page-break-inside: avoid;
        }

        strong {
            color: #000;
        }

        em {
            font-style: italic;
        }
        """

        # Wrap HTML with proper structure
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SwarmAI - AWS Hackathon Submission</title>
        </head>
        <body>
            <h1 style="text-align: center; color: #0066cc; font-size: 28pt; margin-bottom: 30pt;">
                SwarmAI - Autonomous Incident Commander
            </h1>
            <p style="text-align: center; font-size: 14pt; color: #666; margin-bottom: 40pt;">
                AWS Generative AI Hackathon Submission<br/>
                <em>Byzantine Fault-Tolerant Multi-Agent System</em>
            </p>
            {html_content}
        </body>
        </html>
        """

        # Convert HTML to PDF
        print("🔄 Converting to PDF...")
        font_config = FontConfiguration()
        html_obj = HTML(string=full_html)
        css_obj = CSS(string=css_content, font_config=font_config)

        html_obj.write_pdf(output_pdf, stylesheets=[css_obj], font_config=font_config)

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        print(f"✅ PDF created successfully: {output_pdf}")

        # Get file size
        size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
        print(f"📦 File size: {size_mb:.2f} MB")

        return True

    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        return False
    except Exception as e:
        print(f"❌ Error converting to PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    input_file = "hackathon/COMBINED_HACKATHON_SUBMISSION.md"
    output_file = "hackathon/SwarmAI_Hackathon_Submission.pdf"

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    print("🚀 Starting PDF conversion with Mermaid diagram support...")
    success = convert_markdown_to_pdf(input_file, output_file)

    if success:
        print("\n✅ PDF submission ready!")
        print(f"📄 Location: {os.path.abspath(output_file)}")

    sys.exit(0 if success else 1)
