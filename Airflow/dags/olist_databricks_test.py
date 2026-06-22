from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime

@dag(
    dag_id="olist_databricks_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,          # manual trigger only — no automatic runs
    catchup=False,
    default_args={"retries": 2},
    tags=["olist", "test"],
)
def olist_databricks_test():

    run_silver = DatabricksRunNowOperator(
        task_id="run_silver_transformation",
        databricks_conn_id="databricks_default",
        job_id=641247821334369,
    )

    run_silver

olist_databricks_test()