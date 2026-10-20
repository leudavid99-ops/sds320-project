# Data inventory – SDS320 project

Project question: How well can Sentinel-2-derived vegetation stress indices identify and map the severity of drought-induced forest dieback in the Jura/Valais region since the severe 2018 summer drought, compared to already documented damage patterns?
Study area: Valais (Rhône valley, Pinus sylvestris dieback; core test area Pfynwald/Leuk). Jura = optional comparison area if time allows.
Time period: Summer composites (Jun–Aug) 2017 (pre-drought baseline), 2018 (drought), 2019–2025 (recovery/dieback)

---

Main raster dataset: Sentinel-2 L2A surface reflectance
Provider: ESA / Copernicus
Access route: STAC API (Earth Search by Element84 on AWS, no login) – alternatives: Copernicus Data Space Ecosystem, Microsoft Planetary Computer
Search criteria: bbox of study area, datetime 2017-06-01 to 2025-08-31, collection `sentinel-2-l2a`, eo:cloud_cover < 20 %, summer months only
Useful assets or bands: B04 red, B08 NIR, B05/B06/B07 red edge, B8A, B11/B12 SWIR, SCL (scene classification for cloud/shadow masking)
Indices to derive: NDVI, NDMI (moisture, B08/B11), NDRE (B08/B05), NBR (B08/B12), EVI; delta vs. 2017 baseline
Resolution / coverage: 10 m (VIS/NIR), 20 m (red edge/SWIR), revisit ~5 days, archive from 2017 for Europe
Expected output: Per-pixel anomaly (index change vs. baseline) per year and a dieback-severity map for the study area
Main limitation: Clouds/snow/shadow in alpine terrain; 10–20 m pixels mix healthy and dead trees; phenology and slope/aspect effects can mimic stress

---

Main vector/context dataset: Reference and forest context layers (to be verified for availability and licence)

| Dataset | Provider | Access route | Role in project | Geometry |
|---|---|---|---|---|
| Forest area (swissTLM3D, Wald) | swisstopo | geo.admin.ch / opendata.swiss | Context: forest mask to restrict analysis | Polygon |
| Vegetation Height Model (NFI) | WSL / BAFU | Download via WSL / geo.admin.ch | Context: forest height, stand structure, filter out non-forest | Raster (1 m) |
| Forest mixture degree (Waldmischungsgrad) | WSL / BAFU | geo.admin.ch / opendata.swiss | Context/stratification: conifer vs. broadleaf (pine dieback) | Raster |
| swissIMAGE (orthophoto) | swisstopo | WMTS / Download | Validation: visual check of dead crowns | Raster |
| swissALTI3D (DEM) | swisstopo | Download | Context: slope, aspect, elevation | Raster |
| Documented damage data (Canton Valais forest service; WSL/ICP Forests) | Canton VS / WSL | Request / literature | Labels/validation: documented dieback patterns | Polygon/point (to be checked) |

Role in project: Forest mask and stratification (context), documented damage as reference for evaluation
Main limitation: Documented damage data may not be openly available or may be spatially incomplete – fallback is visual validation with swissIMAGE and published studies

---

Small test:
What I tested: (planned) STAC search for Sentinel-2 L2A over a small bbox around Pfynwald, summers 2017/2018/2022, cloud cover < 20 %; load one scene, compute NDVI/NDMI (see `notebooks/01_data_search.ipynb`)
What worked: – (to fill in after running the notebook)
What did not work: – (to fill in)
Next decision: Confirm study area (Valais only vs. + Jura), choose main index, check availability of reference damage data

---

## Documentation

| Dataset | Format | CRS | Licence / attribution |
|---|---|---|---|
| Sentinel-2 L2A | COG/JP2 via STAC | UTM 32N (EPSG:32632) | Copernicus open data policy – attribute "Contains modified Copernicus Sentinel data [year]" |
| swisstopo layers | GeoTIFF / GPKG / Shapefile | CH1903+/LV95 (EPSG:2056) | swisstopo OGD – free use, source must be cited (to verify per dataset) |
| NFI/WSL layers | GeoTIFF | EPSG:2056 | Check per dataset before publishing |

## Reflection

1. Most central dataset: Sentinel-2 L2A time series.
2. Main data risk: No reliable reference/damage labels → evaluation unclear.
3. Smallest test: One bbox, one summer scene per year (2017/2018/2022), NDVI/NDMI map overlay on swissIMAGE.
4. Still to check: Licence of cantonal/WSL damage data and VHM before publishing results.
5. Simplification if access gets hard: Smaller area (Pfynwald only), fewer years, NDVI/NDMI only, visual validation instead of reference labels.
