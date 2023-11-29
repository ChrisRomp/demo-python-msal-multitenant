import os

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient

def main():
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TENANT_ID = os.getenv("TENANT_ID")
    SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")

    print("Authenticating...")
    resource_client = ResourceManagementClient(
        credential=ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        ),
        subscription_id=SUBSCRIPTION_ID,
    )

    print("Getting resource groups...")
    resource_groups = resource_client.resource_groups.list()

    for group in resource_groups:
        print("Group: %s" % group.name)

if __name__ == "__main__":
    main()
