# Training Data Preparation Plan (L04)

SDS320 Spatial Data Analytics · David Leu · Project: Sentinel-2 vegetation stress and drought-induced forest dieback, Jura/Valais

Items marked *(verify)* are assumptions that still need to be confirmed.

## 0. Task framing

- **What the model learns:** the severity of drought-induced forest dieback per Sentinel-2 pixel (Jura/Valais, post-2018).
- **One training example:** a multi-band Sentinel-2 chip, with a pre-drought composite (summer 2017) and a post-drought composite, paired with a severity label chip.
- **Label format:** raster mask with ordinal classes (0 = no forest/ignore, 1 = healthy, 2 = stressed, 3 = dieback). If only continuous reference data is available (e.g. % canopy loss), switch to a target raster for regression (L11).

## 1. Imagery and annotation sources

- **Imagery:** Sentinel-2 L2A (10 m bands, cloud-masked summer median composites per year), as planned in L02.
- **Labels (the weak point):** Sentinel-2 indices are the predictors, so they cannot also serve as labels. Candidates *(verify availability and licence)*:
  - Swiss forest-protection or disturbance records (WSL/FOEN)
  - cantonal dieback or damage surveys (Jura, Valais)
  - NFI plots
  - the STDL HETRES reference data (https://tech.stdl.ch/PROJ-HETRES/)
  - fallback: manual digitising on swissIMAGE for a small area
- **Alignment check:** the label date must fall after the drought and match the imagery year. Overlay labels on a true-colour chip for at least one area before tiling.

## 2. Tile size, stride, overlap

- **64 × 64 px (640 × 640 m), stride 64, no overlap** for the first prototype.
- **Why:** dieback patches are small at 10 m, and 640 m gives enough stand context without creating thousands of files. If patches are often cut by tile edges, move to 50% overlap (stride 32) for **train only**. Never use overlap in val/test, since it double-counts pixels.
- **Prototype area:** one \~10 × 10 km forested block in Jura, giving about 150–250 chips.

## 3. Batch pairing

- **Naming:** `{region}_{year}_{row}_{col}`, shared by `img/` and `mask/` chips, so pairing is a pure filename match.
- **Why it fits:** imagery comes as one composite per region and year, so batch-loop over regions and match masks by the same ID. A check that every image chip has exactly one mask catches silent mismatches.
- **CRS:** keep everything on the Sentinel-2 grid (UTM 32N) and rasterise the labels onto that grid.

## 4. Split strategy

- **Spatial block split:** 5 × 5 km blocks assigned to train/val/test at **70 / 15 / 15**, with a one-chip (640 m) buffer between blocks.
- **Stress test later:** hold out a whole sub-region (e.g. a Valais valley) as an extra test set to check generalisation across climate and species mix.
- **Why:** random chip splits would put neighbouring, near-identical chips in train and test, giving suspiciously good validation scores.

## 5. First tile batch

Generate a few dozen chips into `data/tiles/{train,val,test}/{img,mask}/`, then visually check 5–10 pairs for edge artefacts, clouds or snow, and label shifts.

## Reflection

- **Biggest quality risk:** incompleteness. Reference data likely covers only part of the damaged stands, so unlabelled dieback becomes false "healthy". Check by overlaying labels with a post-drought NDVI/NDMI drop.
- **Class balance:** dieback is probably rare, so count pixels per class per split early.
- **Leakage confidence:** block buffering helps; a hold-out region would raise confidence further.
- **Fallback if the dataset is too small:** add a second area or year, use overlap in train, or narrow to one species (e.g. beech).
- **Parameters to document:** chip size, stride, overlap, block size, buffer, split ratio, CRS, composite dates, cloud mask, class mapping, label source and date.
