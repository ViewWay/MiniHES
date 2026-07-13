#!/usr/bin/env python3
"""Generate 1-year test data for MiniHES and import into MongoDB.

Reads template_meter.json (exported from Puma-01_DCPP_DailyCheck),
generates 3 projects x 8 meters, inserts directly into MongoDB.

Usage:
    cd docs/testdata && python3 generate_testdata_mongo.py
"""

import json
import copy
import random
import os
import subprocess
from datetime import datetime, timedelta

random.seed(42)

PROJECTS = [
    {"name": "Cusk-01_DCPP_DailyCheck", "serial_base": 2025030100001},
    {"name": "Andromeda-01_DailyCheck", "serial_base": 2025031500001},
    {"name": "Draco-01_DCPP_DailyCheck", "serial_base": 2025040100001},
]

METERS = 8
DATA_START = datetime(2024, 6, 1)
DAYS_IN_YEAR = 365
COLLECT_BASE = datetime(2025, 6, 1, 9, 0, 0)

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(HERE, "template_meter.json")


def nint(v):
    """Wrap integer as MongoDB canonical JSON numberInt."""
    return {"$numberInt": str(v)}


def dlms_ts(dt):
    return dt.strftime("%Y-%m-%d %w %H:%M:%S") + " 00,FF88,80"


def dlms_day(dt):
    return dt.strftime("%Y-%m-%d %w") + " 00:00:00 00,FF88,80"


def load_template():
    with open(TEMPLATE_FILE) as f:
        data = json.load(f)
    data.pop("_id", None)
    return data


def set_val(sheets, kvp, sheet_name, control_name, attr_name, value):
    """Set value in both sheets and key_value_pairs."""
    if sheet_name not in sheets:
        return False
    for obj in sheets[sheet_name]["objects"]:
        if obj.get("controlName") == control_name and obj.get("attributeName") == attr_name:
            obj["value"] = value
            kvp[obj["key"]] = value
            return True
    return False


def season_factor(month):
    if month in (6, 7, 8, 12, 1, 2):
        return random.uniform(1.0, 1.8)
    return random.uniform(0.4, 1.0)


def make_meter(template, serial, pos):
    r = copy.deepcopy(template)
    sheets = r["sheets"]
    kvp = r["key_value_pairs"]

    dev_id = f"{serial:011d}"
    meter_no = f"KFM{dev_id}"

    # Timestamp
    ts = COLLECT_BASE + timedelta(minutes=random.randint(0, 180))
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond:06d}"
    r["timestamp"] = ts_str
    r["source_file"] = f"data/{meter_no}/XMLFunctionLists_Meter_PP.xlsx"

    # Basic Information
    set_val(sheets, kvp, "Basic Information", "E-meter Logic device name", "E-meter Logic device name", meter_no)
    set_val(sheets, kvp, "Basic Information", "E-meter Serial Number", "E-meter Serial Number", dev_id)

    # Energy parameters
    base_e = random.randint(50000, 250000)
    avg_d = random.randint(300, 900)

    # Calculate 1-year cumulative energy
    total_e = base_e
    for d in range(DAYS_IN_YEAR):
        dt = DATA_START + timedelta(days=d)
        total_e += int(avg_d * season_factor(dt.month))

    e_r1 = int(total_e * 0.95)
    e_r2 = total_e - e_r1
    e_neg = random.randint(0, 50)

    set_val(sheets, kvp, "Energy", "Cumulative A Positive", "Value", nint(total_e))
    set_val(sheets, kvp, "Energy", "Cumulative A Positive rate1", "Value", nint(e_r1))
    set_val(sheets, kvp, "Energy", "Cumulative A Positive rate2", "Value", nint(e_r2))
    set_val(sheets, kvp, "Energy", "Cumulative A Negative", "Value", nint(e_neg))
    set_val(sheets, kvp, "Energy", "Cumulative A Negative rate1", "Value", nint(e_neg))
    set_val(sheets, kvp, "Energy", "Cumulative A Negative rate2", "Value", nint(0))

    # Daily Billing (365 entries)
    db_buf = {}
    e = base_e
    for d in range(DAYS_IN_YEAR):
        dt = DATA_START + timedelta(days=d)
        e += int(avg_d * season_factor(dt.month))
        db_buf[str(d)] = [
            dlms_day(dt), nint(random.randint(30, 200)),
            nint(e), nint(0), nint(0), nint(0)
        ]
    set_val(sheets, kvp, "Daily Billing", "E-meter Daily Billing", "Buffer", db_buf)
    set_val(sheets, kvp, "Daily Billing", "E-meter Daily Billing", "Entries in use", nint(DAYS_IN_YEAR))
    set_val(sheets, kvp, "Daily Billing", "E-meter Daily Billing", "Profile entries", nint(DAYS_IN_YEAR))

    # Monthly Billing (12 entries)
    mb_buf = {}
    monthly_e = base_e
    dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_offset = 0
    for m in range(12):
        month_start = DATA_START + timedelta(days=day_offset)
        dim = dpm[m]
        month_end = month_start + timedelta(days=dim - 1)
        for _ in range(dim):
            monthly_e += int(avg_d * season_factor(month_start.month))
        mb_buf[str(m)] = [
            dlms_day(month_end), nint(random.randint(30, 200)),
            nint(monthly_e), nint(0), nint(0), nint(0)
        ]
        day_offset += dim
    set_val(sheets, kvp, "Month Billing", "E-meter Monthly Billing", "Buffer", mb_buf)
    set_val(sheets, kvp, "Month Billing", "E-meter Monthly Billing", "Entries in use", nint(12))
    set_val(sheets, kvp, "Month Billing", "E-meter Monthly Billing", "Profile entries", nint(13))

    # Load Profile (96 entries, 1 day)
    lp_buf = {}
    ld = DATA_START + timedelta(days=random.randint(0, DAYS_IN_YEAR - 1))
    ev = base_e
    for i in range(96):
        t = ld + timedelta(minutes=15 * i)
        h = t.hour
        if 6 <= h <= 9 or 17 <= h <= 22:
            f = random.uniform(1.3, 2.5)
        elif 0 <= h <= 5:
            f = random.uniform(0.1, 0.4)
        else:
            f = random.uniform(0.5, 1.2)
        ev += int(avg_d / 96 * f)
        lp_buf[str(i)] = [dlms_ts(t), nint(8), nint(ev), nint(0)]
    set_val(sheets, kvp, "Load Profile", "Energy Profile", "Buffer", lp_buf)

    # Instantaneous Data
    v = random.randint(218, 235)
    i_ = random.randint(0, 30)
    p_total = random.randint(50, 500)
    p_l1 = random.randint(0, p_total // 3)
    p_l2 = random.randint(0, p_total // 3)
    p_l3 = max(0, p_total - p_l1 - p_l2)

    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous current (Sum of all phases)", "Value", nint(i_))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Current L1", "Value", nint(max(0, i_ + random.randint(-5, 5))))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Current L2", "Value", nint(max(0, i_ + random.randint(-5, 5))))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Current L3", "Value", nint(max(0, i_ + random.randint(-5, 5))))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Voltage L1", "Value", nint(v))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Voltage L2", "Value", nint(v + random.randint(-3, 3)))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous Voltage L3", "Value", nint(v + random.randint(-3, 3)))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous active power (+P) Total", "Value", nint(p_total))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous active power (+P) L1", "Value", nint(p_l1))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous active power (+P) L2", "Value", nint(p_l2))
    set_val(sheets, kvp, "Instantaneous Data", "Instantaneous active power (+P) L3", "Value", nint(p_l3))

    # Update all object timestamps
    for sn, sd in sheets.items():
        if "objects" in sd:
            for obj in sd["objects"]:
                obj_ts = ts + timedelta(milliseconds=random.randint(100, 50000))
                obj["timestamp"] = obj_ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{obj_ts.microsecond:06d}"

    return r


def main():
    print("Loading template...")
    tpl = load_template()
    print(f"Template: {len(tpl['sheets'])} sheets\n")

    tmp_dir = os.path.join(HERE, "_tmp_import")
    os.makedirs(tmp_dir, exist_ok=True)

    for proj in PROJECTS:
        name = proj["name"]
        base = proj["serial_base"]

        print(f"Project: {name}")

        for i in range(METERS):
            serial = base + i
            meter_no = f"KFM{serial:011d}"

            rec = make_meter(tpl, serial, i + 1)

            tmp_file = os.path.join(tmp_dir, f"{name}__{meter_no}.json")
            with open(tmp_file, "w") as f:
                json.dump(rec, f, ensure_ascii=False)

            result = subprocess.run(
                ["mongoimport", "--db", "minihes", "--collection", "meter_sessions",
                 "--file", tmp_file, "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  [{i + 1}/8] {meter_no} imported")
            else:
                print(f"  [{i + 1}/8] {meter_no} FAILED: {result.stderr.strip()}")

            os.remove(tmp_file)

        print(f"  -> Database '{name}' ready\n")

    # Cleanup
    if os.path.isdir(tmp_dir) and not os.listdir(tmp_dir):
        os.rmdir(tmp_dir)

    print("Done.")


if __name__ == "__main__":
    main()
