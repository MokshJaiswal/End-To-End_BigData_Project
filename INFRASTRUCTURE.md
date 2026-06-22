# Infrastructure

This document describes the cloud resources, connections, and access roles
behind the Olist end-to-end pipeline. It does **not** describe code/folder
layout — see the repo's own folder structure for that. It also does **not**
contain any secret values (passwords, keys, client secrets) — only what each
credential is, where it's used, and what kind of value it should be filled
with when recreating this project from scratch.

## 1. Architecture Overview
GitHub raw CSVs ──┬──► ADF Bronze (7 files, direct copy) ───┐

│                                          │

AWS RDS (Postgres) ┴──► ADF Bronze (olist_order_payments) ────┤

▼

ADLS Gen2 — bronze/

│

▼

Databricks Silver (PySpark)

◄── MongoDB Atlas

(product_category_name_translation,

read directly, never touches Bronze)

│

▼

ADLS Gen2 — silver/ (Parquet)

│

▼

Synapse Gold (serverless SQL views,

query Silver live — not materialized)
**Orchestration:** Airflow (`olist_pipeline` DAG) chains:
`run_bronze_ingestion` (ADF) → `run_silver_transformation` (Databricks) →
`refresh_gold_views` (Synapse).

**One-time seed (outside the recurring DAG):** a Colab notebook
(`Notebooks/Ingestion/`) pushes the static Olist CSVs into RDS Postgres
(`olist_order_payments` table) and MongoDB Atlas
(`product_category_name_translation` collection) once. These are
preconditions the pipeline depends on, not steps it re-runs — the dataset
is static, so there's nothing new to ingest on a recurring basis.

## 2. Resource Inventory

| Resource | Platform | Purpose |
|---|---|---|
| RDS PostgreSQL instance (`olist-postgres-db`, `us-east-2`) | AWS | Hosts `olist_order_payments` — the one Bronze source ADF pulls from a database instead of GitHub |
| MongoDB Atlas cluster (`Cluster0`, database `olist_db`) | MongoDB Atlas | Hosts `product_category_name_translation`, read directly by the Databricks Silver notebook |
| Storage Account `olistecommstorageaccount` | Azure | ADLS Gen2 — `olist-ecomm-data/bronze/` and `olist-ecomm-data/silver/` |
| Data Factory `project-olist-data-factory` (resource group `ecomm-olist`) | Azure | Bronze ingestion — metadata-driven copy from GitHub + one Postgres-sourced copy |
| Databricks workspace (`adb-7405606591701272`) | Azure | Silver transformation (serverless PySpark) |
| Synapse workspace `olistsynapse` | Azure | Gold layer — serverless SQL pool, views over Silver Parquet; git-integrated to `Synapse/` in this repo |
| Astro project (`Airflow/`) | Local / Astronomer | Airflow orchestration — runs via Docker/WSL2 |

## 3. Airflow Connections

These live in Airflow's metadata DB, not in git (correctly — `.env` and
`airflow_settings.yaml` are gitignored). Recreating this project means
recreating these three by hand, or via the bootstrap script described below.

| Connection ID | Type | Key fields (no values shown) |
|---|---|---|
| `databricks_default` | Databricks | Host = workspace URL; Password = Personal Access Token (PAT) |
| `azure_data_factory_default` | Azure Data Factory | Login = Service Principal Client ID; Password = Client **Secret Value** (not the Secret ID — see gotchas); Extra = `{"tenantId": "...", "subscriptionId": "...", "resource_group_name": "ecomm-olist", "factory_name": "project-olist-data-factory"}` |
| `azure_synapse_default` | Azure Synapse | Same Service Principal credentials as above; Extra = `{"tenantId": "..."}`; note the workspace dev endpoint is **not** read from this connection automatically — it must be passed explicitly as `azure_synapse_workspace_dev_endpoint` in every `AzureSynapseRunPipelineOperator` call |

## 4. RBAC

The orchestrating identity is an App Registration named **`airflow`**
(Object ID `7d4d1bfa-f5d5-4105-8749-6e6e1de93568`). It needs access granted
in **two separate, non-overlapping systems**:

- **Azure (ARM) RBAC** — the standard subscription/resource-group-level
  roles you'd assign via the Azure Portal's IAM blade. This is what governs
  Data Factory access.
- **Synapse internal RBAC** — a workspace-scoped role system that lives
  *inside* Synapse Studio (Manage → Access control), entirely separate from
  ARM RBAC. The `airflow` SP needs **two** roles here, granted separately,
  because they cover different permissions:
  - **Synapse Contributor** — general pipeline/artifact operations
  - **Synapse Credential User** — specifically grants
    `Microsoft.Synapse/workspaces/credentials/useSecret/action`. Contributor
    does **not** include this. Without it, any Synapse pipeline activity
    that authenticates via the workspace's System-Assigned Managed Identity
    (common for ADLS access) fails with `AccessControlUnauthorized`, even
    though Contributor looks like it should be enough.

## 5. Known Gotchas

Things that cost real debugging time and aren't obvious from the code alone:

- **Databricks serverless blocks `spark.conf.set()`** for `fs.azure.*` keys.
  Credentials must be passed via `.option()` on each individual read/write
  call. Secrets are pulled via `dbutils.secrets.get()` from secret scope
  `olist-scope` (keys: `storage-key`, `mongo-password`).
- **Azure App Registration secrets have two columns: Secret ID and Secret
  Value.** Only the Value is the real credential — the ID is a GUID that
  *looks* credential-shaped but isn't. Pasting the ID produces
  `AADSTS7000215: Invalid client secret provided`.
- **`AzureSynapseRunPipelineOperator` requires
  `azure_synapse_workspace_dev_endpoint`** as a direct constructor argument.
  It is not inferred from the Connection's host/extras.
- **Synapse RBAC ≠ Azure RBAC**, and Synapse Contributor specifically does
  not include `credentials/useSecret/action` — see RBAC section above.
- **Gold is views-only, not CETAS.** Views query Silver Parquet live on
  every read — there's no physical Gold storage to refresh. Re-running
  `gold.refresh_gold_views` only matters when a view's SQL *definition*
  changes, not for picking up new data.
- **Never import one DAG file from another** (e.g.
  `from dags.x import y`). A shared `DagBag()` parse (like in a pytest
  suite) can register the same `dag_id` twice this way, even though the
  live Airflow scheduler's per-file parse isolation hides the problem.
- **Synapse pipeline Script activities only ever execute their own inline
  Query text** — they cannot reference a separately saved Develop-hub SQL
  script by name. Standalone scripts left in the Develop hub are inert
  unless manually opened and run.
- **WSL2 on Windows:** disable "fast startup" — it can corrupt WSL state
  across reboots. Also cap memory explicitly in `.wslconfig`
  (`memory=6GB` on a 15GB host, for example) rather than leaving WSL2's
  default ~50%-of-host-RAM ceiling in place — under heavy Docker rebuild
  load this can starve Windows itself, not just WSL.
- **Projects under OneDrive-synced paths** can cause Docker bind-mount /
  Airflow file-watcher staleness — saved DAG changes don't always get
  picked up without a full `astro dev restart`, which is a much heavier
  fix than the problem usually warrants.
- **MongoDB Atlas:** requires `tlsCAFile=certifi.where()` in `MongoClient`,
  and `0.0.0.0/0` in Atlas Network Access for Colab/Databricks connectivity.
- **Colab secrets:** use `google.colab.userdata.get()`, not environment
  variables.
