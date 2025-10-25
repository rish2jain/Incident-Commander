#!/usr/bin/env python3
"""
Convert simplified judge guide to PDF with Mermaid diagrams
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
            ['npx', '-y', '@mermaid-js/mermaid-cli', '-i', mmd_file, '-o', output_path, '-b', 'transparent', '-w', '1200'],
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

        print(f"  📊 Rendering diagram {diagram_count}...")
        if render_mermaid_to_png(mermaid_code, png_path):
            # Convert to base64 for embedding
            import base64
            with open(png_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            return f'<div style="page-break-inside: avoid; text-align: center; margin: 20px 0;"><img src="data:image/png;base64,{img_data}" style="max-width: 95%; height: auto;" /></div>'
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
            @bottom-center {
                content: "SwarmAI - AWS Generative AI Hackathon";
                font-size: 8pt;
                color: #999;
            }
            @bottom-right {
                content: "Page " counter(page);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }

        h1 {
            color: #0066cc;
            font-size: 24pt;
            margin-top: 24pt;
            margin-bottom: 12pt;
            page-break-after: avoid;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 8pt;
        }

        h2 {
            color: #0066cc;
            font-size: 18pt;
            margin-top: 20pt;
            margin-bottom: 10pt;
            page-break-after: avoid;
            background-color: #f0f8ff;
            padding: 8px 12px;
            border-left: 4px solid #0066cc;
        }

        h3 {
            color: #333;
            font-size: 14pt;
            margin-top: 14pt;
            margin-bottom: 8pt;
            page-break-after: avoid;
        }

        h4 {
            color: #333;
            font-size: 12pt;
            margin-top: 12pt;
            margin-bottom: 6pt;
            page-break-after: avoid;
        }

        code {
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            color: #c7254e;
        }

        pre {
            background-color: #f8f8f8;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid #0066cc;
            overflow-x: auto;
            font-size: 9pt;
            line-height: 1.4;
            margin: 12px 0;
            page-break-inside: avoid;
        }

        pre code {
            background-color: transparent;
            padding: 0;
            color: #333;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
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
            padding-left: 15px;
            margin-left: 0;
            color: #666;
            font-style: italic;
            margin: 12px 0;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }

        li {
            margin: 5px 0;
        }

        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 20px 0;
            page-break-after: avoid;
        }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px auto;
        }

        strong {
            color: #000;
            font-weight: bold;
        }

        em {
            font-style: italic;
        }

        /* Checkboxes */
        input[type="checkbox"] {
            margin-right: 8px;
        }

        /* Highlight boxes */
        .highlight {
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 12px;
            margin: 12px 0;
        }
        """

        # Wrap HTML with proper structure and cover page
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SwarmAI - Judge Evaluation Guide</title>
        </head>
        <body>
            <div style="page-break-after: always; text-align: center; padding-top: 200px;">
                <h1 style="font-size: 36pt; color: #0066cc; border: none; margin-bottom: 20pt;">
                    SwarmAI
                </h1>
                <p style="font-size: 18pt; color: #666; margin-bottom: 40pt;">
                    Autonomous Incident Commander
                </p>
                <p style="font-size: 14pt; color: #333; margin-bottom: 60pt;">
                    <strong>AWS Generative AI Hackathon</strong><br/>
                    Judge Evaluation Guide
                </p>
                <div style="background-color: #f0f8ff; padding: 20px; border-radius: 8px; display: inline-block; text-align: left;">
                    <p style="margin: 5px 0;"><strong>✅ Live Dashboards:</strong> d2j5829zuijr97.cloudfront.net</p>
                    <p style="margin: 5px 0;"><strong>🎯 MTTR Reduction:</strong> 95.2% (30min → 1.4min)</p>
                    <p style="margin: 5px 0;"><strong>💰 Annual Savings:</strong> $2.8M (458% ROI)</p>
                    <p style="margin: 5px 0;"><strong>🤖 AWS AI Services:</strong> 2/8 Production, 6/8 Planned</p>
                </div>
            </div>
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

        # Count pages (approximate)
        from PyPDF2 import PdfReader
        try:
            reader = PdfReader(output_pdf)
            print(f"📄 Pages: {len(reader.pages)}")
        except:
            pass

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
    input_file = "hackathon/SIMPLIFIED_JUDGE_GUIDE.md"
    output_file = "hackathon/SwarmAI_Judge_Guide_Simple.pdf"

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    print("🚀 Creating simplified judge-friendly PDF...")
    success = convert_markdown_to_pdf(input_file, output_file)

    if success:
        print("\n✅ Judge-friendly PDF ready!")
        print(f"📄 Location: {os.path.abspath(output_file)}")
        print("\nThis PDF includes:")
        print("  ✓ Quick summary and access links")
        print("  ✓ Architecture diagrams (visual)")
        print("  ✓ Key innovations explained")
        print("  ✓ Evaluation checklist")
        print("  ✓ Testing instructions")

    sys.exit(0 if success else 1)
