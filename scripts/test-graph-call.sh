#!/bin/bash

source ../.env

# Log in to Azure as service principal
az login --service-principal -t $TENANT_ID -u $CLIENT_ID -p $CLIENT_SECRET

# This will fail because the SP does not have the application permission for Application.Read.All.
# It only has delegated permissions for when acting on behalf of a signed-in user.
az rest --uri https://graph.microsoft.com/v1.0/applications
