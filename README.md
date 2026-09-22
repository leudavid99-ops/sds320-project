# Forest Health Monitoring: Drought-Induced Dieback Detection

---
## Short summary

This project investigates drought-induced forest dieback using satellite-based Earth observation data. Building on the increasing frequency of summer droughts in Switzerland, the project aims to develop a method for detecting and mapping areas of forest stress or dieback, producing an output usable for decision-making in forest management and conservation planning.

*(TO-DO: refine once the study area and exact framing are finalized — see Wulf's feedback to narrow to one problem, one study area, one target variable.)*

---
## Research question

*TO-DO — final research question not yet defined. Draft direction:*

> How well can Sentinel-2-derived vegetation-stress indices identify and map drought-induced dieback severity in the canton of Jura/Valais since 2018 severe summer-drought, compared to existing documented dieback patterns?

---
## Data sources

| Dataset | Provider | Access | Format | Notes |
|---|---|---|---|---|
| Sentinel-2 L2A | Copernicus / ESA | Copernicus Data Space Ecosystem | GeoTIFF / SAFE | Candidate primary imagery source |
| MODIS (e.g. NDVI/EVI products) | NASA | NASA Earthdata | HDF/GeoTIFF | Candidate for temporal/change context |
| *(Reference/label data — TBD)* | | | | e.g. forest inventory, dieback ground-truth, or a proxy such as NDVI anomaly |

*TO-DO: confirm final data sources, access routes, date ranges, and licences once the study area and target variable are fixed. See the reference project [STDL PROJ-HETRES](https://tech.stdl.ch/PROJ-HETRES/) for comparable data choices.*

---
## Methods

*TO-DO — to be detailed once finalized. Planned outline:*

1. Data acquisition and preprocessing (cloud masking, mosaicking, clipping to study area)
2. Derivation of vegetation/stress indices (e.g. NDVI, NDMI) and/or use of pretrained foundation model embeddings
3. Change detection / anomaly analysis relative to a pre-drought baseline
4. Classification or regression to map dieback extent/severity
5. Validation against reference data
6. Production of a final decision-support map

---
## Repository structure

```
my-sds320-project/
├── README.md              <- Project overview (this file)
├── environment.yml         <- Conda environment specification
├── .gitignore
├── data/
│   ├── README.md           <- Description of data sources and structure
│   ├── raw/                <- Original, unprocessed data (not tracked in git)
│   ├── processed/          <- Cleaned/derived data used for analysis
│   └── training/           <- Data used for model training/validation
├── notebooks/
│   ├── 01_explore_data.ipynb        <- Initial data exploration
│   ├── 02_preprocess_data.ipynb     <- Preprocessing and feature derivation
│   └── 03_results_and_figures.ipynb <- Analysis, results, figure generation
├── scripts/
│   ├── preprocessing.py    <- Reusable preprocessing functions
│   └── plotting.py         <- Reusable plotting functions
├── results/
│   ├── figures/             <- Plots and charts
│   ├── maps/                 <- Output maps
│   ├── predictions/          <- Model output/predictions
│   └── evaluation/           <- Accuracy/validation metrics
└── report/                <- Final written report
```

---
## How to run

1. Clone the repository:
   ```bash
   git clone https://github.com/leudavid99-ops/sds320-project.git
   cd sds320-project
   ```
2. Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate sds320-project
   ```
3. Run the notebooks in order:
   - `notebooks/01_explore_data.ipynb`
   - `notebooks/02_preprocess_data.ipynb`
   - `notebooks/03_results_and_figures.ipynb`

*TO-DO: update once the environment file and data access steps (e.g. API keys/credentials) are finalized.*

---
## Results

*TO-DO — to be filled in as results become available. Link key figures/maps here, e.g.:*

- `results/maps/dieback_map_final.png`
- `results/evaluation/accuracy_metrics.csv`

---
## Limitations

*TO-DO — to be expanded, e.g.:*

- Study area and time period not yet finalized
- Availability and quality of reference/ground-truth data for validation is uncertain
- Cloud cover may limit usable Sentinel-2 scenes in the study period
- Spatial/temporal resolution trade-offs between Sentinel-2 and MODIS

---
## AI use

*TO-DO — document specific AI tool use as the project progresses, e.g. code assistance, drafting text, or debugging. State which tools and for which parts.*

---
## Licence and citation

*TO-DO — confirm licence for code/data/figures (e.g. MIT for code, check data provider licences for Sentinel-2/MODIS) and add citation format if required by the course.*
