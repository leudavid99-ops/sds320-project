"""Shared helpers for the SDS320 beech-dieback project (Sentinel-2 only, first step).

Used by notebooks 02-08. Network-dependent functions (STAC access) are kept
separate from pure numpy/xarray functions so the latter can be tested offline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths & constants
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
# Derived data (composites, features, models) are large and rebuilt by the notebooks. The
# ".nosync" suffix keeps the folder out of iCloud Drive: with a synced Desktop, iCloud uploaded
# and evicted the files while they were being written, which stalled and corrupted reads.
PROC = DATA / "derived.nosync"
LABELS = DATA / "labels"
FIGS = ROOT / "results" / "figures"
TABLES = ROOT / "results" / "tables"
for _p in (PROC, LABELS, FIGS, TABLES):
    _p.mkdir(parents=True, exist_ok=True)

CRS_UTM = "EPSG:32632"  # all three AOIs lie in UTM zone 32N
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

S2_BANDS = ["B02", "B03", "B04", "B05", "B07", "B08", "B8A", "B11", "B12"]
# SCL classes to drop: 0 no data, 1 saturated, 3 cloud shadow, 8/9 cloud (medium/high),
# 10 thin cirrus, 11 snow/ice
SCL_INVALID = [0, 1, 3, 8, 9, 10, 11]

# Two phenological windows per year (MM-DD). 'late' targets premature leaf
# senescence / canopy loss that appeared in late summer 2018 (Frei et al. 2022).
WINDOWS = {
    "peak": ("06-15", "07-31"),
    "late": ("08-15", "09-30"),
}

# --------------------------------------------------------------------------
# Areas of interest (WGS84 bbox: lon_min, lat_min, lon_max, lat_max)
# Approximate boxes - refine with the STDL HETRES polygons / forest-service data.
# --------------------------------------------------------------------------
AOIS = {
    "ajoie_ju": dict(
        label="Ajoie (JU)",
        bbox=(7.02, 47.39, 7.20, 47.50),
        role="target / out-of-region test",
        note="Beech dieback hotspot after 2018 drought (swisstopo/STDL CLASSIFY, WSL 'Ajoie' module).",
    ),
    "fricktal_ag": dict(
        label="Fricktal / Tafeljura (AG)",
        bbox=(7.93, 47.42, 8.10, 47.53),
        role="train / validation",
        note="Comparable limestone Jura-type, beech-dominated mixed forest; similar elevation range.",
    ),
    "valais_rhone": dict(
        label="Rhone valley (VS)",
        bbox=(7.50, 46.25, 7.70, 46.35),
        role="domain-shift test",
        note="Inner-alpine dry valley (Pfynwald area); mostly Scots pine/oak, NOT beech -> tests transferability.",
    ),
}


def aoi_gdf():
    """AOIs as GeoDataFrame (EPSG:4326) with area in km2 (computed in UTM)."""
    import geopandas as gpd
    from shapely.geometry import box

    rows = [dict(aoi=k, geometry=box(*v["bbox"]), **{kk: v[kk] for kk in ("label", "role", "note")})
            for k, v in AOIS.items()]
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    gdf["area_km2"] = gdf.to_crs(CRS_UTM).area / 1e6
    return gdf


# --------------------------------------------------------------------------
# Data access (needs internet; Microsoft Planetary Computer STAC, no login)
# --------------------------------------------------------------------------
def _catalog():
    import planetary_computer
    import pystac_client

    return pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def search_s2(bbox, start, end, max_cloud=70):
    """Sentinel-2 L2A items for bbox and ISO date range."""
    s = _catalog().search(
        collections=["sentinel-2-l2a"], bbox=bbox, datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
    )
    return list(s.item_collection())


def _baseline(item) -> float:
    return float(item.properties.get("s2:processing_baseline", "0"))


def aoi_grid(aoi, res=10):
    """Target grid of an AOI in UTM 32N, snapped to `res`: (transform, width, height, x, y)."""
    from rasterio.transform import from_origin
    from rasterio.warp import transform_bounds

    w, s, e, n = transform_bounds("EPSG:4326", CRS_UTM, *AOIS[aoi]["bbox"])
    w, s = np.floor(w / res) * res, np.floor(s / res) * res
    e, n = np.ceil(e / res) * res, np.ceil(n / res) * res
    width, height = int(round((e - w) / res)), int(round((n - s) / res))
    x = w + res * (np.arange(width) + 0.5)
    y = n - res * (np.arange(height) + 0.5)
    return from_origin(w, n, res, res), width, height, x, y


def read_on_grid(href, transform, width, height, resampling="bilinear", retries=3):
    """Read band 1 of a (remote) raster, warped onto the target grid. Windowed COG read
    through a WarpedVRT; plain rasterio, no dask (the odc-stac/dask path hung on AOIs
    that straddle two MGRS tiles in different UTM zones)."""
    import time
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.vrt import WarpedVRT

    err = None
    for k in range(retries):
        try:
            with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3",
                              GDAL_HTTP_RETRY_DELAY="1", GDAL_HTTP_TIMEOUT="30",
                              GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES", GDAL_HTTP_MULTIPLEX="YES",
                              VSI_CACHE="TRUE", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
                with rasterio.open(href) as src, WarpedVRT(
                        src, crs=CRS_UTM, transform=transform, width=width, height=height,
                        resampling=Resampling[resampling]) as vrt:
                    return vrt.read(1)
        except Exception as e:  # transient network errors
            err = e
            time.sleep(2 * (k + 1))
    raise err


def _threaded(fn, args, workers=16):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, args))


def composite_s2(items, aoi, bands=S2_BANDS, workers=16):
    """Cloud-masked per-pixel median composite of `items` on the AOI grid.

    Per scene the SCL layer gives the valid mask; reflectance = DN * 1e-4, minus the
    0.1 offset of processing baseline >= 04.00. Same-day scenes from overlapping MGRS
    tiles are merged first (first valid value), so a day counts once in the median.
    Works band by band to keep memory low. Returns xarray.Dataset (bands + n_obs)."""
    import xarray as xr

    tr, width, height, x, y = aoi_grid(aoi)
    items = sorted(items, key=lambda i: i.datetime)
    days = np.array([i.datetime.date().toordinal() for i in items])
    scl = _threaded(lambda i: read_on_grid(i.assets["SCL"].href, tr, width, height, "nearest"), items, workers)
    valid = [~np.isin(s, SCL_INVALID) for s in scl]
    off = [0.1 if _baseline(i) >= 4.0 else 0.0 for i in items]

    def merge_days(arrs):
        out = []
        for d in np.unique(days):
            m = None
            for k in np.where(days == d)[0]:
                m = arrs[k] if m is None else np.where(np.isfinite(m), m, arrs[k])
            out.append(m)
        return np.stack(out)

    data = {}
    for b in bands:
        dn = _threaded(lambda i: read_on_grid(i.assets[b].href, tr, width, height, "bilinear"), items, workers)
        refl = [np.where(v & (a > 0), np.clip(a.astype("float32") * 1e-4 - o, 0, 1), np.nan).astype("float32")
                for a, v, o in zip(dn, valid, off)]
        st = merge_days(refl)
        if "n_obs" not in data:
            data["n_obs"] = (("y", "x"), np.isfinite(st).sum(0).astype("int16"))
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                data[b] = (("y", "x"), np.nanmedian(st, axis=0).astype("float32"))
    ds = xr.Dataset(data, coords=dict(x=x, y=y))
    ds.attrs["n_days"] = int(len(np.unique(days)))
    return ds


def add_indices(ds):
    """Spectral indices. NDVI (Rouse 1974), NDRE (Gitelson & Merzlyak 1994),
    CIre (Gitelson et al. 2003), NDMI (Wilson & Sader 2002), NBR (Key & Benson 2006)."""
    def nd(a, b):
        s = a + b
        return ((a - b) / s).where(s != 0)

    ds = ds.copy()
    ds["NDVI"] = nd(ds["B08"], ds["B04"])
    ds["NDRE"] = nd(ds["B8A"], ds["B05"])
    ds["CIre"] = ds["B07"] / ds["B05"].where(ds["B05"] > 0) - 1
    ds["NDMI"] = nd(ds["B08"], ds["B11"])
    ds["NBR"] = nd(ds["B08"], ds["B12"])
    return ds


def open_nc(path):
    """Open a cached NetCDF file with an explicit engine (engine guessing is fragile)."""
    import xarray as xr

    return xr.open_dataset(path, engine="netcdf4")


def composite_path(aoi, year, window):
    return PROC / f"{aoi}_{year}_{window}.nc"


MAX_DAYS = 12  # per window: use the least cloudy acquisition days only (keeps downloads bounded)


def least_cloudy_days(items, max_days=MAX_DAYS):
    """Keep all scenes of the `max_days` acquisition days with the lowest scene cloud cover."""
    best = {}
    for i in items:
        d = i.datetime.date()
        best[d] = min(best.get(d, 101.0), i.properties.get("eo:cloud_cover", 100.0))
    keep = set(sorted(best, key=best.get)[:max_days])
    return [i for i in items if i.datetime.date() in keep]


def build_composite(aoi, year, window, max_cloud=70, overwrite=False):
    """Median composite of cloud-masked scenes in one window; cached as NetCDF."""
    import rioxarray  # noqa: F401
    import xarray as xr

    path = composite_path(aoi, year, window)
    if path.exists() and not overwrite:
        return open_nc(path).load()

    bbox = AOIS[aoi]["bbox"]
    d0, d1 = WINDOWS[window]
    items = search_s2(bbox, f"{year}-{d0}", f"{year}-{d1}", max_cloud)
    if not items:
        raise RuntimeError(f"No scenes for {aoi} {year} {window}")
    items = least_cloudy_days(items)
    comp = add_indices(composite_s2(items, aoi))
    comp = comp.rio.write_crs(CRS_UTM)
    comp.attrs.update(aoi=aoi, year=year, window=window, n_scenes=len(items))
    enc = {v: dict(zlib=True, complevel=4) for v in comp.data_vars}
    tmp = path.with_suffix(".tmp.nc")
    comp.to_netcdf(tmp, encoding=enc)
    tmp.replace(path)  # atomic: an interrupted run never leaves a half-written cache file
    return comp


def open_composite(aoi, year, window):
    import rioxarray  # noqa: F401
    import xarray as xr

    ds = open_nc(composite_path(aoi, year, window)).load()
    return ds.rio.write_crs(CRS_UTM)


def load_ancillary(aoi, ref=None, overwrite=False):
    """ESA WorldCover 2021 tree mask (`forest` = interior pixels, `forest_all` = all tree
    cover) + Copernicus DEM GLO-30 (elevation, slope, aspect) on the AOI grid. `ref` is kept for backwards compatibility and ignored."""
    import xarray as xr

    path = PROC / f"{aoi}_ancillary.nc"
    if path.exists() and not overwrite:
        return open_nc(path).load()

    cat = _catalog()
    bbox = AOIS[aoi]["bbox"]
    tr, width, height, x, y = aoi_grid(aoi)

    def mosaic(collection, asset, resampling, **kw):
        out = None
        for it in cat.search(collections=[collection], bbox=bbox, **kw).item_collection():
            a = read_on_grid(it.assets[asset].href, tr, width, height, resampling).astype("float32")
            if collection == "esa-worldcover":
                a[a == 0] = np.nan  # 0 = no data
            out = a if out is None else np.where(np.isfinite(out), out, a)
        return out

    wc = mosaic("esa-worldcover", "map", "nearest", datetime="2021-01-01/2021-12-31")
    elev = mosaic("cop-dem-glo-30", "data", "bilinear")
    slope, aspect = slope_aspect(elev, res=10.0)
    # Forest = WorldCover tree cover (class 10), shrunk by one pixel. Edge pixels mix canopy with
    # fields or roads and shift slightly between years, which shows up as false change.
    from scipy.ndimage import binary_erosion
    tree = wc == 10
    core = binary_erosion(tree, structure=np.ones((3, 3), bool), border_value=1)
    anc = xr.Dataset(dict(forest=(("y", "x"), core.astype("uint8")),
                          forest_all=(("y", "x"), tree.astype("uint8")),
                          elevation=(("y", "x"), elev), slope=(("y", "x"), slope),
                          aspect=(("y", "x"), aspect)), coords=dict(x=x, y=y))
    anc.to_netcdf(path, encoding={v: dict(zlib=True, complevel=4) for v in anc.data_vars})
    return anc


# --------------------------------------------------------------------------
# Pure numpy helpers (testable offline)
# --------------------------------------------------------------------------
def slope_aspect(elev: np.ndarray, res: float = 10.0):
    """Slope (deg) and aspect (deg, 0 = north, clockwise) from a DEM grid with y decreasing."""
    dz_dy, dz_dx = np.gradient(elev, res)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
    aspect = (np.degrees(np.arctan2(-dz_dx, dz_dy)) + 360) % 360  # rows run north->south
    return slope.astype("float32"), aspect.astype("float32")


def nan_gaussian(img: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian smoothing that ignores NaNs (normalised convolution)."""
    from scipy.ndimage import gaussian_filter

    m = np.isfinite(img).astype("float32")
    num = gaussian_filter(np.where(m > 0, img, 0).astype("float32"), sigma)
    den = gaussian_filter(m, sigma)
    out = np.where(den > 1e-3, num / np.maximum(den, 1e-3), np.nan)
    return np.where(m > 0, out, np.nan).astype("float32")


def detect_canopy_units(img, forest_mask, sigma=1.0, min_distance=2, min_value=None):
    """Local-maximum detection + marker-controlled watershed on a smoothed NIR/NDVI image.

    Method: local maximum filtering (Wulder et al. 2000; Popescu & Wynne 2004) to find
    treetop-like peaks, then watershed (Meyer & Beucher 1990) on the inverted image to
    delineate one region per peak. At 10 m a 'unit' is a small patch of neighbouring trees (median ~0.15 ha).
    Returns (peaks Nx2 array [row, col], labels int32 array, 0 = background).
    """
    from skimage.feature import peak_local_max
    from skimage.segmentation import watershed

    forest = forest_mask.astype(bool)
    sm = nan_gaussian(np.where(forest, img, np.nan), sigma)
    ok = forest & np.isfinite(sm)
    filled = np.where(np.isfinite(sm), sm, np.nanmin(sm))
    thr = np.percentile(sm[ok], 25) if min_value is None else min_value
    peaks = peak_local_max(filled, min_distance=min_distance, threshold_abs=thr,
                           labels=ok.astype(int), exclude_border=False)
    markers = np.zeros(img.shape, dtype="int32")
    markers[peaks[:, 0], peaks[:, 1]] = np.arange(1, len(peaks) + 1)
    labels = watershed(-filled, markers, mask=ok)
    return peaks, labels.astype("int32")


def labels_to_gdf(labels, transform, crs=CRS_UTM):
    """Polygonise a label raster (rasterio affine transform) -> GeoDataFrame with 'unit_id'."""
    import geopandas as gpd
    from rasterio import features
    from shapely.geometry import shape

    geoms = [(shape(g), int(v)) for g, v in
             features.shapes(labels.astype("int32"), mask=labels > 0, transform=transform)]
    return gpd.GeoDataFrame({"unit_id": [v for _, v in geoms]},
                            geometry=[g for g, _ in geoms], crs=crs)


def zonal_stats(labels: np.ndarray, layers: dict, stats=("mean", "std")) -> pd.DataFrame:
    """Per-label statistics of 2D arrays (NaN-aware). Returns DataFrame indexed by unit_id."""
    lab = labels.ravel()
    keep = lab > 0
    out = {}
    for name, arr in layers.items():
        s = pd.Series(arr.ravel()[keep]).groupby(lab[keep]).agg(list(stats))
        for st in stats:
            out[f"{name}_{st}"] = s[st]
    df = pd.DataFrame(out)
    df["n_pix"] = pd.Series(lab[keep]).value_counts().sort_index()
    df.index.name = "unit_id"
    return df


def dissimilarity_index(X_train: np.ndarray, X_new: np.ndarray, weights=None):
    """Simplified dissimilarity index (after Meyer & Pebesma 2021): distance of each new
    sample to its nearest training sample in standardised (optionally importance-weighted)
    feature space, divided by the mean pairwise training distance. Returns (DI_new, threshold)
    where threshold = Q3 + 1.5 IQR of the training leave-one-out DI (area of applicability)."""
    from scipy.spatial import cKDTree

    mu, sd = X_train.mean(0), X_train.std(0) + 1e-9
    w = np.ones(X_train.shape[1]) if weights is None else np.asarray(weights, float)
    Zt, Zn = (X_train - mu) / sd * w, (X_new - mu) / sd * w
    rng = np.random.default_rng(0)
    sub = Zt[rng.choice(len(Zt), min(len(Zt), 1000), replace=False)]
    d = np.sqrt(((sub[:, None, :] - sub[None, :, :]) ** 2).sum(-1))
    dbar = d[np.triu_indices(len(sub), 1)].mean()
    tree = cKDTree(Zt)
    di_new = tree.query(Zn, k=1)[0] / dbar
    di_tr = tree.query(Zt, k=2)[0][:, 1] / dbar  # leave-one-out nearest neighbour
    q1, q3 = np.percentile(di_tr, [25, 75])
    return di_new, q3 + 1.5 * (q3 - q1)


def robust_z(d):
    """Robust z-score (median / MAD) of an array, NaN-aware. Used as relative change threshold."""
    med = np.nanmedian(d)
    mad = np.nanmedian(np.abs(d - med))
    return (d - med) / (1.4826 * mad + 1e-9)


def index_delta(aoi, var, year, base=2017, window="late", min_obs=2):
    """Index difference year - base on forest pixels (NaN elsewhere or where < min_obs valid scenes)."""
    a, b = open_composite(aoi, year, window), open_composite(aoi, base, window)
    forest = load_ancillary(aoi)["forest"].values == 1
    ok = forest & (a["n_obs"].values >= min_obs) & (b["n_obs"].values >= min_obs)
    return np.where(ok, a[var].values - b[var].values, np.nan).astype("float32")


# --------------------------------------------------------------------------
# Plot helpers
# --------------------------------------------------------------------------
def stretch(a, lo=2, hi=98):
    v = a[np.isfinite(a)]
    l, h = np.percentile(v, [lo, hi])
    return np.clip((a - l) / (h - l + 1e-9), 0, 1)


def rgb(ds, bands=("B04", "B03", "B02"), lo=2, hi=98):
    return np.dstack([stretch(ds[b].values, lo, hi) for b in bands])


def overlay_png(da, cmap="RdYlGn", vmin=None, vmax=None):
    """DataArray (UTM) -> (RGBA uint8 array, [[south, west], [north, east]]) for folium overlays."""
    import matplotlib as mpl
    import rioxarray  # noqa: F401

    ll = da.rio.write_crs(CRS_UTM).rio.reproject("EPSG:4326")
    a = ll.values
    vmin = np.nanpercentile(a, 2) if vmin is None else vmin
    vmax = np.nanpercentile(a, 98) if vmax is None else vmax
    cm = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap
    rgba = cm((a - vmin) / (vmax - vmin + 1e-9), bytes=True)
    rgba[~np.isfinite(a), 3] = 0
    w, s, e, n = ll.rio.bounds()
    return rgba, [[s, w], [n, e]]
