from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.microsoft.azure.operators.data_factory import AzureDataFactoryRunPipelineOperator
from airflow.providers.microsoft.azure.operators.synapse import AzureSynapseRunPipelineOperator
from datetime import datetime, timedelta

@dag(
    dag_id="olist_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["olist", "pipeline"],
)
def olist_pipeline():

    run_bronze_ingestion = AzureDataFactoryRunPipelineOperator(
        task_id="run_bronze_ingestion",
        azure_data_factory_conn_id="azure_data_factory_default",
        factory_name="project-olist-data-factory",
        resource_group_name="ecomm-olist",
        pipeline_name="olist-pipeline",
    )

    run_silver = DatabricksRunNowOperator(
        task_id="run_silver_transformation",
        databricks_conn_id="databricks_default",
        job_id=641247821334369,
    )

    refresh_gold = AzureSynapseRunPipelineOperator(
        task_id="refresh_gold_views",
        azure_synapse_conn_id="azure_synapse_default",
        pipeline_name="refresh-gold-views",
        azure_synapse_workspace_dev_endpoint="https://olistsynapse.dev.azuresynapse.net",
    )

    run_bronze_ingestion >> run_silver >> refresh_gold

olist_pipeline()