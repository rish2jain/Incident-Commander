#!/usr/bin/env python3
"""
Convert combined markdown to PDF using markdown2 and weasyprint
"""

import sys
import os

def convert_markdown_to_pdf(input_md: str, output_pdf: str):
    """Convert markdown file to PDF"""
    try:
        import markdown2
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        # Read markdown content
        with open(input_md, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert markdown to HTML
        html_content = markdown2.markdown(
            md_content,
            extras=[
                'fenced-code-blocks',
                'tables',
                'break-on-newline',
                'header-ids',
                'code-friendly'
            ]
        )

        # Add CSS styling for better PDF appearance
        css_content = """
        @page {
            size: letter;
            margin: 1in;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
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
            page-break-before: always;
        }

        h1:first-of-type {
            page-break-before: avoid;
        }

        h2 {
            color: #0066cc;
            font-size: 18pt;
            margin-top: 18pt;
            margin-bottom: 10pt;
        }

        h3 {
            color: #333;
            font-size: 14pt;
            margin-top: 14pt;
            margin-bottom: 8pt;
        }

        code {
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }

        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #0066cc;
            overflow-x: auto;
            font-size: 9pt;
        }

        pre code {
            background-color: transparent;
            padding: 0;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 10pt;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #0066cc;
            color: white;
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
        }
        """

        # Wrap HTML with proper structure
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SwarmAI Hackathon Submission</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Convert HTML to PDF
        font_config = FontConfiguration()
        html_obj = HTML(string=full_html)
        css_obj = CSS(string=css_content, font_config=font_config)

        html_obj.write_pdf(output_pdf, stylesheets=[css_obj], font_config=font_config)

        print(f"✅ PDF created successfully: {output_pdf}")
        return True

    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown2", "weasyprint"])
        print("✅ Packages installed. Please run the script again.")
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

    success = convert_markdown_to_pdf(input_file, output_file)
    sys.exit(0 if success else 1)
