"""Run the UK speed query, compute the RM-tab metrics, and render rm_dashboard.html.

Usage:
  python build_rm.py              # query Snowflake (browser SSO), then render
  python build_rm.py --from-csv   # render from the last saved uk_speed_metrics.csv
"""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SQL_FILE = HERE / "uk_speed.sql"
CSV_FILE = HERE / "uk_speed_metrics.csv"
TEMPLATE = HERE / "rm_template.html"
OUT_FILE = HERE / "rm_dashboard.html"
CARRIER = "ROYAL_MAIL"
DAILY_DAYS = 42


def fetch() -> pd.DataFrame:
    import snowflake.connector

    conn = snowflake.connector.connect(
        account="YLEFPTS-QDP_EU",
        user="SAURAV.MOONKA@ONEQUINCE.COM",
        authenticator="SNOWFLAKE_JWT",
        private_key_file=str(HERE / "rsa_key.p8"),
        role="DEV_RO_ROLE",
        warehouse="DEV_COMPUTE_WH",
    )
    try:
        cur = conn.cursor()
        cur.execute(SQL_FILE.read_text(encoding="utf-8"))
        df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
    finally:
        conn.close()
    df.to_csv(CSV_FILE, index=False)
    return df


def ratio(n, d):
    return None if not d else n / d


def metrics(rows: pd.DataFrame, backlog) -> dict:
    s = lambda c: float(pd.to_numeric(rows[c], errors="coerce").fillna(0).sum())
    mx = lambda c: (float(pd.to_numeric(rows[c], errors="coerce").max())
                    if rows[c].notna().any() else None)
    collected, delivered, attempted = s("SHIPMENTS"), s("SHIPMENTS_DELIVERED"), s("DELIVER_ATTEMPTED_SHIPMENTS")
    rts, issues = s("RTS"), s("DELIVER_ISSUE")
    lit_hub, lit_del = s("LIT_PICKUP_TO_HUB"), s("LIT_HUB_TO_DELIVERY")
    return {
        "collected": collected,
        "delivered": delivered,
        "attempted": attempted,
        "onTimeDelivered": s("ON_TIME_DELIVERED"),
        "onTimeAttempted": s("ON_TIME_DELIVERED_ATTEMPTED"),
        "rts": rts,
        "issues": issues,
        "firstAttemptRate": ratio(s("SHIPMENTS_DELIVERED_FIRST_ATTEMPT"), delivered + rts + issues + lit_del),
        "onTimeRate": ratio(s("ON_TIME_DELIVERED"), attempted),
        "onTimeAttemptRate": ratio(s("ON_TIME_DELIVERED_ATTEMPTED"), attempted),
        "slaRate": ratio(s("WITHIN_SLA_SHIPMENTS"), attempted),
        "arrivalToHub": ratio(s("COLLECTION_TO_FIRST_SCAN_DAYS"), collected),
        "transit": ratio(s("SUM_LM_INJECTION_TO_DELIVERED"), delivered),
        "transitP90": mx("TT_P90"),
        "transitAttempt": ratio(s("SUM_LM_INJECTION_TO_DELIVERY_ATTEMPTED"), attempted),
        "transitAttemptP90": mx("TTA_P90"),
        "litHub": lit_hub,
        "litHubValue": s("LIT_PICKUP_TO_HUB_VALUE"),
        "litDelivery": lit_del,
        "litDeliveryValue": s("LIT_HUB_TO_DELIVERY_VALUE"),
        "litRate": ratio(lit_hub + lit_del, collected),
        "backlog": backlog,
        # Raw sums so the page can re-total rates over any selected range.
        "firstAttemptNum": s("SHIPMENTS_DELIVERED_FIRST_ATTEMPT"),
        "withinSla": s("WITHIN_SLA_SHIPMENTS"),
        "sumArrivalToHub": s("COLLECTION_TO_FIRST_SCAN_DAYS"),
        "sumTransit": s("SUM_LM_INJECTION_TO_DELIVERED"),
        "sumTransitAttempt": s("SUM_LM_INJECTION_TO_DELIVERY_ATTEMPTED"),
    }


def with_lit_hub(m: dict, expected: pd.DataFrame) -> dict:
    # LiT flag 1 parcels were never collected, so they have no pickup date;
    # count them on their expected pickup date (UK arrival + 2 days) instead.
    m["litHub"] = float(expected["LIT_PICKUP_TO_HUB"].fillna(0).sum())
    m["litHubValue"] = float(expected["LIT_PICKUP_TO_HUB_VALUE"].fillna(0).sum())
    m["litRate"] = ratio(m["litHub"] + m["litDelivery"], m["collected"])
    return m


def build(df: pd.DataFrame) -> dict:
    df = df.copy()
    for c in ("DATE_RANGE", "PICKUP_DATE", "PICKUP_WEEK",
              "EXPECTED_PICKUP_DATE_MAX", "EXPECTED_PICKUP_WEEK_MAX"):
        df[c] = pd.to_datetime(df[c]).dt.date
    speed = df[df["SHIPMENT_CARRIER_NAME"] == CARRIER]
    backlog = (df[df["CARRIER"] == CARRIER]
               .drop_duplicates(["CARRIER", "DATE_RANGE"])
               .set_index("DATE_RANGE")["COLLECTION_BACKLOG"].to_dict())
    bl = lambda d: (None if d not in backlog or pd.isna(backlog[d]) else float(backlog[d]))

    today = date.today()
    this_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    first_week = min(speed["PICKUP_WEEK"].dropna())
    weekly, wk = [], this_sunday
    while wk >= first_week:
        m = metrics(speed[speed["PICKUP_WEEK"] == wk], bl(wk))
        weekly.append({"period": wk.isoformat(),
                       **with_lit_hub(m, speed[speed["EXPECTED_PICKUP_WEEK_MAX"] == wk])})
        wk -= timedelta(days=7)
    daily = []
    for i in range(DAILY_DAYS):
        d = today - timedelta(days=i)
        m = metrics(speed[speed["PICKUP_DATE"] == d], bl(d))
        daily.append({"period": d.isoformat(),
                      **with_lit_hub(m, speed[speed["EXPECTED_PICKUP_DATE_MAX"] == d])})
    return {"generatedAt": datetime.now().astimezone().isoformat(timespec="minutes"),
            "carrier": CARRIER, "weekly": weekly, "daily": daily}


def main():
    df = pd.read_csv(CSV_FILE) if "--from-csv" in sys.argv else fetch()
    data = build(df)
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    OUT_FILE.write_text(html, encoding="utf-8")
    w = next(r for r in data["weekly"] if r["collected"])
    print(f"Wrote {OUT_FILE.name}: {len(data['weekly'])} weeks, {len(data['daily'])} days; "
          f"latest week {w['period']} collected={w['collected']:.0f} delivered={w['delivered']:.0f}")


if __name__ == "__main__":
    main()
