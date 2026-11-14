"""Build all Sentinel-2 composites and ancillary layers (same as notebook 02, but as a
script so it can run unattended).
Usage: python scripts/build_composites.py [year ...]   (no years = all)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sds_utils as su  # noqa: E402

YEARS = [2017, 2018, 2019, 2020, 2022, 2024, 2025, 2026]

if __name__ == "__main__":
    for aoi in su.AOIS:
        su.load_ancillary(aoi)
        print(aoi, "ancillary ok", flush=True)
    years = [int(a) for a in sys.argv[1:]] or YEARS
    for y in years:  # year-major order: the change years (2017-2019) are ready first
        for aoi in su.AOIS:
            for w in su.WINDOWS:
                t = time.time()
                try:
                    c = su.build_composite(aoi, y, w)
                    print(f"{aoi} {y} {w}: {c.attrs.get('n_scenes')} scenes, "
                          f"valid {float((c['n_obs'] > 0).mean()):.3f}, {time.time() - t:.0f} s", flush=True)
                except Exception as e:
                    print(f"{aoi} {y} {w}: FAILED {e!r}"[:200], flush=True)
