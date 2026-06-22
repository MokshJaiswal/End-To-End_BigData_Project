from airflow.decorators import dag
from airflow.providers.microsoft.azure.operators.synapse import AzureSynapseRunPipelineOperator
from datetime import datetime


@dag(
    dag_id="olist_synapse_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args={"retries": 2},
    tags=["olist", "test"],
)
def olist_synapse_test():

    refresh_gold = AzureSynapseRunPipelineOperator(
        task_id="refresh_gold_views",
        azure_synapse_conn_id="azure_synapse_default",
        pipeline_name="refresh-gold-views",
        azure_synapse_workspace_dev_endpoint="https://olistsynapse.dev.azuresynapse.net",
)

    refresh_gold

olist_synapse_test()