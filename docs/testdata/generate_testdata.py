#!/usr/bin/env python3
"""Generate MiniHES test data: multiple projects, 8 KFM meters each, 1 year of data.

Reads demo3.txt as template, produces one JSON file per project.
Each file is a JSON array of 8 complete DLMS meter records.

IDIS meter number format: KFM + YYYYMMDDNNNNN (16 chars total)
  - KFM: manufacturer code
  - YYYYMMDD: manufacturing date
  - NNNNN: 5-digit sequential serial number

Usage:
    cd docs/testdata && python3 generate_testdata.py
"""

import json
import copy
import random
import re
import os
from datetime import datetime, timedelta

random.seed(42)

PROJECTS = [
    {"name": "Cusk-01_DCPP_DailyCheck", "serial_base": 2025030100001},
    {"name": "Andromeda-01_DailyCheck", "serial_base": 2025031500001},
    {"name": "Draco-01_DCPP_DailyCheck", "serial_base": 2025040100001},
]

METERS = 8
DATA_START = datetime(2024, 6, 1)  # 1 year: 2024-06-01 ~ 2025-05-31
DATA_END = datetime(2025, 5, 31)
DAYS_IN_YEAR = 365
COLLECT_BASE = datetime(2025, 6, 1, 3, 0, 0)

HERE = os.path.dirname(os.path.abspath(__file__))


def load_template():
    with open(os.path.join(HERE, "demo3.txt")) as f:
        text = f.read()
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    return json.loads(text)


def dlms_ts(dt):
    """DLMS timestamp: YYYY-MM-DD W HH:MM:SS 00,FF88,80"""
    return dt.strftime("%Y-%m-%d %w %H:%M:%S") + " 00,FF88,80"


def dlms_day(dt):
    """DLMS date for billing: YYYY-MM-DD W 00:00:00 00,FF88,80"""
    return dt.strftime("%Y-%m-%d %w") + " 00:00:00 00,FF88,80"


def ts_iso(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{random.randint(100000, 999999)}"


def make_meter(tpl, serial, pos):
    r = copy.deepcopy(tpl)

    dev_id = f"{serial:011d}"
    meter_no = f"KFM{dev_id}"

    # Connection
    cs = COLLECT_BASE + timedelta(minutes=random.randint(0, 60))
    dur = round(random.uniform(2, 6), 1)
    ce = cs + timedelta(seconds=dur)

    r["_id"] = ts_iso(ce + timedelta(seconds=random.randint(0, 30)))
    r["pos"] = pos
    r["connection_start"] = cs.strftime("%Y-%m-%d %H:%M:%S")
    r["connection_end"] = ce.strftime("%Y-%m-%d %H:%M:%S")
    r["connection_consume"] = dur

    # Identity
    r["1,0.0.96.1.0.255,2#Device ID&value"] = dev_id
    r["1,0.0.42.0.0.255,2#LogicalName&value"] = meter_no

    # Clock
    ct = ce + timedelta(seconds=random.randint(1, 8))
    r["actual_time"] = ts_iso(ct)
    r["8,0.0.1.0.0.255,2#Clock&time"] = dlms_ts(ct)
    r["currently_time"] = ct.strftime("%Y-%m-%d %H:%M:%S")

    # Profile / reading timing
    gps = ct + timedelta(seconds=random.randint(1, 3))
    gpe = gps + timedelta(seconds=round(random.uniform(0.3, 0.6), 6))
    r["getProfile_start_time"] = ts_iso(gps)
    r["getProfile_end_time"] = ts_iso(gpe)

    rs = gps + timedelta(seconds=random.randint(5, 15))
    rd = round(random.uniform(8, 18), 6)
    r["reading_status"] = True
    r["reading_start_time"] = ts_iso(rs)
    r["reading_end_time"] = ts_iso(rs + timedelta(seconds=rd))
    r["reading_consume"] = rd

    # Energy parameters
    base_e = random.randint(50000, 250000)
    avg_d = random.randint(300, 900)

    # Daily Billing Profile (365 entries = 1 year)
    db = {}
    e = base_e
    for d in range(DAYS_IN_YEAR):
        dt = DATA_START + timedelta(days=d)
        # Seasonal variation: summer/winter higher consumption
        month = dt.month
        if month in (6, 7, 8, 12, 1, 2):
            season_factor = random.uniform(1.0, 1.8)
        else:
            season_factor = random.uniform(0.4, 1.0)
        e += int(avg_d * season_factor)
        db[str(d)] = [dlms_day(dt), 8, e, 0, 0, 0]
    r["7,1.0.99.2.0.255,2#Daily Billing Profile&buffer"] = db
    r["7,1.0.99.2.0.255,7#Daily Billing Profile&entries_in_use"] = DAYS_IN_YEAR
    r["7,1.0.99.2.0.255,8#Daily Billing Profile&profile_entries"] = DAYS_IN_YEAR

    # Monthly Billing Profile (12 entries = 1 year)
    mb = {}
    monthly_e = base_e
    for m in range(12):
        month_start = DATA_START + timedelta(days=sum([31,28,31,30,31,30,31,31,30,31,30,31][:m]))
        if month_start.month == 2:
            days_in_month = 28
        else:
            days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31][month_start.month - 1]
        month_end = month_start + timedelta(days=days_in_month - 1)
        # Sum daily increments for this month
        for _ in range(days_in_month):
            mm = month_start.month
            sf = random.uniform(1.0, 1.8) if mm in (6, 7, 8, 12, 1, 2) else random.uniform(0.4, 1.0)
            monthly_e += int(avg_d * sf)
        mb[str(m)] = [dlms_day(month_end), 8, monthly_e, 0, 0, 0]
    r["7,1.0.98.1.0.255,2#Monthly Billing Profile&buffer"] = mb
    r["7,1.0.98.1.0.255,7#Monthly Billing Profile&entries_in_use"] = 12
    r["7,1.0.98.1.0.255,8#Monthly Billing Profile&profile_entries"] = 13

    # Load Profile (96 entries, 15-min intervals, 1 day)
    lp = {}
    ld = DATA_START + timedelta(days=random.randint(0, DAYS_IN_YEAR - 1))
    ev = base_e
    for i in range(96):
        ts = ld + timedelta(minutes=15 * i)
        h = ts.hour
        if 6 <= h <= 9 or 17 <= h <= 22:
            factor = random.uniform(1.3, 2.5)
        elif 0 <= h <= 5:
            factor = random.uniform(0.1, 0.4)
        else:
            factor = random.uniform(0.5, 1.2)
        ev += int(avg_d / 96 * factor)
        lp[str(i)] = [dlms_ts(ts), 8, ev, 0]
    r["7,1.0.99.1.0.255,2#Load profile with period 1&buffer"] = lp

    # Power Quality Profile (96 entries)
    pq = {}
    for i in range(96):
        ts = ld + timedelta(minutes=15 * i)
        pq[str(i)] = [
            dlms_ts(ts), 8,
            0, 0, 0,
            8, random.randint(80, 150), 0,
            0, 3, random.randint(80, 150), 0,
            0, 0
        ]
    r["7,1.0.99.1.1.255,2#PowerQualityProfile1&buffer"] = pq

    # Register values
    v = random.randint(218, 235)
    i_ = random.randint(0, 30)
    p = random.randint(50, 500)

    r["3,1.0.1.8.0.255,2#Active energy import&value"] = e
    r["3,1.0.1.8.1.255,2#Active energy import rate 1&value"] = e
    r["3,1.0.1.8.2.255,2#Active energy import rate 2&value"] = 0
    r["3,1.0.2.8.0.255,2#Active energy export&value"] = 0
    r["3,1.0.2.8.1.255,2#Active energy export rate 1&value"] = 0
    r["3,1.0.2.8.2.255,2#Active energy export rate 2&value"] = 0

    for ph, ln in [(32, "L1"), (52, "L2"), (72, "L3")]:
        r[f"3,1.0.{ph}.7.0.255,2#Instantaneous voltage {ln}&value"] = v + random.randint(-3, 3)
        r[f"3,1.0.{ph - 1}.7.0.255,2#Instantaneous current {ln}&value"] = max(0, i_ + random.randint(-10, 10))
        r[f"3,1.0.{ph}.25.0.255,2#Last Average Voltage {ln}&value"] = v + random.randint(-2, 2)
        r[f"3,1.0.{ph - 1}.25.0.255,2#Last Average Current {ln}&value"] = max(0, i_ + random.randint(-5, 5))

    r["3,1.0.1.7.0.255,2#Instantaneous active import power&value"] = p
    r["3,1.0.21.7.0.255,2#Instantaneous active import power L1&value"] = random.randint(0, p // 3)
    r["3,1.0.41.7.0.255,2#Instantaneous active import power L2&value"] = random.randint(0, p // 3)
    r["3,1.0.61.7.0.255,2#Instantaneous active import power L3&value"] = random.randint(0, p // 3)

    # Communication session log
    csl = {}
    for j in range(random.randint(2, 6)):
        lt = cs - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        csl[str(j)] = [dlms_ts(lt), random.randint(70, 80), random.randint(0, 100)]
    r["7,0.0.99.98.4.255,2#Communication Session Log&Buffer"] = csl

    return r


def main():
    print("Loading template...")
    tpl = load_template()
    print(f"Template: {len(tpl)} top-level keys\n")

    for proj in PROJECTS:
        name = proj["name"]
        base = proj["serial_base"]
        print(f"Project: {name}")

        records = []
        for i in range(METERS):
            serial = base + i
            rec = make_meter(tpl, serial, i + 1)
            records.append(rec)
            print(f"  [{i + 1}/8] KFM{serial:011d}")

        path = os.path.join(HERE, f"{name}.json")
        with open(path, "w") as f:
            json.dump(records, f, indent="\t", ensure_ascii=False)

        mb = os.path.getsize(path) / 1048576
        print(f"  -> {name}.json ({mb:.1f} MB)\n")

    print("Done.")


if __name__ == "__main__":
    main()
