# Training Data Preparation Plan (L04)

SDS320 Spatial Data Analytics · David Leu · 27 October 2026

**Research question:** To what extent can a two-stage deep-learning approach, combining beech crown detection and ordinal health classification on high-resolution RGB+NIR aerial imagery, map the severity of drought-induced beech dieback in the Ajoie (Canton Jura) since 2018, as validated against forester-assessed ground truth?

- **Sub-question 1:** How reliably are beech crowns detected (share of reference trees matched to a crown)?
- **Sub-question 2:** How accurately are crowns classified as healthy, unhealthy or dead, compared with the random forest baseline of the STDL project HETRES?
- **Sub-question 3:** How well does the model transfer to a spatially held-out site?

**Study area:** the two HETRES sub-areas in the Ajoie, near Miécourt and near Beurnevésin (about 5 km² together, 600–700 m altitude, 2 km apart). Items marked *(verify)* are assumptions that still need confirming.

## 0. Task framing

- **Stage 1, crown detection:** a 4-band chip (R, G, B, NIR) goes in, crown polygons come out (instance segmentation, with the *arborizer* crown segmenter as baseline). Restricted to beech.
- **Stage 2, health class:** each crown gets an ordinal class (1 = healthy, 2 = unhealthy, 3 = dead). With only point labels, this is crown-level classification on crown-centred crops, not pixel-wise segmentation.
- **Metrics:** stage 1 = share of reference trees within 4 m of a detected crown (as in HETRES) plus a visual check on a subset; stage 2 = overall accuracy, per-class sensitivity, macro-F1 and quadratic weighted kappa.
- **Baseline:** HETRES reports an overall accuracy of up to 0.79 on a random 70/30 split. A spatial split will likely score lower, so the numbers are not directly comparable.

## 1. Imagery and annotation sources

- **Imagery (primary):** SWISSIMAGE RS 2020, RGB+NIR, 10 cm, public for Jura.
- **Imagery (upgrade):** the 3 cm RGB+NIR flight and LiDAR of August 2022, owned by the Canton of Jura *(verify access)*.
- **Ground truth:** 226 beeches (76 healthy, 77 unhealthy, 73 dead) assessed by foresters in August–October 2022, as points *(verify access, e.g. via the HETRES repository or the canton)*.
- **Time gap:** labels are from 2022, SWISSIMAGE RS from 2020. HETRES adapted the label locations to the 2020 imagery, and symptoms may have changed in between.
- **Context layer (optional):** yearly NDVI difference from waldmonitoring.ch. The 2018–2019 difference was the most important descriptor in HETRES.
- **Beech mask:** reference trees are beech only, so predictions for other species must be masked out *(verify which species layer is available)*.
- **Extra labels (optional):** dead trees are clearly visible on false-colour imagery, so a small set can be added by photo-interpretation.

## 2. Tile size, stride, overlap

- **Resample to 20 cm GSD** *(verify against native 10 cm)*, **tiles of 512 × 512 px (about 102 × 102 m), stride 384 (25% overlap) for train only**, no overlap in val/test.
- **Why:** a beech crown of 10 m spans about 50 px at 20 cm, enough for detection, and 100 m gives stand context.
- **Edge rule:** keep a crown in a tile if at least 50% lies inside, applied identically in all splits.
- **Stage 2 crops:** 64 × 64 px (12.8 m) around each labelled crown, four bands.
- **Volume:** about 95 non-overlapping tiles per km², so roughly 450 for the 5 km² *(forest share to be checked)*. SWISSIMAGE RS needs about 620 MB per km².

## 3. Batch pairing

- **Naming:** `{aoi}_{year}_{row}_{col}` for tiles and `{aoi}_{year}_{crownID}` for crops, with a `crowns.gpkg` table holding crown ID, health class, split, tile ID and match distance.
- **Point-to-crown matching:** join each reference point to the nearest crown within 4 m, resolve conflicts by nearest centroid, and inspect mismatches on a false-colour view.
- **CRS:** keep the native Swiss grid (EPSG:2056).
- **Stage 2 inputs:** train on matched reference crowns, test end-to-end on predicted crowns to measure error propagation from stage 1.

## 4. Split strategy

- **Across areas:** Miécourt for training and validation, Beurnevésin as a fully held-out test. Check class counts per area first. If a class is too rare in one, run both directions (train Miécourt, test Beurnevésin, and the reverse).
- **Within Miécourt:** spatial block k-fold (k = 5, blocks of at least 200 m, with a buffer), reporting mean and spread. HETRES notes that labelled trees show spatial autocorrelation, which inflates random-split scores.
- **Optional qualitative test:** the Val Terbi area, where damage was also observed but no reference data exists.

## 5. First tile batch

Generate about 50 tiles from Miécourt and about 30 crops per class. Check that reference points fall inside the right crown, and look for NIR shifts, shadows and seams between flight strips.

## Reflection

- **Biggest risk:** only 226 labels. Use pretrained backbones, strong augmentation, and the optional photo-interpreted labels.
- **Segmentation errors:** crown detection misses hidden trees and over- or under-segments complex crowns. Evaluate stage 1 and stage 2 separately and end-to-end.
- **Class confusion:** HETRES confused healthy and unhealthy trees most, so report per-class sensitivity, not only overall accuracy.
- **Transfer:** HETRES found that a model needs retraining for a new acquisition and area, so expect weaker transfer to other sites.
- **Fallback:** if crown-level deep learning underperforms, use the random forest with crown statistics as a strong baseline and compare.
- **Parameters to document:** GSD, tile size, stride, overlap, edge rule, crop size, match distance, block size, buffer, CRS, imagery year, label date, class mapping.

## Sources

- [CLASSIFY – Health status of beech trees (swisstopo)](https://www.swisstopo.admin.ch/en/classify-health-status-of-beech-trees)
- [HETRES technical documentation (STDL)](https://tech.stdl.ch/PROJ-HETRES/)
- [arborizer crown segmentation tool](https://github.com/RaffiBienz/arborizer)
