# Project transfers, lesson by lesson

Each SDS320 lesson ends with a "project transfer" task. This file lists what was asked, the decision for this project, and where it is implemented. Project: canopy decline in beech-dominated forest of the Ajoie (JU) after the 2018 drought, Sentinel-2 first, high-resolution RGB+NIR later.

| Lesson | Transfer task | Status | Where |
|---|---|---|---|
| L01 Introduction | project idea sketch | done | `README.md` |
| L02 Data acquisition | data acquisition plan + small test | done | `data/data_inventory.md`, `data/data_inventory.csv`, `notebooks/01_data_search.ipynb` |
| L03 Visualization | interactive map, styled layer, split panel | done | `notebooks/03_project_visualization.ipynb`, `notebooks/04_data_visualization.ipynb` |
| L04 Training data | training data preparation plan | done (plan) | `docs/L04_training_data_preparation_plan.md` |
| L05 Image recognition | image recognition plan | plan | below |
| L06 Object detection | detection plan, first prototype | prototype | `notebooks/05_treecanopy_objectdetection.ipynb`, below |
| L07 Semantic segmentation | segmentation plan, first model output | implemented (weak labels) | `notebooks/06_train_test_workflow.ipynb`, `notebooks/08_regression_embeddings_segmentation.ipynb` |
| L08 Instance segmentation | plan, workflow diagram | plan | below, `README.md` (workflow) |
| L09 Image translation | plan, draft figure | not used (reasoned) | below, `notebooks/07_change_detection.ipynb` (figure) |
| L10 Change detection | change detection plan | implemented | `notebooks/07_change_detection.ipynb` |
| L11 Regression | regression plan | implemented | `notebooks/08_regression_embeddings_segmentation.ipynb` |
| L12 Segment Anything | prompt-based segmentation plan | plan | below |
| L13 Embeddings | embedding plan | implemented | `notebooks/08_regression_embeddings_segmentation.ipynb` |

A constraint runs through all of them: **the forester-assessed labels (HETRES, 226 beeches) and the 3 cm RGB+NIR flight are property of the Canton of Jura and not public** (checked 14 Nov 2026; the STDL repository holds code only). Everything that needs crown-level labels is therefore a plan. Everything implemented uses public Sentinel-2 data and a decline proxy, and says so.

## L05 Image recognition plan (stage 2: crown health)

- **Classes:** healthy, unhealthy, dead (HETRES scheme, merged by STDL from five forester classes). Three classes are kept because HETRES showed that finer classes are not separable even with LiDAR and 3 cm imagery.
- **Folder structure:** `data/training/{train,val,test}/{healthy,unhealthy,dead}/{aoi}_{year}_{crownID}.tif`, 64 × 64 px RGB+NIR chips at 20 cm, masked to the crown.
- **Baseline:** ResNet-50 pretrained on ImageNet, first convolution extended to four channels (NIR initialised from the red weights), nominal cross-entropy head. Comparison: the same backbone with an ordinal (CORAL) head, and the Random Forest on crown statistics as the simple baseline.
- **Evaluation:** macro-F1, balanced accuracy, quadratic weighted kappa, confusion matrix; split by site (train Miécourt, test Beurnevésin) with spatial block CV inside the training site.
- **Expected confusion:** healthy vs unhealthy, the pair HETRES confused most. Dead crowns should be easy on NIR.
- **Status:** needs the labels and imagery. No accuracy to report.

## L06 Object detection plan (stage 1: crown detection)

- **Target class:** one class, "tree crown" (overstory). Beech is selected afterwards with a species or stand mask.
- **Annotation source and budget:** no crown boxes exist. Budget: about 300 crowns drawn by hand on SWISSIMAGE RS tiles (roughly 4 hours), plus the 226 HETRES reference points as a recall check if they become available.
- **Model:** `fasterrcnn_resnet50_fpn_v2` (course default) fine-tuned from COCO weights; DeepForest (RetinaNet, pretrained on tree crowns) as a zero-shot comparison.
- **Metric:** mAP@0.5 as primary metric, since crown outlines are fuzzy and a tight box is not the point; confidence threshold 0.3 to favour recall, because a missed crown cannot be classified in stage 2.
- **Failure mode:** merged crowns in closed beech canopy, where neighbouring crowns interlock.
- **Prototype implemented (week 6):** `notebooks/05_treecanopy_objectdetection.ipynb` detects "canopy units" on 10 m Sentinel-2 NIR with local maxima and a marker-controlled watershed. It is the classical counterpart of a detector and feeds the unit table of notebook 06. At 10 m a unit is a group of trees, not a crown.

## L07 Semantic segmentation plan

- **Classes:** binary, *persistent decline* vs *other forest* (non-forest ignored). Multi-class health needs field labels.
- **Imagery and bands:** Sentinel-2 late-summer composites of 2017 and 2018, nine bands each (B02, B03, B04, B05, B07, B08, B8A, B11, B12), stacked to 18 channels.
- **Label source:** weak labels from the change rule of notebook 07 (relative NDVI drop in 2019 that persists in 2020). The labels come from later years than the input, so the model has to anticipate decline from the drought-year image.
- **Architecture:** U-Net with a ResNet-34 encoder (`geoai.train_segmentation_model`, `num_channels=18`, `num_classes=2`).
- **Metrics and imbalance:** IoU, F1, precision and recall of the decline class; the class covers only a few percent of the forest, so class weights are used and overall accuracy is not reported.
- **Split:** region-based. Train in the western part of the Fricktal, validate in the eastern part (no shared tiles), test in the Ajoie.
- **Output:** probability raster and class raster (GeoTIFF); vector patches only after a minimum mapping unit.
- **Implemented:** notebook 08, part C. Later, with the aerial imagery: same recipe at 20 cm with dead-crown masks from photo-interpretation.

## L08 Instance segmentation plan

- **Target objects:** individual beech crowns, one polygon each.
- **Label source:** hand-delineated crowns (some exist in HETRES, others are buffered points; availability unconfirmed).
- **Bands and resolution:** RGB+NIR resampled to 20 cm; a pretrained RGB model (Mask R-CNN / Detectree2) first sees a false-colour NIR-R-G composite, which needs no change to the input layer.
- **Confidence and post-processing:** threshold 0.5; `min_area` 4 m² (drops understory fragments), `max_hole_area` 1 m², vectorisation, then `geoai.add_geometric_properties` for crown area and perimeter.
- **Failure mode:** over-segmentation of large, irregular beech crowns into several instances; checked by counting predicted crowns per reference crown.
- **Status:** plan. Sentinel-2 cannot resolve instances.

## L09 Image translation plan

- **Used?** No. Super-resolving Sentinel-2 to "see" crowns would create detail that was never observed, and health classes read from generated texture would not be evidence.
- **Possible visual use:** a super-resolved backdrop for presentation maps, clearly labelled as generated.
- **Uncertainty:** not applicable to the analysis since no generated pixels enter it.
- **Claim to avoid:** "single crowns were mapped from Sentinel-2".
- **Documentation rule:** every map states the sensor and the pixel size; observed (10 m) and any generated detail are never mixed in one layer.

## L10 Change detection plan

Implemented in `notebooks/07_change_detection.ipynb`.

- **Change type and output:** canopy decline; continuous (ΔNDVI, ΔNDMI, ΔNBR) and categorical (stable, low in 2018 only, decline 2019 only, persistent decline 2019–2020), as GeoTIFF and as vector patches.
- **Dates and comparability:** late-summer median composites (15 Aug – 30 Sep) of 2017 (baseline) and 2018–2020; same sensor, window and grid; comparability table with valid observations and forest median per year.
- **Method:** traditional index differencing. ChangeStar from the lesson targets building change on high-resolution imagery and is not applicable.
- **Threshold strategy:** fixed value, Otsu and robust z-score compared; the z-score (≤ −1.5) is used, with a persistence rule and a 300 m² minimum mapping unit.
- **Validation:** informal. NDVI/NDMI flag agreement, multi-year trajectories per category, split map on SWISSIMAGE.

## L11 Regression plan

Implemented in notebook 08, part A.

- **Continuous target:** ΔNDVI late summer 2019 − 2017 per 10 m forest pixel.
- **Reference data and pairing:** the target is measured by Sentinel-2 itself one year after the input (2017 and 2018 bands); input and target share the grid, so pairing is exact.
- **Valid range:** target limited to [−1, 1] at tiling; predictions clipped to the same range at inference; non-forest pixels excluded from all metrics.
- **Architecture and loss:** U-Net with ResNet-34 encoder (`geoai.train_pixel_regressor`), Huber loss, because harvested pixels are outliers that would dominate MSE. Baselines: the 2018 change alone (linear fit) and a Random Forest on pixel features.
- **Evaluation:** RMSE, MAE, R² on the Ajoie (never used in training), plus a residual map and an observed-vs-predicted scatter as spatial checks.

## L12 Segment Anything plan

- **Target feature:** dead and defoliated crowns (bright, low-NIR objects) and canopy gaps on the aerial imagery.
- **Prompt type:** box prompts from the stage 1 detector; text prompts ("dead tree") only as an exploratory comparison, since health is not a visual category these models were trained on.
- **Filtering and post-processing:** predicted IoU ≥ 0.8, area between 4 and 300 m², overlap removal.
- **Processing:** tiled (512 px, 20 cm), batch over the two HETRES sites.
- **Validation:** share of reference trees whose point falls in exactly one mask; visual audit of 50 masks per site.
- **Status:** plan. SAM has no useful objects to segment at 10 m.

## L13 Embeddings plan

Implemented in notebook 08, part B.

- **Analysis goal:** (1) does change between annual embeddings point to the same places as the index-based change map; (2) are embeddings better features than hand-made indices for the decline proxy.
- **Dataset:** TESSERA pixel embeddings (128 dimensions, 10 m, annual, via `geoai.tessera_download`), because they are built from Sentinel-1/2 time series at the same resolution as the rest of the project and need no account. Patch embeddings (Clay) are too coarse for single stands. AlphaEarth is the alternative but needs Earth Engine access.
- **Labels:** no field labels. The decline proxy from notebook 07 gives labels for every forest pixel; with HETRES, 226 points would be realistic.
- **Validation:** spatial block cross-validation inside the embedding tile, per-class precision, recall and F1, class balance reported.
- **What an embedding result would not prove:** that the embedding "knows" tree health. High agreement with the proxy shows that embeddings encode the same spectral-temporal signal as NDVI change, and nothing about the cause of the decline.
