# GdScO₃:Eu³⁺ Photoluminescence Analysis

Interactive and scripted analysis of excitation-dependent photoluminescence (PL) 
in Eu³⁺-doped GdScO₃ single crystals, comparing two crystal samples 
(Crystal A — Amazon, Crystal B — Bharat).

## Contents

| File | Description |
|---|---|
| `Amazon_vs_Bharat_PL.html` | Interactive Plotly visualization — open in any browser |
| `pl_analysis.py` | Python script for stacked PL plots with draggable excitation/emission lines |

## Live Interactive Plot

👉 [Open Interactive PL Viewer](file:///Users/shadi/Library/CloudStorage/Box-Box/Berardi/GSO/PL/3-6-26/PL_Amazon%20and%20266.6%20Bharat.html)

No installation needed — runs directly in your browser.

## Science

GdScO₃:Eu³⁺ exhibits two mechanistically independent excitation pathways:

- **Host-band excitation (233–253 nm)** → dominant ⁵D₂ emission at ~491 nm
- **Gd³⁺-mediated excitation (264–270 nm)** → ⁵D₀ emission at ~612 nm

Crystal A (Amazon) and Crystal B (Bharat) are compared across the full 
excitation-emission landscape to probe site symmetry, energy transfer 
efficiency, and defect contributions.

## Python Script

### Requirements

```bash
pip install pandas matplotlib numpy openpyxl
```

### Usage

Place `pl_analysis.py` in the same folder as your `.xlsx` data files 
(dark spectrum, transmission spectrum, and individual PL files named by 
excitation wavelength, e.g. `254 nm.xlsx`), then run:

```bash
python pl_analysis.py
```

Drag the red dashed line on the transmission panel to select an excitation 
wavelength — the corresponding PL spectrum highlights automatically.
Line positions are saved between sessions.

## Author

Shadi Mirmohammadi  
PhD Candidate, Electrical & Computer Engineering, University of Utah  
Sensale-Rodriguez Lab
