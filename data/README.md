# Data

Nothing in this folder has to be downloaded by hand. The notebooks fetch all inputs from open sources.

| Path | Content | In git |
|---|---|---|
| `data_inventory.md`, `data_inventory.csv` | data acquisition plan: sources, access routes, licences, limitations | yes |
| `data_test_results.csv`, `scene_coverage_by_year.csv` | output of the small loading test in notebook 01 | yes |
| `processed/` | five small Ajoie GeoTIFFs (NDVI, NDMI 2017 and 2019, ΔNDVI) used by notebook 03 | yes |
| `derived.nosync/` | composites (`<aoi>_<year>_<window>.nc`), ancillary layers, canopy units, feature tables, TESSERA tiles, training tiles, models | no, rebuilt by notebooks 02, 05, 06, 07, 08 (about 6 GB) |
| `labels/` | optional field labels, `<aoi>_labels.gpkg` with column `damage_class` (0 healthy, 1 unhealthy, 2 dead) | no (none available) |

Rebuild everything: `python scripts/build_composites.py`, then run notebooks 05 to 08.

Sources and attribution:

- Sentinel-2 L2A, ESA WorldCover 2021, Copernicus DEM GLO-30: Microsoft Planetary Computer STAC (`https://planetarycomputer.microsoft.com/api/stac/v1`). Contains modified Copernicus Sentinel data.
- TESSERA embeddings: downloaded with `geoai.tessera_download` (package `geotessera`).
- The HETRES beech health labels and the 2022 RGB+NIR flight belong to the Canton of Jura and are not included.

`derived.nosync` carries the `.nosync` suffix so that iCloud Drive does not sync it.
