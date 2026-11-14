# Mapping drought-associated beech dieback in Ajoie with a two-stage GeoAI workflow

**Project:** SDS320 -- Spatial Data Science / GeoAI\
**Study area:** Ajoie, Canton of Jura, Switzerland\
**Status:** Proposed research workflow / implementation in progress

## Research question

> To what extent can a two-stage deep-learning approach, combining
> individual beech crown detection and ordinal health classification on
> high-resolution RGB-NIR aerial imagery, map the severity of
> drought-associated beech dieback in Ajoie (Canton Jura), and how can
> historical satellite-derived vegetation indicators contextualise its
> development since 2018?

The project aims to create a reproducible, georeferenced workflow that
detects individual beech crowns, assigns an ordered health-severity
class to each crown, and relates the 2022 condition snapshot to
historical vegetation dynamics following the 2018 drought.

**Important scope distinction:** a single high-resolution image acquired
in 2022 can support a detailed 2022 tree-health map. It cannot, by
itself, reconstruct annual individual-tree health states from 2018
onward. Historical Sentinel-2 indicators will therefore be used as
contextual, stand-/pixel-scale evidence unless multi-date
high-resolution imagery and temporally matched tree-level labels become
available.

## Project objectives

1.  Detect and delineate individual tree crowns in high-resolution
    aerial imagery.
2.  Identify beech crowns, using forest inventory information and/or a
    species-filtering step where necessary.
3.  Classify each beech crown into an ordinal health category: healthy,
    unhealthy, or dead.
4.  Test whether NIR information improves health classification compared
    with RGB-only imagery.
5.  Validate detection and health classification against independent
    forester-assessed ground truth.
6.  Contextualise the mapped 2022 health condition using
    satellite-derived vegetation anomalies from 2018 onward.
7.  Produce georeferenced tree-level outputs and aggregated severity
    maps for forest stands.

## Study context and existing research

The project builds on previous work in Ajoie by the Swiss Territorial
Data Lab (STDL), commissioned by the Canton of Jura. The PROJ-HETRES
work explored beech health assessment using high-resolution RGB-NIR
aerial imagery, LiDAR, satellite-derived vegetation indicators and
forester assessments. The published project description reports a study
area around Miécourt and Beurnevésin, 3 cm RGB-NIR imagery acquired in
August 2022, and three health categories (healthy, unhealthy, dead).

The proposed contribution is not to claim that beech dieback mapping is
entirely new. It is to investigate a reproducible two-stage
deep-learning alternative and evaluate its performance, data
requirements and transferability against an existing local reference
context.

## Conceptual methodology

``` text
High-resolution aerial imagery (RGB + NIR)
                  |
          Preprocessing / tiling
                  |
     Stage 1: individual crown detection
       Detectree2 / Mask R-CNN / alternative
                  |
        Crown masks / polygons
                  |
       Beech identification/filtering
                  |
        Individual crown image chips
                  |
    Stage 2: ordinal health classification
       CNN backbone + ordinal head (CORAL)
                  |
     Healthy / Unhealthy / Dead + confidence
                  |
     Geospatial join and quality control
                  |
    Tree-level severity map and summaries

Historical context (parallel analysis):
Sentinel-2 2018–present -> NDVI / NDMI anomalies
                  |
       contextual temporal analysis
                  |
     association with 2022 tree health
```

### Stage 1 -- individual crown detection and delineation

**Purpose:** locate individual crowns and create one spatial geometry
per detected tree.

Candidate methods: - **Detectree2 / Mask R-CNN:** an
instance-segmentation framework developed for individual tree crown
delineation. - **Arborizer:** an additional candidate because it has
been explored in the STDL Ajoie-related workflow. - **YOLO instance
segmentation:** an optional speed-oriented comparison if time and
annotation capacity permit.

Recommended initial strategy: 1. Start with one established
instance-segmentation baseline rather than implementing several models
simultaneously. 2. Test the pretrained model on representative Ajoie
image tiles. 3. Fine-tune using local crown annotations if permitted
data and annotation capacity are available. 4. Export crown masks and
georeferenced polygons. 5. Restrict to beech-dominated forest stands
using authoritative species/stand information, if available. If mixed
stands are included, add a species-identification step or explicitly
quantify species uncertainty.

**RGB-NIR adaptation:** many pretrained crown detectors expect
three-channel RGB input. A four-band model requires an explicit
input-layer adaptation, appropriate weight initialisation and
retraining/fine-tuning. Do not assume a pretrained RGB model can accept
RGB-NIR imagery unchanged.

### Stage 2 -- ordinal health classification

**Purpose:** assign an ordered health-severity class to each detected
beech crown.

Proposed label scheme (subject to matching the forester protocol): -
`0 – Healthy` - `1 – Unhealthy` - `2 – Dead`

Candidate model: - Pretrained CNN feature extractor (e.g. ResNet-50 or
EfficientNet). - Ordinal classification head, with CORAL as a candidate
method. - Masked crown chips to reduce background influence. - Compare
RGB-only against RGB-NIR, and optionally RGB-NIR plus derived vegetation
indices.

CORAL models the ordered thresholds rather than treating the classes as
unrelated categories. For three classes, it learns whether a sample is
at least unhealthy and whether it is dead. The predicted class and
confidence should both be retained.

**Ground-truth limitation:** the existing Ajoie project description
reports 226 forester-assessed beech trees across three health classes.
The availability of coordinates, photographs, crown polygons, image
dates and permission for academic reuse must be confirmed. Point labels
alone do not provide crown segmentation masks for Stage 1.

### Historical context since 2018

Use Sentinel-2 as a complementary time series, not as a substitute for
high-resolution individual-tree imagery: - NDVI: greenness /
photosynthetic activity proxy. - NDMI: vegetation moisture-related
spectral indicator. - Seasonal composites and annual anomalies relative
to a suitable baseline. - Cloud, shadow, snow and phenology filtering.

For each reference tree or stand, extract contextual time-series
summaries using carefully defined buffers or forest-stand polygons.
Sentinel-2 pixels are 10 m for red and NIR and may contain multiple
crowns; therefore, they cannot reliably attribute historical signals to
individual trees in dense forest.

Avoid causal language unless confounding factors (pathogens, pests, site
conditions, competition and management) can be addressed. Prefer
"drought-associated" or "following the 2018 drought" over
"drought-induced" when causal attribution is not established.

## Data requirements and status

  -----------------------------------------------------------------------
  Dataset                 Intended use            Status / action
  ----------------------- ----------------------- -----------------------
  2022 RGB-NIR aerial     Stage 1 and Stage 2     Request access and
  imagery (reported 3 cm) input                   usage permission

  Forester-assessed tree  Health labels /         Confirm coordinates,
  records                 validation              labels, dates and
                                                  access

  Crown polygons or tree  Detection labels /      Availability not yet
  photographs             audit                   confirmed

  LiDAR / CHM             Optional structural     Request availability;
                          feature or comparison   not essential to
                                                  baseline

  Forest stand / species  Beech filtering and     Identify authoritative
  inventory               stratification          Canton Jura source

  Sentinel-2 time series, Historical vegetation   Public Copernicus
  2018 onward             context                 source; processing
                                                  required

  Historical aerial       Possible annual /       Availability and
  imagery                 multi-date analysis     comparability to be
                                                  assessed
  -----------------------------------------------------------------------

Do not commit restricted or large source datasets to Git. Store data
locally or in approved institutional storage, and document source,
licence, acquisition date, CRS, processing and access restrictions.

## Experimental design

### Baselines and ablation experiments

  -----------------------------------------------------------------------
  Experiment              Input                   Purpose
  ----------------------- ----------------------- -----------------------
  Detection baseline      RGB                     Establish
                                                  crown-detection
                                                  performance

  Detection adaptation    RGB-NIR (if supported)  Test whether NIR helps
                                                  crown delineation

  Health model A          RGB crown chips         Baseline health
                                                  classification

  Health model B          RGB-NIR crown chips     Measure contribution of
                                                  NIR

  Health model C          RGB-NIR + NDVI / NDMI   Test derived-index
  (optional)                                      contribution

  Ordinal vs nominal head Same image input        Test value of
                                                  respecting ordered
                                                  labels
  -----------------------------------------------------------------------

Use a simple Random Forest or conventional CNN classifier as a reference
baseline if the existing STDL data and code can be accessed.

### Data splitting and leakage prevention

-   Split by spatially separated forest stands or spatial blocks, not by
    random neighbouring tree chips.
-   Keep an independent test set untouched until final evaluation.
-   Where possible, stratify splits by health class and stand
    conditions.
-   If multiple images or observations exist for the same tree, keep all
    observations from that tree in the same split.
-   Report uncertainty and class support, not only a single headline
    score.

### Evaluation metrics

**Stage 1 -- detection / segmentation** - Precision, recall and F1 for
matched tree detections. - Average Precision at specified IoU
thresholds. - Mask IoU / Dice score for crown boundaries. - Matching
rule and minimum IoU threshold documented explicitly.

**Stage 2 -- ordinal health classification** - Macro-F1 and balanced
accuracy. - Confusion matrix. - Weighted Cohen's kappa. - Mean absolute
error on encoded ordinal labels (0, 1, 2). - Per-class precision, recall
and support. - Calibration / confidence assessment where feasible.

**End-to-end** - Health-class performance for crowns successfully
detected by Stage 1. - Detection failure rate and its effect on mapped
class totals. - Spatial distribution of errors. - Aggregated severity
proportions by forest stand, with uncertainty.

## Proposed repository structure

The following is a suggested target structure; adapt it to the
repository's existing files rather than deleting current coursework or
project material.

``` text
sds320-project/
├── README.md
├── data/
│   ├── raw/                 # Original immutable inputs (not committed)
│   ├── interim/             # Tiled / aligned / intermediate data
│   ├── processed/           # Prepared model inputs and labels
│   └── metadata/            # Data inventory, licences, CRS, provenance
├── notebooks/
│   ├── 01_data_inventory_eda.ipynb
│   ├── 02_aerial_preprocessing.ipynb
│   ├── 03_crown_detection.ipynb
│   ├── 04_health_classification.ipynb
│   ├── 05_sentinel2_temporal_context.ipynb
│   └── 06_validation_and_mapping.ipynb
├── src/
│   ├── preprocessing/
│   ├── detection/
│   ├── classification/
│   ├── temporal/
│   ├── geospatial/
│   └── evaluation/
├── models/                  # Configs / checkpoints (large files excluded)
├── results/
│   ├── figures/
│   ├── tables/
│   ├── predictions/
│   └── maps/
├── docs/
│   ├── data_dictionary.md
│   └── methodology.md
└── requirements.txt
```

## Suggested software stack

-   Python, PyTorch, torchvision
-   Detectree2 (if selected for Stage 1)
-   Rasterio / rioxarray / GDAL for raster operations
-   GeoPandas / Shapely for vector processing
-   TorchGeo for geospatial deep-learning utilities where useful
-   Albumentations for image augmentation
-   scikit-learn for baselines and evaluation
-   xarray for temporal raster analysis
-   Jupyter for exploratory work

Exact package versions and pretrained-weight provenance should be
recorded once implementation begins.

## Key risks and mitigation

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  RGB-NIR imagery or labels           Confirm access before model
  inaccessible                        development; prepare a fallback
                                      data plan

  Too few labelled crowns             Transfer learning, conservative
                                      augmentation, additional annotation
                                      and simpler ordinal head

  Point labels without crown polygons Manually delineate a representative
                                      subset or obtain existing crown
                                      masks

  Mixed tree species                  Restrict to mapped beech stands or
                                      add a species filter and report
                                      uncertainty

  Crown overlap / understory trees    Define target population (visible
                                      overstory crowns) and document
                                      missed understory trees

  Spatial leakage                     Hold out entire stands / spatial
                                      blocks

  Historical attribution overclaimed  Treat Sentinel-2 as contextual
                                      evidence, not annual
                                      individual-tree ground truth

  Data alignment errors               Verify CRS, orthorectification,
                                      acquisition dates and RGB-NIR
                                      co-registration
  -----------------------------------------------------------------------

## Immediate next steps

1.  Contact STDL and the Canton of Jura to request the 2022 RGB-NIR
    imagery and forester-assessed reference records.
2.  Confirm whether the 226 tree observations include coordinates,
    photographs, crown polygons and a documented health protocol.
3.  Obtain a small representative image subset and run a feasibility
    test with one pretrained crown detector.
4.  Establish a spatially independent validation design before
    annotation and model training.
5.  Implement the Stage 1 baseline, then add Stage 2 only after the
    crown/label linkage is verified.

## Selected references and resources

-   STDL -- PROJ-HETRES, Ajoie beech dieback project:
    https://tech.stdl.ch/PROJ-HETRES/
-   swisstopo -- CLASSIFY health status of beech trees:
    https://www.swisstopo.admin.ch/en/classify-health-status-of-beech-trees
-   WSL -- Drought & beech, medium-term effects of the 2018 summer
    drought:
    https://www.wsl.ch/en/projects/drought-beech-medium-term-effects-of-the-2018-summer-drought-on-beech-north-of-the-alps/
-   Detectree2: https://github.com/PatBall1/detectree2
-   OAM Tree Crown Delineation dataset:
    https://github.com/open-forest-observatory
-   CORAL ordinal regression: https://arxiv.org/abs/1901.07884
-   TorchGeo: https://torchgeo.readthedocs.io/

------------------------------------------------------------------------

**Project status note:** This README describes the proposed research
design. It does not imply that the imagery, ground-truth records, crown
annotations or model outputs have already been acquired or generated.
Update the status, data provenance, model versions and results as the
project progresses.
