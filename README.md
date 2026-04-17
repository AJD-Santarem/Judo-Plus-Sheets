# 🥋 Judo+ Tournament System

A Python pipeline to automatically:

* Process athlete registrations
* Create balanced competition groups
* Distribute groups across mats
* Generate Excel fight sheets
* Export PDF mat schedules

---

# 📦 Requirements

## Python version

* Python **3.10+** (recommended 3.11+)

## Install dependencies

```bash
pip install pandas openpyxl pyyaml jinja2 pdfkit
```

## System dependency (IMPORTANT)

### wkhtmltopdf

Required for PDF generation.

### Ubuntu / WSL

```bash
sudo apt install wkhtmltopdf
```

### Windows

Download:
[https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)

Make sure `wkhtmltopdf` is in PATH.

---

# 📁 Project Structure (simplified)

```
Input/
Output/
Resources/
    Templates/
        Table/
        *.xlsx templates
config.py
judo+_draw.py
judo+_mat_distribution.py
judo+_sheets.py
```

---

# ⚙️ Setup (IMPORTANT)

## 1. Edit `config.py`

Before running anything:

### Required changes (example):

* **Tournament stage**

```python
STAGE = "B"   # "B" = Benjamins, "I" = Iniciados/Infantis
```

* **Tournament identifier**

```python
TOURNAMENT_CODE = "FZ_2026"
```

* **Location + date**

```python
LOC_DATE = "Coimbra, 2026-04-17"
```

* **Number of mats**

```python
NUMBER_OF_MATS = 5
```

---

# 🚀 How to Run

## Step 1 — Generate groups (DRAW)

```bash
python judo+_draw.py
```

### Output:

* grouped YAML files per gender
* validation logs
* draw report (`.md`)

### ⚠️ IMPORTANT:

Check YAML output carefully:

* no ungrouped athletes
* no invalid categories

---

## Step 2 — Distribute groups to mats

```bash
python judo+_mat_distribution.py
```

### Output:

* `mat_distribution.yaml`
* `mat_distribution.pdf`

### 🔎 What to verify:

* balanced mats
* no same weight class duplication on same mat (if possible)
* fights count is consistent

---

## Step 3 — Generate Excel sheets

```bash
python judo+_sheets.py
```

### Output:

* One Excel file per group
* Stored in:

```
Output/<TOURNAMENT_CODE>/Excel_Sheets/
```

Each sheet contains:

* fight layout
* athlete names
* club info
* weights
* mat assignment

---

## 🔁 Running for Stage 2

To run a second stage:

1. Update:

```python
STAGE = "I"
```

2. Repeat pipeline:

```bash
python judo+_draw.py
python judo+_mat_distribution.py
python judo+_sheets.py
```

Each stage generates separate output files automatically.

---

# 📊 Output Summary

| Step             | Output                           |
| ---------------- | -------------------------------- |
| Draw             | grouped YAML + validation report |
| Mat distribution | YAML + PDF schedule              |
| Sheets           | Excel fight sheets               |
