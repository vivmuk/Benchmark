from pathlib import Path
root = Path('/Users/vivgatesai/.openclaw/workspace/benchmarks/venice-benchmark-site')
report = []
for p in [
    root/'index.html',
    root/'arcade.html',
    root/'experimental-design.html',
    root/'assets/styles.css',
    root/'assets/app.js',
]:
    t = p.read_text(encoding='utf-8', errors='replace')
    report.append(f'{p.name}: bytes={p.stat().st_size} design={("experimental-design.html" in t)} full_protocol={("Full protocol" in t)} escape={("\\u0026amp;" in t)} canvas_entity={("<canvas>" in t)} light_bg={("--bg: #F7F5F1" in t)}')
Path('/Users/vivgatesai/.openclaw/workspace/benchmarks/venice-benchmark-site/tool_status_report.txt').write_text('\n'.join(report)+'\n')
print('wrote report')
