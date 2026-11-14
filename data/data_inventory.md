# Data acquisition plan – SDS320 (refined)

**Project question:**
How well can Sentinel-2 (10 m) separate healthy, declining and dead beech canopy after the 2018 drought, and does a model trained in the Aargau transfer to the Ajoie (JU)? A second stage (high-resolution NIR, true crowns, ordinal damage class per crown) follows once the Sentinel-2 baseline is understood.

**Study area:** three AOIs (approximate bounding boxes, to be replaced by HETRES / forest-service polygons)

| AOI | Role | Bbox (lon/lat) | Rationale |
|---|---|---|---|
| Ajoie (JU) | target / out-of-region test | 7.02, 47.39 – 7.20, 47.50 | Beech dieback area of the swisstopo/STDL CLASSIFY project |
| Fricktal / Tafeljura (AG) | training / validation | 7.93, 47.42 – 8.10, 47.53 | Comparable limestone, beech-dominated forest |
| Rhone valley (VS) | domain-shift test | 7.50, 46.25 – 7.70, 46.35 | Dry inner-alpine valley; mostly pine/oak, not a like-for-like beech case |

**Time period:** 2017 (pre-drought baseline), 2018 (drought), 2019–2026 (lagged mortality, current state). Two windows per year: 15 Jun–31 Jul (peak) and 15 Aug–30 Sep (late, senescence).

---

## Main raster dataset
**Dataset:** Sentinel-2 L2A surface reflectance
**Provider:** ESA / Copernicus, hosted on Microsoft Planetary Computer
**Access route:** STAC API (`pystac-client`), windowed COG reads with `rasterio`, no login. Alternative: Copernicus Data Space Ecosystem.
**Search criteria:** collection `sentinel-2-l2a`, bbox per AOI, the two windows above, `eo:cloud_cover < 70`, pixel-level cloud mask from the SCL band.
**Useful assets or bands:** B02, B03, B04, B08 (10 m); B05, B07, B8A, B11, B12 (20 m, resampled to 10 m); SCL. Derived: NDVI, NDRE, CIre, NDMI, NBR.
**Expected output:** cloud-masked median composites per AOI, year and window; per-unit stress features (ΔNDVI vs 2017 etc.) for the training notebook.
**Main limitation:** 10 m is too coarse for individual beech crowns (1–2 pixels), so objects are canopy units, not crowns. Year-to-year NDVI differences also mix drought signal with phenology and haze. Processing baseline ≥ 04.00 requires the +1000 DN offset to be handled.
**Licence / attribution:** free and open; cite "Contains modified Copernicus Sentinel data [year]".

## Main vector / context datasets
| Dataset | Provider | Access route | Role | Main limitation |
|---|---|---|---|---|
| ESA WorldCover 2021 | ESA (Planetary Computer) | STAC `esa-worldcover` | context: forest mask | no species, single epoch |
| Copernicus DEM GLO-30 | ESA (Planetary Computer) | STAC `cop-dem-glo-30` | context: elevation, slope, aspect | 30 m source |
| Beech health labels (STDL HETRES) | Canton of Jura (via STDL) | **not public**; request from the canton | **labels / validation** | proprietary; 226 trees, Jura only |
| TESSERA embeddings | Univ. of Cambridge (geotessera) | `geoai.tessera_download`, no login | alternative features (128-d, 10 m, annual) | embedding dimensions have no physical meaning |
| WSL "1000 beech trees" | WSL / EnviDat | EnviDat download | possible labels for the Aargau-type region | coordinates and site overlap unverified |
| swissBOUNDARIES3D | swisstopo | geo.admin.ch OGD | context: boundaries, map layout | no ecological content |
| Forest species / mixture map | FOEN / WSL | to be identified | beech-specific mask | product not yet identified |

Full list with formats, CRS and licence notes: `data_inventory.csv`.

---

## Small test
**What I tested:** `notebooks/01_data_search.ipynb`: one AOI (Ajoie), one 2 × 2 km subset, window late 2018, STAC search, loading of the least cloudy scene (B04, B08, SCL), NDVI map, valid-pixel share, plus a check for label files. Results are written to `data/data_test_results.csv`.
**What worked:** the STAC search (16 scenes for late summer 2018, best scene 0.04 % cloud, 23 s), loading the least cloudy scene for the subset (27 s), the SCL mask (99.8 % valid pixels) and NDVI (median 0.72). All years 2017–2026 have at least 8 scenes per window.
**What did not work:** no labels. The HETRES ground truth is not public (checked 14 Nov 2026: the STDL repository holds code only, the data belong to the Canton of Jura). No beech-specific forest mask identified yet. Loading the full Ajoie AOI with `odc-stac` + dask hung (two MGRS tiles in different UTM zones); the composites are now read with plain `rasterio` (`scripts/sds_utils.py`).
**Next decision:**
1. Obtain beech health labels (HETRES ground truth or WSL data). Without labels the training notebook can only run with circular proxy labels.
2. Decide whether Valais stays as third AOI or is replaced by a beech-dominated region (e.g. in the Pre-Alps), since pine/oak forest tests a different question.
3. Request the NIR orthophoto data for the second (high-resolution) stage.

---

## Reflection
1. **Most central dataset:** Sentinel-2 for the baseline; the beech health labels decide whether the project can be evaluated at all.
2. **Main data risk:** missing or unusable labels, followed by 10 m resolution versus crown size.
3. **Smallest useful test:** the 2 × 2 km, single-scene test above.
4. **Open licence / sharing issues:** HETRES labels, WSL data, any NIR orthophotos; Sentinel-2, WorldCover and DEM attribution wording to be verified before publishing.
5. **If access gets harder:** shrink to Ajoie plus Aargau only, fewer years (2017–2019 plus one recent year), stand-level instead of unit-level classes.

## Sources
- swisstopo (2025): CLASSIFY – Gesundheitsgrad von Buchen. https://www.swisstopo.admin.ch/de/classify-gesundheitsgrad-von-buchen
- STDL PROJ-HETRES documentation: https://tech.stdl.ch/PROJ-HETRES/
- Course template: https://hendrikwulf.github.io/sds320-jb/book/lessons/l02/project-transfer/
