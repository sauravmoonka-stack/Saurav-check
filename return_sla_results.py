#!/usr/bin/env python3
"""Export return SLA query results to CSV"""

import snowflake.connector
import configparser
import os
import base64
import csv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

config_path = os.path.expanduser("~/.snowflake/credentials/sf.ini")
config = configparser.ConfigParser()
config.read(config_path)

user = config.get('default', 'user')
private_key_path = config.get('default', 'private_key')
passphrase_b64 = config.get('default', 'passphrase', fallback=None)

passphrase = None
if passphrase_b64:
    passphrase = base64.b64decode(passphrase_b64)

try:
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase,
            backend=default_backend()
        )

    conn = snowflake.connector.connect(
        user=user,
        private_key=private_key,
        account="YLEFPTS-QDP_EU",
        warehouse="DEV_COMPUTE_WH",
        database="DW_PROD_STRUCTURED"
    )

    cursor = conn.cursor()

    query = """
with return_base as (select
(convert_timezone('UTC', 'Europe/London',r.return_delivered_at)) as Delivered_date,
(convert_timezone('UTC', 'Europe/London',received_at)) as received_date,
case when received_at is not null then datediff(seconds,Delivered_date,received_at)/(3600*24)
- (DATEDIFF(week, Delivered_date, received_at) * 2)
        +CASE
            WHEN DAYNAME(Delivered_date) = 'Sat' THEN 1
            WHEN DAYNAME(Delivered_date) = 'Sun' THEN 1
            ELSE 0
          END
end as RTS,
 r.return_id,
 warehouse_return_line_item_status,
count(distinct ru.return_unit_id) as items_claimed,
count(distinct case when received_at is not null then wr.return_line_item_id end) as items_received,
count(distinct case when received_at is not null and
case when received_at is not null then datediff(seconds,Delivered_date,received_at)/(3600*24)
- (DATEDIFF(week, Delivered_date, received_at) * 2)
        +CASE
            WHEN DAYNAME(Delivered_date) = 'Sat' THEN 1
            WHEN DAYNAME(Delivered_date) = 'Sun' THEN 1
            ELSE 0
          END
end <=2
then wr.return_line_item_id end) as items_within_SLA

from DW_PROD_STRUCTURED.OMS.RETURN_DIM r
left join DW_PROD_STRUCTURED.OMS.RETURN_UNIT_DIM ru on r.return_id = ru.return_id and ru.is_active = true
left join (select return_line_item_id ,min(warehouse_return_line_item_status) as warehouse_return_line_item_status ,min(received_at) as received_at from dw_prod_raw.hevo_supply_chain.mysql_rds_warehouse_return_line_item wr where __hevo__marked_deleted = false
group by all) wr on ru.return_unit_id = wr.return_line_item_id

where r.region_id = 103 and r.return_status != 'CANCELLED'
and date(r.return_created_at_utc) >= '2026-08-06'
and  r.is_active = true
and return_delivered_at is not null
group by all
order by 1
)
select * from return_base where received_date is null and date(Delivered_date)< current_date()-1
order by Delivered_date desc
    """

    cursor.execute(query)
    results = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]

    # Export to CSV
    csv_path = r"C:\Users\SauravMoonka\Downloads\Saurav-check\return_sla_results.csv"

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(col_names)
        writer.writerows(results)

    print(f"✓ Results exported to: {csv_path}")
    print(f"✓ Total records: {len(results)}")
    print(f"\nColumns exported:")
    for col in col_names:
        print(f"  - {col}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
