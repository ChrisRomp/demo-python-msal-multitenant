# demo-python-msal-multitenant

Example of using Entra ID (formerly Azure AD) authentication to grant an application access to another tenant.

The [src/web](src/web) directory is a Python/Flask application which allows a user tenant to grant access for the application to their tenant, and select a subscription to grant the Azure Reader RBAC role to the application.

The [src/svc](src/svc) directory is a Python application that will access the user's tenant as the application an enumerate objects in the subscription.

Within the Azure directory there will exist an App Registration in the source tenant as well as an Enterprise Application.

In the user tenant's directory there will only exist the Enterprise Application, aka Service Principal. All of the authentication secrets are managed in the source tenant.
