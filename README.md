# Olist E-commerce BI Data Warehouse

End-to-end Business Intelligence project: from raw e-commerce data to a star-schema data warehouse, an automated ETL pipeline and decision-oriented Power BI dashboards.

---

## 1. Project overview

This project simulates the work of a BI analyst at **Olist**, a Brazilian marketplace that connects small sellers to customers. Starting from 9 raw CSV files (about 100K orders, 2016-2018), the goal is to build the full analytics chain a company would use:

**Raw data -> Profiling and cleaning -> Data warehouse (star schema) -> ETL -> Dashboards -> Business insights**

The focus is not only on tools, but on answering real business questions with well-defined KPIs.

## 2. Business context and objectives

| Stakeholder | Key questions |
|---|---|
| Management | Is revenue growing? Which regions and product categories drive it? |
| Operations | Where are deliveries late, and how does lateness affect customer satisfaction? |
| Marketing | Who are the best customers? Do they come back? |
| Seller management | Which sellers perform well or badly? |

### KPIs (formal definitions in `docs/business_requirements.md`)

- **Revenue**: total item sales value
- **AOV (Average Order Value)**: revenue / number of orders
- **Repeat purchase rate**: customers with 2+ orders / total customers (based on `customer_unique_id`)
- **On-time delivery rate**: orders delivered on or before the estimated date / delivered orders
- **Average review score** and **cancellation rate**

## 3. Dataset

**Source:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

| File | Content | Grain (1 row = ...) |
|---|---|---|
| `olist_orders_dataset` | Order status and timestamps | one order |
| `olist_order_items_dataset` | Products per order, price, freight | one item in an order |
| `olist_order_payments_dataset` | Payment type and installments | one payment |
| `olist_order_reviews_dataset` | Review score and comments | one review |
| `olist_customers_dataset` | Customer location | one customer ID |
| `olist_products_dataset` | Category and dimensions | one product |
| `olist_sellers_dataset` | Seller location | one seller |
| `olist_geolocation_dataset` | Zip code to latitude/longitude | one geolocation point |
| `product_category_name_translation` | Portuguese to English categories | one category |

> The raw data is not stored in this repository (see `.gitignore`). Download it from Kaggle and place the CSV files in `data/raw/`.

## 4. Planned architecture
CSV files (Kaggle)
|
v
Extract + Clean (Python / pandas)
|
v
Staging layer (PostgreSQL)
|
v
Data warehouse (star schema: fact + dimension tables)
|
v
Power BI (DAX measures, dashboards)


An architecture diagram will be added in `docs/` once the design is finalized.

## 5. Tech stack

| Layer | Tools |
|---|---|
| Data exploration | Python, pandas, Jupyter |
| Storage / warehouse | PostgreSQL |
| ETL | Python scripts (optional orchestration with Airflow or dbt) |
| Visualization | Power BI (DAX) |
| Version control | Git, GitHub |

## 6. Repository structure

olist-bi-data-warehouse/
├── data/
│ ├── raw/ # original CSV files (not versioned)
│ └── processed/ # cleaned data (not versioned)
├── sql/ # schema creation and transformation scripts
├── etl/ # Python ETL scripts
├── notebooks/ # exploration and profiling notebooks
├── dashboards/ # Power BI files and screenshots
├── docs/ # requirements, data dictionary, ERD, architecture
├── .gitignore
└── README.md


## 7. Roadmap and progress

### Step 1: Business framing, setup and data understanding
- [x] Create the GitHub repository and project structure
- [x] Configure `.gitignore` (data and secrets excluded)
- [x] Write the project README
- [ ] Define stakeholders, business questions and KPIs (`docs/business_requirements.md`)
- [ ] Download the dataset and profile it (`notebooks/01_data_profiling.ipynb`)
- [ ] Document data quality issues (`docs/data_quality_notes.md`)
- [ ] Draw the source ER diagram (`docs/source_erd.png`)

### Step 2: Data warehouse design
- [ ] Define the grain of each fact table
- [ ] Design fact tables (sales, deliveries) and dimensions (customer, product, seller, date, geography)
- [ ] Create the star schema in PostgreSQL

### Step 3: ETL pipeline
- [ ] Extract and clean the source data
- [ ] Load staging, then dimensions, then facts
- [ ] Add data quality checks and logging

### Step 4: Dashboards
- [ ] Connect Power BI to the warehouse
- [ ] Build DAX measures for the KPIs
- [ ] Create executive, operations and customer dashboards

### Step 5: Insights and documentation
- [ ] RFM customer segmentation and cohort retention
- [ ] "Findings and recommendations" page
- [ ] Final documentation, screenshots and demo

## 8. Data quality points to handle

Identified from the dataset documentation, to be confirmed during profiling:

- `customer_id` is generated **per order**; the real customer is `customer_unique_id`
- Only `delivered` orders should be used for delivery KPIs
- Delivery dates are null for non-delivered orders
- The geolocation table has many rows per zip-code prefix and must be aggregated
- Product category names are in Portuguese and need translation

## 9. How to run (will be completed as the project progresses)

```bash
# 1. Clone the repository
git clone https://github.com/fidayahyaoui7/olist-bi-data-warehouse.git
cd olist-bi-data-warehouse

# 2. Download the dataset from Kaggle and place the CSVs in data/raw/

# 3. Create a virtual environment and install dependencies
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/Mac: source .venv/bin/activate
```

## 10. Results

Dashboards, screenshots and key insights will be added here at the end of the project.

## 11. Author

**Your Name**: student in software engineering, ENSI (Université de la Manouba)
GitHub: [fidayahyaoui7](https://github.com/fidayahyaoui7) | LinkedIn: *add your link*
