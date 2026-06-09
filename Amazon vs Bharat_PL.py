import re
import pandas as pd
import numpy as np
import json
from pathlib import Path

data_dir = Path(__file__).parent

trans_min, trans_max = 225, 320
pl_min, pl_max = 330, 800
stack_offset = 500

dark_df = pd.read_excel(data_dir / "dark.xlsx", header=None, skiprows=6)
dark_wl = dark_df[0].values
dark_int_raw = dark_df[1].values

trans_df = pd.read_excel(data_dir / "Transmission spectra.xlsx", header=None)
trans_wl = trans_df[0].values
trans_val = trans_df[1].values
t_mask = (trans_wl >= trans_min) & (trans_wl <= trans_max)

SKIP = {"dark", "transmission spectra"}

def parse_file(f):
    stem = f.stem
    # "Bharat 250 nm" or "Amazon 266.6 nm"
    m = re.match(r'^(Bharat|Amazon)\s+([\d.]+)(?:\s*nm)?$', stem, re.IGNORECASE)
    if m:
        return float(m.group(2)), m.group(1).capitalize()
    # "266.6 Bharat" (old style)
    m2 = re.match(r'^([\d.]+)\s*(Bharat|Amazon)$', stem, re.IGNORECASE)
    if m2:
        return float(m2.group(1)), m2.group(2).capitalize()
    # "260 nm" or "260"
    m3 = re.match(r'^([\d.]+)(?:\s*nm)?$', stem)
    if m3:
        return float(m3.group(1)), "Amazon"
    return None

entries = []
for f in data_dir.glob("*.xlsx"):
    if f.stem.lower() in SKIP:
        continue
    result = parse_file(f)
    if result is None:
        continue
    excitation, sample = result
    entries.append((excitation, sample, f))

sample_order = {"Amazon": 0, "Bharat": 1}
entries.sort(key=lambda x: (sample_order.get(x[1], 99), x[0]))

COLORS = [
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2",
    "#7f7f7f","#bcbd22","#17becf","#aec7e8","#ffbb78","#98df8a","#ff9896",
    "#c5b0d5","#c49c94","#f7b6d2","#c7c7c7","#dbdb8d","#9edae5",
    "#393b79","#637939","#8c6d31","#843c39","#7b4173",
    "#3182bd","#e6550d","#31a354","#756bb1","#636363",
    "#6baed6","#fd8d3c","#74c476","#9e9ac8","#969696",
    "#9ecae1","#fdae6b","#a1d99b","#bcbddc","#bdbdbd",
    "#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00",
]

pl_stacked = []
for i, (excitation, sample, f) in enumerate(entries):
    df = pd.read_excel(f, header=None, skiprows=6)
    wl = df[0].values
    dark_interp = np.interp(wl, dark_wl, dark_int_raw)
    intensity = np.clip(df[1].astype(float).values - dark_interp, 0, None)
    mask = (wl >= pl_min) & (wl <= pl_max)
    label = f"{excitation:.1f} nm \u2014 {sample}" if sample != "Base" else f"{excitation:.1f} nm"
    pl_stacked.append({
        "wl": wl[mask].tolist(),
        "intensity": (intensity[mask] + i * stack_offset).tolist(),
        "sample": sample,
        "label": label,
        "excitation": excitation,
        "color": COLORS[i % len(COLORS)],
    })

samples_list = []
seen = set()
for _, s, _ in entries:
    if s not in seen:
        seen.add(s)
        samples_list.append(s)

data_js = {
    "trans_wl": trans_wl[t_mask].tolist(),
    "trans_val": trans_val[t_mask].tolist(),
    "pl_stacked": pl_stacked,
    "trans_min": trans_min, "trans_max": trans_max,
    "pl_min": pl_min, "pl_max": pl_max,
    "samples": samples_list,
}

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Amazon vs Bharat PL</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; margin: 16px; background: #fff; }}
  h2 {{ color: #333; margin-bottom: 4px; }}
  #info {{ font-size: 12px; color: #888; margin-bottom: 8px; }}
  #filter-bar {{ margin-bottom: 10px; }}
  .filter-btn {{
    padding: 5px 18px; margin-right: 6px; border: 1.5px solid #555;
    border-radius: 4px; cursor: pointer; font-size: 13px;
    background: #eee; color: #333;
  }}
  .filter-btn.active {{ background: #333; color: #fff; }}
</style>
</head>
<body>
<h2>Amazon vs Bharat — PL Dark Subtracted</h2>
<div id="info">Drag the red line on transmission to select excitation &nbsp;|&nbsp; Drag black line on PL to mark emission</div>
<div id="filter-bar">
  <button class="filter-btn active" data-filter="All" onclick="setFilter('All')">All</button>
</div>
<div id="trans_plot" style="height:260px; cursor:crosshair;"></div>
<div id="pl_plot" style="height:520px;"></div>

<script>
const D = {json.dumps(data_js)};
let currentFilter = 'All';

// Build sample filter buttons
const filterBar = document.getElementById('filter-bar');
D.samples.forEach(s => {{
  const btn = document.createElement('button');
  btn.className = 'filter-btn';
  btn.dataset.filter = s;
  btn.textContent = s;
  btn.onclick = () => setFilter(s);
  filterBar.appendChild(btn);
}});

function setFilter(f) {{
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.filter === f);
  }});
  refreshOpacity(new Set());
}}

function refreshOpacity(hiSet) {{
  const opacities = [], widths = [];
  D.pl_stacked.forEach((d, i) => {{
    const vis = currentFilter === 'All' || d.sample === currentFilter;
    const hi = hiSet.has(i);
    opacities.push(hi ? 1.0 : vis ? 0.35 : 0.04);
    widths.push(hi ? 2.5 : 0.8);
  }});
  Plotly.restyle('pl_plot', {{opacity: opacities, 'line.width': widths}});
}}

function getVisibleEntries() {{
  return D.pl_stacked
    .map((d, i) => ({{i, ex: d.excitation, sample: d.sample}}))
    .filter(x => currentFilter === 'All' || x.sample === currentFilter);
}}

// Returns one index per sample that actually has data near wl (within 2 nm of the best match)
function getNearestIndices(wl) {{
  const vis = getVisibleEntries();
  if (!vis.length) return [0];
  // Find the globally nearest excitation
  const best = vis.reduce((b, x) => Math.abs(x.ex - wl) < Math.abs(b.ex - wl) ? x : b);
  const tol = 2.0;
  // Only include a sample if it has data within tol of that best excitation
  const byGroup = {{}};
  vis.forEach(x => {{
    if (Math.abs(x.ex - best.ex) <= tol) {{
      if (!byGroup[x.sample] || Math.abs(x.ex - best.ex) < Math.abs(byGroup[x.sample].ex - best.ex))
        byGroup[x.sample] = x;
    }}
  }});
  return Object.values(byGroup).map(x => x.i);
}}

function getNearestIdx(wl) {{
  const vis = getVisibleEntries();
  if (!vis.length) return 0;
  return vis.reduce((best, x) =>
    Math.abs(x.ex - wl) < Math.abs(best.ex - wl) ? x : best
  ).i;
}}

function clientToDataX(div, clientX) {{
  const bb = div.getBoundingClientRect();
  const layout = div._fullLayout;
  const m = layout.margin;
  const plotW = layout.width - m.l - m.r;
  const frac = (clientX - bb.left - m.l) / plotW;
  const range = layout.xaxis.range;
  return range[0] + frac * (range[1] - range[0]);
}}

// ── Transmission plot ───────────────────────────────────────────
const initEx = D.pl_stacked[0].excitation;
Plotly.newPlot('trans_plot', [{{
  x: D.trans_wl, y: D.trans_val,
  mode: 'lines', line: {{color:'black', width:1.5}},
  showlegend: false,
  hovertemplate: '%{{x:.1f}} nm  T=%{{y:.1f}}<extra></extra>'
}}], {{
  xaxis: {{title:'Wavelength (nm)', range:[D.trans_min, D.trans_max]}},
  yaxis: {{title:'Transmission'}},
  margin: {{t:30, b:50, l:60, r:20}},
  title: {{text:'Transmission', font:{{size:13}}}},
  dragmode: false,
  shapes: [{{type:'line', x0:initEx, x1:initEx,
             yref:'paper', y0:0, y1:1,
             line:{{color:'red', width:2.5, dash:'dash'}}}}],
  annotations: [{{x:initEx, yref:'paper', y:1.04,
                  text:initEx.toFixed(1)+' nm',
                  showarrow:false, font:{{color:'red',size:12}}, xanchor:'left'}}]
}}, {{responsive:true, displayModeBar:false}});

// ── PL plot ─────────────────────────────────────────────────────
const initPlLine = (D.pl_min + D.pl_max) / 2;
const initLaser  = initEx * 3;
const initSH     = initEx * 1.5;

function plShapes(emLine, laser, sh) {{
  return [
    {{type:'line', x0:emLine, x1:emLine, yref:'paper', y0:0, y1:1,
      line:{{color:'black', width:2}}}},
    {{type:'line', x0:laser,  x1:laser,  yref:'paper', y0:0, y1:1,
      line:{{color:'red', width:1.5, dash:'dot'}}}},
    {{type:'line', x0:sh,     x1:sh,     yref:'paper', y0:0, y1:1,
      line:{{color:'orange', width:1.5, dash:'dot'}}}}
  ];
}}

function plAnnotations(emLine, laser, sh) {{
  return [
    {{x:emLine, yref:'paper', y:1.02, text:emLine.toFixed(1)+' nm',
      showarrow:false, font:{{color:'black',size:11}}, xanchor:'left'}},
    {{x:laser,  yref:'paper', y:0.97, text:'Laser '+laser.toFixed(0)+' nm',
      showarrow:false, font:{{color:'red',size:10}}, xanchor:'left'}},
    {{x:sh,     yref:'paper', y:0.90, text:'SH '+sh.toFixed(0)+' nm',
      showarrow:false, font:{{color:'orange',size:10}}, xanchor:'left'}}
  ];
}}

Plotly.newPlot('pl_plot',
  D.pl_stacked.map((d, i) => ({{
    x: d.wl, y: d.intensity, mode:'lines',
    line: {{color: d.color, width: 0.8}},
    opacity: 0.35,
    showlegend: false,
    hoverinfo: 'none', hovertemplate: null
  }})),
  {{
    xaxis: {{title:'Wavelength (nm)', range:[D.pl_min, D.pl_max]}},
    yaxis: {{title:'Intensity (counts)'}},
    margin: {{t:50, b:50, l:70, r:20}},
    title: {{text:'Excitation = '+initEx.toFixed(1)+' nm  |  Laser: '+initLaser.toFixed(0)+' nm', font:{{size:13}}}},
    showlegend: false, hovermode: false, dragmode: 'zoom',
    shapes: plShapes(initPlLine, initLaser, initSH),
    annotations: plAnnotations(initPlLine, initLaser, initSH)
  }},
  {{responsive:true, displayModeBar:true}}
);

// ── Drag logic ──────────────────────────────────────────────────
const transDiv = document.getElementById('trans_plot');
const plDiv    = document.getElementById('pl_plot');
let dragTrans = false, dragPL = false;

function updateTrans(wl) {{
  wl = Math.max(D.trans_min, Math.min(D.trans_max, wl));
  const indices = getNearestIndices(wl);
  const idx = getNearestIdx(wl);
  const ex = D.pl_stacked[idx].excitation;
  Plotly.relayout('trans_plot', {{
    'shapes[0].x0': wl, 'shapes[0].x1': wl,
    'annotations[0].x': wl,
    'annotations[0].text': wl.toFixed(1)+' nm'
  }});
  refreshOpacity(new Set(indices));
  const laser = ex * 3;
  const sh    = laser / 2;
  const emLine = plDiv._fullLayout.shapes[0].x0;
  const labels = indices.map(i => D.pl_stacked[i].sample).join(' & ');
  Plotly.relayout('pl_plot', {{
    'title.text': 'Excitation = '+ex.toFixed(1)+' nm  |  Laser: '+laser.toFixed(0)+' nm  |  '+labels,
    shapes: plShapes(emLine, laser, sh),
    annotations: plAnnotations(emLine, laser, sh)
  }});
}}

function updatePLline(wl) {{
  wl = Math.max(D.pl_min, Math.min(D.pl_max, wl));
  const laser = transDiv._fullLayout.shapes[0].x0 * 3;
  const sh    = laser / 2;
  Plotly.relayout('pl_plot', {{
    shapes: plShapes(wl, laser, sh),
    annotations: plAnnotations(wl, laser, sh)
  }});
}}

transDiv.addEventListener('mousedown', e => {{
  const wl = clientToDataX(transDiv, e.clientX);
  if (Math.abs(wl - transDiv._fullLayout.shapes[0].x0) < (D.trans_max-D.trans_min)*0.02) {{
    dragTrans = true; e.preventDefault();
  }}
}});

plDiv.addEventListener('mousedown', e => {{
  const wl = clientToDataX(plDiv, e.clientX);
  if (Math.abs(wl - plDiv._fullLayout.shapes[0].x0) < (D.pl_max-D.pl_min)*0.02) {{
    dragPL = true; e.preventDefault(); e.stopPropagation();
  }}
}}, true);

document.addEventListener('mousemove', e => {{
  if (dragTrans) updateTrans(clientToDataX(transDiv, e.clientX));
  if (dragPL)    updatePLline(clientToDataX(plDiv, e.clientX));
}});
document.addEventListener('mouseup', () => {{ dragTrans = false; dragPL = false; }});

transDiv.addEventListener('mousemove', e => {{
  const wl = clientToDataX(transDiv, e.clientX);
  transDiv.style.cursor = Math.abs(wl - transDiv._fullLayout.shapes[0].x0) < (D.trans_max-D.trans_min)*0.02 ? 'ew-resize' : 'default';
}});
plDiv.addEventListener('mousemove', e => {{
  const wl = clientToDataX(plDiv, e.clientX);
  plDiv.style.cursor = Math.abs(wl - plDiv._fullLayout.shapes[0].x0) < (D.pl_max-D.pl_min)*0.02 ? 'ew-resize' : 'default';
}});
</script>
</body>
</html>"""

output = data_dir / "Amazon vs Bharat_PL.html"
output.write_text(html)
print(f"Saved: {output} ({len(pl_stacked)} traces)")
for s in samples_list:
    n = sum(1 for e in entries if e[1] == s)
    print(f"  {s}: {n} files")
