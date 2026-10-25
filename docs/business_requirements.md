# Business Requirements

## 1. Context
Olist is a Brazilian marketplace connecting small sellers to customers. This project builds a data warehouse and dashboards to support decisions on sales, delivery performance, customer behavior and sellers.

## 2. Stakeholders and questions

| Stakeholder | Questions | Dashboard |
|---|---|---|
| Management | Is revenue growing? Which states and categories drive it? | Executive overview |
| Operations | Where are deliveries late? Does lateness hurt reviews? | Delivery performance |
| Marketing | Who are the best customers? How many come back? | Customer analysis |
| Seller management | Which sellers generate revenue or complaints? | Seller performance |

## 3. KPI definitions

| KPI | Definition | Source tables |
|---|---|---|
| Revenue | Sum of `price` of order items (freight excluded, reported separately) for orders not canceled or unavailable | order_items, orders |
| Freight value | Sum of `freight_value` | order_items |
| Orders | Count of distinct `order_id` | orders |
| AOV | Revenue / number of orders | order_items, orders |
| Repeat purchase rate | Customers (`customer_unique_id`) with 2+ distinct orders / total customers | orders, customers |
| On-time delivery rate | Delivered orders with `order_delivered_customer_date` <= `order_estimated_delivery_date` / delivered orders | orders |
| Average delay (days) | Delivered date minus estimated date, for late orders only | orders |
| Average review score | Mean of `review_score` (1 to 5) | order_reviews |
| Cancellation rate | Orders with status `canceled` / total orders | orders |

## 4. Business rules (to validate during profiling)
- The real customer is `customer_unique_id`, not `customer_id` (generated per order).
- Delivery KPIs only use orders with status `delivered`.
- Revenue excludes `canceled` and `unavailable` orders.
- Product category names are translated to English.

## 5. Scope
- **In scope:** orders from 2016 to 2018, Brazil only, sales, delivery, customers, sellers, reviews.
- **Out of scope:** real-time data, marketing spend, profit margins (no cost data available).

## 6. Assumptions and limits
- The dataset is a public sample; names are anonymized.
- No cost data, so we measure revenue, not profit.
- Rules above may be refined after data profiling (changes will be logged in `docs/data_quality_notes.md`).
