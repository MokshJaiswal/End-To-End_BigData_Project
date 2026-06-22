from airflow.decorators import dag
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from datetime import datetime

@dag(
    dag_id="olist_adf_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args={"retries": 2},
    tags=["olist", "test"],
)
def olist_adf_test():

    run_bronze_ingestion = AzureDataFactoryRunPipelineOperator(
        task_id="run_bronze_ingestion",
        azure_data_factory_conn_id="azure_data_factory_default",
        factory_name="project-olist-data-factory",
        resource_group_name="ecomm-olist",
        pipeline_name="olist-pipeline",
    )

    run_bronze_ingestion

olist_adf_test()