#!/usr/bin/env python3
"""Inject GA4 tracking snippet into all relevant HTML files."""

import os
import glob

MEASUREMENT_ID = "G-3F21WXSMPB"

GA4_SNIPPET = f"""    <!-- Google Analytics GA4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{MEASUREMENT_ID}');
    </script>"""

# Files to skip (email templates, recorder tools, debug files)
SKIP_FILES = {
    'email-templates', 'free-tools-recorder.html', 'logo-recorder.html',
    'logo-studio.html', 'simulator-recorder.html', 'debug.html',
    'tooltip-preview.html', 'closing-recorder.html'
}

BASE_DIR = "/Users/davidkish/Desktop/AI Career Coach"

html_files = []
for pattern in ['*.html', 'strategy/*.html', 'guides/*.html']:
    html_files.extend(glob.glob(os.path.join(BASE_DIR, pattern)))

updated = []
skipped = []
already_has = []

for filepath in sorted(html_files):
    filename = os.path.basename(filepath)
    relpath = os.path.relpath(filepath, BASE_DIR)
    
    # Skip certain files
    if any(skip in relpath for skip in SKIP_FILES):
        skipped.append(relpath)
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has GA4
    if MEASUREMENT_ID in content or 'G-3F21WXSMPB' in content:
        already_has.append(relpath)
        continue
    
    # Also skip if googletagmanager is already there for THIS id
    if 'googletagmanager.com/gtag/js?id=G-3F21WXSMPB' in content:
        already_has.append(relpath)
        continue
    
    # Inject after <head> tag
    if '<head>' in content:
        new_content = content.replace('<head>', '<head>\n' + GA4_SNIPPET, 1)
    elif '<head ' in content:
        # head with attributes
        idx = content.find('<head ')
        end_idx = content.find('>', idx) + 1
        new_content = content[:end_idx] + '\n' + GA4_SNIPPET + content[end_idx:]
    else:
        skipped.append(f"{relpath} (no <head> tag)")
        continue
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    updated.append(relpath)

print(f"\n✅ GA4 ({MEASUREMENT_ID}) injected into {len(updated)} files:")
for f in updated:
    print(f"   + {f}")

if already_has:
    print(f"\n⏭️  Already had GA4 ({len(already_has)} files):")
    for f in already_has:
        print(f"   ~ {f}")

if skipped:
    print(f"\n⏭️  Skipped ({len(skipped)} files):")
    for f in skipped:
        print(f"   - {f}")

print(f"\nDone! Deploy to Vercel to activate tracking.")
