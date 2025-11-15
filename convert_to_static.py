#!/usr/bin/env python3
"""
Convert Flask templates to static HTML for Netlify deployment
"""
import os
import re
from pathlib import Path

def convert_template_to_static(template_path, output_path, base_content=None):
    """Convert a Flask template to static HTML"""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it extends base.html
    if '{% extends "base.html" %}' in content:
        if not base_content:
            # Read base.html
            base_path = template_path.parent / 'base.html'
            with open(base_path, 'r', encoding='utf-8') as f:
                base_content = f.read()
        
        # Extract title
        title_match = re.search(r'{%\s*block\s+title\s*%}(.*?){%\s*endblock\s*%}', content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else 'RBHS AIEP'
        
        # Extract content block
        content_match = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock\s*%}', content, re.DOTALL)
        page_content = content_match.group(1) if content_match else content
        
        # Replace blocks in base
        result = base_content.replace('{% block title %}{% endblock %}', title)
        result = result.replace('{% block content %}{% endblock %}', page_content)
        
        # Remove any remaining Jinja2 syntax
        result = re.sub(r'{%.*?%}', '', result)
        result = re.sub(r'{{.*?}}', '', result)
        
    else:
        # Standalone template
        result = content
        result = re.sub(r'{%.*?%}', '', result)
        result = re.sub(r'{{.*?}}', '', result)
    
    # Fix static file references
    result = result.replace('{{ url_for("static", filename=', '"/static/')
    result = result.replace('") }}', '"')
    
    # Fix route references
    result = result.replace('{{ url_for("', '"/')
    result = result.replace('") }}', '.html"')
    
    # Add API configuration script
    if '<head>' in result and 'config.js' not in result:
        result = result.replace('</head>', '  <script src="/config.js"></script>\n</head>')
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"✓ Converted {template_path.name} -> {output_path.name}")
    return result


def main():
    """Main conversion process"""
    # Paths
    templates_dir = Path('templates')
    output_dir = Path('netlify-deploy/public')
    static_src = Path('static')
    static_dest = output_dir / 'static'
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy static files
    if static_src.exists():
        import shutil
        if static_dest.exists():
            shutil.rmtree(static_dest)
        shutil.copytree(static_src, static_dest)
        print(f"✓ Copied static files")
    
    # Read base.html once
    base_path = templates_dir / 'base.html'
    base_content = None
    if base_path.exists():
        with open(base_path, 'r', encoding='utf-8') as f:
            base_content = f.read()
    
    # Convert templates
    template_mapping = {
        'welcome.html': 'index.html',  # Main entry point
        'landing.html': 'home.html',
        'upload.html': 'upload.html',
        'reminders.html': 'reminders.html',
        'symptomReport.html': 'symptom-tracker.html',
        'glucose.html': 'glucose.html',
        'settings.html': 'settings.html',
    }
    
    for template_name, output_name in template_mapping.items():
        template_path = templates_dir / template_name
        output_path = output_dir / output_name
        
        if template_path.exists():
            convert_template_to_static(template_path, output_path, base_content)
        else:
            print(f"⚠ Template not found: {template_name}")
    
    print("\n✅ Conversion complete!")
    print(f"📁 Static site generated in: {output_dir}")
    print("\nNext steps:")
    print("1. cd netlify-deploy")
    print("2. npm install")
    print("3. netlify deploy")


if __name__ == '__main__':
    main()
