#!/bin/bash

# Run `az login` first as a user with appropriate permissions.

# Load env
source $CODESPACE_VSCODE_FOLDER/.env

# Get Subscription ID
echo "Getting Subscription ID..."
SUB_ID=$(az account show --query id -o tsv)

# Get role assignment
echo "Getting role assignment..."
RA=$(az role assignment list --role "Reader" --scope "/subscriptions/$SUB_ID" --query "[?principalName == '$CLIENT_ID'] | [0]")
RA_ID=$(echo $RA | jq -r '.id')
SP_ID=$(echo $RA | jq -r '.principalId')

# Delete role assignment
echo "Deleting role assignment..."
az role assignment delete --ids $RA_ID

# Delete service principal
echo "Deleting service principal..."
az ad sp delete --id $SP_ID
