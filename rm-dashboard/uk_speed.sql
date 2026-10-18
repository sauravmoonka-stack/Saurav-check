-- UK speed metrics: weekly OTD, P90, and split-shipment analysis by lane
-- Co-authored with CoCo
with time_horizon_data as (
      select 'Weekly' as time_horizon_value
    ),

      nrf as (
      select
      nrf.date,
      nrf.week_start_date,
      nrf.week,
      nrf.month_start_date,
      nrf.quarter_start_date,
      nrf.quarter,
      nrf.year,
      nrf.year_start_date,
      case
      when time_horizon_value = 'Daily'     then nrf.date
      when time_horizon_value = 'Weekly'    then week_start_date
      when time_horizon_value = 'Monthly'   then month_start_date
      when time_horizon_value = 'Quarterly' then quarter_start_date
      when time_horizon_value = 'Yearly'    then year_start_date
      end as final_date,
      case
      when time_horizon_value = 'Daily' then
      case
      when dayofweek(to_date(nrf.date)) = 0 then 'sun'
      when dayofweek(to_date(nrf.date)) = 1 then 'mon'
      when dayofweek(to_date(nrf.date)) = 2 then 'tue'
      when dayofweek(to_date(nrf.date)) = 3 then 'wed'
      when dayofweek(to_date(nrf.date)) = 4 then 'thu'
      when dayofweek(to_date(nrf.date)) = 5 then 'fri'
      when dayofweek(to_date(nrf.date)) = 6 then 'sat'
      end
      when time_horizon_value = 'Weekly'    then cast(week as string)
      when time_horizon_value = 'Monthly'   then cast(month_start_date as string)
      when time_horizon_value = 'Quarterly' then quarter
      when time_horizon_value = 'Yearly'    then cast(year as string)
      end as final_period_flag,
      case
      when time_horizon_value = 'Weekly'    then 53
      when time_horizon_value = 'Monthly'   then 13
      when time_horizon_value = 'Quarterly' then 5
      when time_horizon_value = 'Yearly'    then 2
      end as final_offset
      from dw_prod_structured.public.nrf_calendar nrf
      left join time_horizon_data
      where nrf.date < current_date
      ),

      o2d_legs_data as (
      select
      case
      when trim(lower(ld.location_country)) = 'india'
      then 'India to UK Customer'
      when trim(lower(ld.location_country)) = 'united kingdom of great britain and northern ireland'
      then 'UK to UK Customer'
      when trim(lower(ld.location_country)) = 'hong kong'
      then 'HK to UK Customer'
      when trim(lower(ld.location_country)) = 'china'
      then 'China to UK Customer'
      when trim(lower(ld.location_country)) = 'italy'
      then 'Italy to UK Customer'
      when trim(lower(ld.location_country)) in ('turkey', 'türkiye')
      then 'Turkey to UK Customer'
      else 'Rest World to UK Customer'
      end as lane_flag,
      shipment_carrier_name,
      q.order_name,
      q.shipment_id,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.order_date)   as order_date,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.pickup_date_pst) as lm_injection_date,
      ex.First_delivery_attempt,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.delivery_date_pst)  as delivered_date,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.fulfillment_created_at_pst)  as fulfillment_confirmed_at,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.fulfillment_fulfilled_at_pst) as fulfillment_fulfilled_at,
      convert_timezone('America/Los_Angeles', 'Europe/London', q.fulfillment_dispatched_at_pst) as fulfillment_dispatched_at,
    coalesce(convert_timezone('UTC', 'Europe/London',atd), convert_timezone('Asia/Hong_Kong', 'Europe/London',source_departure_time))                                                  as destination_departure_time,
      coalesce(convert_timezone('UTC', 'Europe/London',ata),destination_arrival_time)                                 as destination_arrival_time,

      case
      when to_date(
      convert_timezone('America/Los_Angeles', 'Europe/London', q.delivery_date_pst))
      <= to_date(q.max_edd)
     and q.delivery_date_pst  is not null
      then 1 else 0
      end as on_time_flag,

      case
      when to_date(    First_delivery_attempt)  <= to_date(q.max_edd)
      and First_delivery_attempt is not null
      then 1 else 0
      end as on_time_attempt_flag,

case when datediff(day,convert_timezone('America/Los_Angeles','Europe/London', q.pickup_date_pst),
     First_delivery_attempt)   <=
     case when
  REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^(AB|BT|CA|DD|GY|HS|IM|IV|JE|KA|KW|LD|PH|TD|TR|ZE).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^DG([1-9]|1[0-6])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^EH(3[6-8]|4[3-6])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^EX(1[8-9]|2[0-3]|3[5-7])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^FK(8|1[5-9]|2[0-1])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^G(58|60|6[2-3]|65|7[1-9]|8[0-4]|90)([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^KY(10|1[4-6])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^LA([8-9]|1[0-1]|2[1-3])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^LL(1[5-7]|2[0-1]|2[3-7]|3[2-9]|[4-6][0-9]|7[0-8])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^ML(1[0-2])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^NE(4[4-9]|61|6[5-9]|7[0-1])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^PA(2[0-9]|3[0-8]|4[1-9]|6[0-9]|7[0-8]|80)([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^PL([12][0-9]|3[0-5])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^PO(3[0-9]|4[0-1])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^SA(1[4-9]|[2-6][0-9]|7[0-3])([0-9]| |$).*')
  OR REGEXP_LIKE(TRIM(DESTINATION_ZIP), '^SY([6-9]|1[0-9]|2[0-5])([0-9]| |$).*')
     then 2 else 1 end
     and First_delivery_attempt is not null then 1 else 0 end as within_SLA_flag,

      case
      when to_date(coalesce(convert_timezone('UTC', 'Europe/London',ata),destination_arrival_time))
      < current_date() -3 and destination_arrival_time is not null
      and q.pickup_date_pst is  null
      then 1 else 0
      end as lit_flag1,

         case
      when to_date(convert_timezone('America/Los_Angeles','Europe/London', pickup_date_pst))
      < current_date() -2 and pickup_date_pst is not null
      and  First_delivery_attempt is null
      then 1 else 0
      end as lit_flag2,
           case
      when to_date(coalesce(convert_timezone('UTC', 'Europe/London',ata),destination_arrival_time))
      < current_date() -3 and destination_arrival_time is not null
      and q.pickup_date_pst is  null
      then gross_sales else 0
      end as lit_value1,
         case
      when to_date(convert_timezone('America/Los_Angeles','Europe/London', pickup_date_pst))
      < current_date() -2 and pickup_date_pst is not null
      and First_delivery_attempt is null
      then gross_sales else 0
      end as lit_value2,

      case when First_delivery_attempt
      is not null then 1 end                                            as shipments_delivery_attempted,
      case when delivery_date_pst
      is not null then 1 end                                            as shipments_delivered,
      case when convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_created_at_pst)
      is not null then 1 end                                            as fulfillment_confirmed,
      case when convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_fulfilled_at_pst)
      is not null then 1 end                                            as fulfillment_fulfilled,
      case when convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_dispatched_at_pst)
      is not null then 1 end                                            as fulfillment_dispatched,
      case when   coalesce(convert_timezone('UTC', 'Europe/London',atd), convert_timezone('Asia/Hong_Kong', 'Europe/London',source_departure_time))  is not null then 1 end                  as destination_departed,
      case when coalesce(convert_timezone('UTC', 'Europe/London',ata),destination_arrival_time)   is not null then 1 end                  as destination_arrived,
      case when q.pickup_date_pst      is not null then 1 end                  as lm_injected,
      case when coalesce(q.out_for_delivery_pst,q.delivery_date_pst)      is not null then 1 end                  as out_for_delivery,
      case when Delivery_issues_event is not null and RTS_event is null and  delivery_date_pst   is  null then 1 end                  as Del_issue,
      case when RTS_event   is not null and  delivery_date_pst   is  null then 1 end        as RTS,

      q.units_sold,
      q.gross_sales,

      -- Duration metrics (fractional days = seconds / 86400)
      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.order_date),

      convert_timezone('America/Los_Angeles', 'Europe/London', q.delivery_date_pst)
      ) / 86400.0                                                              as OTD,
           datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.order_date),

First_delivery_attempt
) / 86400.0                                                              as OTD_LM,

      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.order_date),
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_created_at_pst)
      ) / 86400.0                                                              as order_to_fulfillment_confirmed_days,

      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_created_at_pst),
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_fulfilled_at_pst)
      ) / 86400.0                                                              as fulfillment_confirmed_to_fulfill_days,

      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_fulfilled_at_pst),
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_dispatched_at_pst)
      ) / 86400.0                                                              as fulfillment_fulfill_to_dispatch_days,

      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_dispatched_at_pst),
      q.flight_departure_pst
      ) / 86400.0                                                              as fulfillment_to_flight_departure_days,

      datediff(second,
      q.flight_departure_pst,
      dateadd(hour, 7, q.flight_arrival_pst)
      ) / 86400.0                                                              as flight_days,

      datediff(second,
     coalesce(convert_timezone('UTC', 'Europe/London',ata),destination_arrival_time),
      convert_timezone('America/Los_Angeles','Europe/London', q.pickup_date_pst)
      ) / 86400.0                                                              as lm_injection_days,

      datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.pickup_date_pst),
      convert_timezone('America/Los_Angeles','Europe/London', q.delivery_date_pst)
      ) / 86400.0                                                              as lm_injection_to_delivered_days,
            datediff(second,
      convert_timezone('America/Los_Angeles','Europe/London', q.pickup_date_pst),
     First_delivery_attempt
      ) / 86400.0                                                              as lm_injection_to_delivered_attempted_days,

      case when count(distinct q.shipment_id) over (partition by q.order_name) > 1
      then 1 else 0 end                                                   as multi_shipment_orders,

      nrf.final_date                                                           as time_horizon_order_date,
      ww.final_date                                                            as time_horizon_injected_date

      from DW_PROD_STRUCTURED.OMS.SHIPMENT_AGGREGATES_V3 q
      left join dw_prod_raw.hevo_supply_chain.mysql_rds_flightticketdetails f on q.MASTER_AIRWAY_BILL = f.master_airway_bill and __hevo__marked_deleted = false
      left join (select shipment_id,
min(case when lb_status in ('order-returned-to-sender','order-shipment-exception','order-shipment-exception-delivery-attempt-failed','LM_Shipment_Delivered','order-in-transit-delivery-attempt-scheduled') then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as First_delivery_attempt,
min(case when lb_status in ('order-returned-to-sender') then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as RTS_event,
min(case when lb_status in ('order-shipment-exception','order-shipment-exception-delivery-attempt-failed','order-in-transit-delivery-attempt-scheduled') then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as Delivery_issues_event,
max(deliver_attempt_rank) as no_of_attempts,
min (case when deliver_attempt_rank =2 then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as Second_delivery_attempt,
min (case when deliver_attempt_rank =3 then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as Third_delivery_attempt,
min (case when deliver_attempt_rank =4 then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as Fourth_delivery_attempt,
min (case when deliver_attempt_rank =5 then convert_timezone('UTC', 'Europe/London',event_time) else null end ) as Fifth_delivery_attempt,
from (
select
*,
CASE
    WHEN lb_status IN (
        'order-returned-to-sender',
        'order-shipment-exception',
        'order-shipment-exception-delivery-attempt-failed',
        'LM_Shipment_Delivered',
        'order-in-transit-delivery-attempt-scheduled'
    ) then
COUNT(
        CASE WHEN lb_status IN (
            'order-returned-to-sender',
            'order-shipment-exception',
            'order-shipment-exception-delivery-attempt-failed',
            'LM_Shipment_Delivered',
            'order-in-transit-delivery-attempt-scheduled'
        ) THEN 1 END
    ) OVER (
        PARTITION BY shipment_id
        ORDER BY event_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) else null end as deliver_attempt_rank

from
DL_PROD.SHIPMENT_TRACKING_DB_SHIPMENT.TRACKING_HISTORY

where is_active = 1
--group by all
order by shipment_id desc, deliver_attempt_rank)
group by all
order by shipment_id desc
) ex on ex.shipment_id = q.shipment_id
      left join dw_prod_structured.oms.vw_location_dim ld
      on ld.location_id = q.location_id
      and ld.is_active   = true
      left join nrf
      on nrf.date = to_date(convert_timezone('America/Los_Angeles','Europe/London', q.order_date))
      left join nrf ww
      on ww.date = to_date(convert_timezone('America/Los_Angeles','Europe/London', q.pickup_date_pst))
      where q.region_id      = 103
      and q.fulfillment_id <> -1
      and convert_timezone('America/Los_Angeles','Europe/London', q.fulfillment_created_at_pst) is not null
      and 1=1 -- no filter on 'o2d_uk_speed_metrics.reporting_date_filter'

      and 1=1 -- no filter on 'o2d_uk_speed_metrics.lane_filter'

      ),
date_dimension AS (
  SELECT
    DATEADD(day, SEQ4(), '2026-07-29') AS KPI_date
  FROM
    TABLE(GENERATOR(ROWCOUNT => 1000))
),
one as(
SELECT to_date(KPI_date) as date_range
FROM date_dimension
WHERE KPI_date <= CURRENT_DATE()
),
backlog_data as (
select shipment_carrier_name as carrier,date_range,
count(distinct case when lit_flag1 =0 then  shipment_id else null end) as collection_backlog,
from one o left join o2d_legs_data o2d on
date(o2d.destination_arrival_time) < o.date_range and (o2d.lm_injection_date is null or date(o2d.lm_injection_date) >=o.date_range) and order_date >= '2026-07-24 19:00:00'::timestamp
group by all
order by 1,2
 ),
 wbr as (


      -- ── Aggregated weekly speed metrics ──────────────────────────────────
      select      shipment_carrier_name,
      DATE_TRUNC('WEEK', date(lm_injection_date)  + 1) - 1 as Pickup_week,
    date(lm_injection_date)  as Pickup_date,
          DATE_TRUNC('WEEK',  coalesce (date(destination_arrival_time),date(destination_departed))+2 + 1) - 1 as expected_pickup_week_max,
   coalesce (date(destination_arrival_time),date(destination_departed))+2 as expected_pickup_date_max,
    count(distinct shipment_id)                                              as shipments,
      coalesce(sum(shipments_delivered), 0)                                    as shipments_delivered,
     sum(on_time_flag) as on_time_delivered,
      sum(lm_injection_to_delivered_days)                                      as sum_lm_injection_to_delivered,
       coalesce(sum(lm_injected), 0)                                            as lm_injected_count,
      sum(units_sold)                                                          as units_sold,
      sum(gross_sales)                                                         as gross_sales,
      coalesce(sum(out_for_delivery), 0)                                            as out_for_delivery_count,
      sum(lit_flag1) as lit_pickup_to_hub,
      sum(lit_flag2) as lit_hub_to_delivery,
      sum(lit_value1) as lit_pickup_to_hub_value,
      sum(lit_value2) as lit_hub_to_delivery_value,
        sum(lm_injection_days)  as collection_to_first_scan_days,
        sum(Del_issue)  as Deliver_issue,
        sum(RTS)  as RTS,
             sum(on_time_attempt_flag) as on_time_delivered_attempted,
             sum(shipments_delivery_attempted)                                      as Deliver_attempted_shipments,

                   sum(lm_injection_to_delivered_attempted_days)                                      as sum_lm_injection_to_delivery_attempted,
                   sum(within_SLA_flag) as within_SLA_shipments,
                   PERCENTILE_DISC(.9) within group (order by lm_injection_to_delivered_attempted_days) as TTA_P90,
                   PERCENTILE_DISC(.9) within group (order by lm_injection_to_delivered_days) as TT_P90,

      coalesce(sum(case when date(First_delivery_attempt) = date(delivered_date) then shipments_delivered else 0 end), 0) as  shipments_delivered_first_attempt


from o2d_legs_data

          where order_date >= '2026-07-24 19:00:00'::timestamp
          and coalesce (date(destination_arrival_time),date(destination_departed)) <= current_date
          and shipment_carrier_name in ('ROYAL_MAIL','ROYAL_MAIL_RETURNS')
          group by all
          order by 1,2,3
      )
      select * from
     backlog_data full outer join wbr on date_range =  Pickup_date and carrier = shipment_carrier_name
    --wbr
    --backlog_data
    order by date_range
