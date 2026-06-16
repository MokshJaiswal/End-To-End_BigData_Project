# Raw Data

This folder contains the raw CSV files from the **Brazilian E-Commerce Public Dataset by Olist**.

**Original source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data

---

## Files

| File | Description |
|---|---|
| `olist_customers_dataset.csv` | Customer IDs and location |
| `olist_geolocation_dataset.csv` | ZIP codes with lat/lng coordinates |
| `olist_order_items_dataset.csv` | Items purchased within each order |
| `olist_order_payments_dataset.csv` | Payment method and values per order |
| `olist_order_reviews_dataset.csv` | Customer review scores and comments |
| `olist_orders_dataset.csv` | Core order table — status and timestamps |
| `olist_products_dataset.csv` | Product attributes and category |
| `olist_sellers_dataset.csv` | Seller IDs and location |
| `product_category_name_translation.csv` | Portuguese category names → English |

---

## How to reproduce

These files are not committed to this repo due to size. Follow the steps below to populate this folder.

### Prerequisites
- [Git](https://git-scm.com/downloads) installed (Git Bash on Windows)
- This repo cloned locally

### Steps

**1. Sparse-clone the source repo (downloads only the Data folder)**
```bash
cd ~/Desktop
git clone --filter=blob:none --sparse https://github.com/mayank953/BigDataProjects.git temp-source
cd temp-source
git sparse-checkout set "Project-Brazillian Ecommerce/Data"
```

**2. Copy CSVs into this folder**
```bash
cp "Project-Brazillian Ecommerce/Data"/*.csv /path/to/End-To-End_BigData_Project/Data/Raw/
```
> Replace `/path/to/` with the actual path to your local clone of this repo.

**3. Clean up the temp clone**
```bash
cd ~/Desktop
rm -rf temp-source
```

Alternatively, you can download the files directly from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data) and place them in this folder.
