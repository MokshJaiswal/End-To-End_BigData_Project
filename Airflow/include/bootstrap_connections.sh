#!/bin/bash
set -e

required_vars=(
  DATABRICKS_HOST DATABRICKS_TOKEN
  AZURE_SP_CLIENT_ID AZURE_SP_CLIENT_SECRET
  AZURE_TENANT_ID AZURE_SUBSCRIPTION_ID
  SYNAPSE_DEV_ENDPOINT
)
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Missing required env var: $var"
    exit 1
  fi
done

airflow connections delete databricks_default 2>/dev/null || true
airflow connections add 'databricks_default' \
  --conn-type 'databricks' \
  --conn-host "$DATABRICKS_HOST" \
  --conn-password "$DATABRICKS_TOKEN"

airflow connections delete azure_data_factory_default 2>/dev/null || true
airflow connections add 'azure_data_factory_default' \
  --conn-type 'azure_data_factory' \
  --conn-login "$AZURE_SP_CLIENT_ID" \
  --conn-password "$AZURE_SP_CLIENT_SECRET" \
  --conn-extra "{\"tenantId\": \"$AZURE_TENANT_ID\", \"subscriptionId\": \"$AZURE_SUBSCRIPTION_ID\"}"

airflow connections delete azure_synapse_default 2>/dev/null || true
airflow connections add 'azure_synapse_default' \
  --conn-type 'azure_synapse' \
  --conn-host "$SYNAPSE_DEV_ENDPOINT" \
  --conn-login "$AZURE_SP_CLIENT_ID" \
  --conn-password "$AZURE_SP_CLIENT_SECRET" \
  --conn-extra "{\"tenantId\": \"$AZURE_TENANT_ID\", \"subscriptionId\": \"$AZURE_SUBSCRIPTION_ID\"}"

echo "All three connections recreated."