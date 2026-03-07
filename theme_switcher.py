import re

with open("v2/resume-analyzer.html", "r") as f:
    html = f.read()

# Dark to Light mappings
replacements = [
    ("bg-slate-950", "bg-slate-50"),
    ("bg-slate-900", "bg-white"),
    ("border-slate-800", "border-slate-200"),
    ("border-slate-700", "border-slate-300"),
    ("text-white", "text-slate-900"),
    ("text-slate-400", "text-slate-600"),
    ("text-slate-500", "text-slate-500"),
    ("text-slate-300", "text-slate-700"),
    ("text-slate-200", "text-slate-800"),
    ("text-[10px] font-bold text-blue-500 uppercase", "text-[10px] font-bold text-blue-600 uppercase"),
    ("text-blue-400", "text-blue-600"),
    ("bg-blue-900", "bg-blue-100"),
    ("border-white/5", "border-slate-200"),
    ("rgba(15, 23, 42, 0.6)", "rgba(255, 255, 255, 0.8)"),
    ("rgba(255, 255, 255, 0.05)", "rgba(0, 0, 0, 0.05)"),
    ("shadow-\\[0_0_10px_rgba\\(59\\,130\\,246\\,0\\.2\\)\\]", "shadow-sm"),
    ("shadow-\\[10px_0_30px_-5px_rgba\\(0\\,0\\,0\\,0\\.5\\)\\]", "shadow-xl"),
    ("text-blue-500", "text-blue-600"),
    ("bg-slate-800", "bg-slate-100"),
    ("bg-blue-500/5", "bg-blue-50"),
    ("border-blue-500/20", "border-blue-200"),
    ("bg-slate-900/20", "bg-slate-50"),
    ("border-blue-500/30", "border-blue-300"),
    ("hover:border-blue-500/60", "hover:border-blue-400"),
    ("bg-slate-800/50", "bg-slate-100"),
    ("bg-green-500/10", "bg-green-50"),
    ("from-slate-950", "from-slate-50"),
    ("via-slate-950", "via-slate-50"),
    ("to-blue-900/10", "to-blue-50"),
    ("from-slate-900/80", "from-white"),
    ("from-slate-800", "from-white"),
    ("to-slate-900", "to-slate-50"),
    ("from-blue-900/20", "from-blue-50"),
    ("border-slate-700/50", "border-slate-200"),
]

for old, new in replacements:
    html = html.replace(old, new)

# Change Text
html = html.replace("STRATEGY LAB", "")
html = html.replace("RESUME_AUDIT", "Resume Scanner")
html = html.replace("SOURCE DOCUMENT", "Upload Resume")
html = html.replace("TARGET CALIBRATION", "Add Job Description")
html = html.replace("Paste JD here for gap analysis...", "Paste the job you want to apply for (Optional)...")
html = html.replace("System Ready", "Ready to Scan")
html = html.replace("Awaiting source documents to initialize AI analysis logic.", "Upload your resume or paste the text to get a free, instant review.")
html = html.replace("RUN DIAGNOSTIC", "SCAN MY RESUME")
html = html.replace("DIAGNOSTIC RUNNING...", "SCANNING...")
html = html.replace("RETRY DIAGNOSTIC", "RETRY SCAN")

with open("v2/resume-analyzer.html", "w") as f:
    f.write(html)

print("Theme switched!")
