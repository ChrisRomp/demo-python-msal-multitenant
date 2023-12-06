import msal
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import logging
import uuid

import app_config

__version__ = "0.8.1"  # The version of this sample, for troubleshooting purpose

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# # If you want to enable debug (verbose) requests output:
# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1
# logging.basicConfig()
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

arm_auth = msal.ConfidentialClientApplication(
    app.config["CLIENT_ID"],
    authority=app.config["AUTHORITY"],
    client_credential=app.config["CLIENT_SECRET"],
)
arm_auth_scopes = ["https://management.azure.com/user_impersonation"]
arm_auth_result = {}
sp_object_id = ""

# Allows for changing token scopes
def refresh_token(scopes):
    # TODO: Validate existing token scope and expiration before refreshing

    global arm_auth_result
    result = arm_auth.acquire_token_by_refresh_token(
        arm_auth_result["refresh_token"],
        scopes=scopes,
    )
    arm_auth_result = result

@app.route("/auth")
def auth():
    redirect_uri = arm_auth.get_authorization_request_url(
        scopes=[".default"],
        redirect_uri=url_for("process_auth", _external=True),
        state="12345" # don't do this in prod
    )
    return redirect(redirect_uri)

@app.route("/processAuth")
def process_auth():
    global arm_auth_result
    arm_auth_result = arm_auth.acquire_token_by_authorization_code(
        request.args["code"],
        scopes=arm_auth_scopes,
        redirect_uri=url_for("process_auth", _external=True),
    )
    return render_template('display.html', result=arm_auth_result)

@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    return render_template('display.html', result={})

def get_subscriptions():
    refresh_token(["https://management.azure.com/user_impersonation"])
    token = arm_auth_result
    if "error" in token:
        return redirect(url_for("auth"))
    # Use access token to call downstream api
    api_result = requests.get(
        "https://management.azure.com/subscriptions?api-version=2022-12-01",
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    )
    return api_result

@app.route("/get_subscriptions")
def call_azure_api():
    api_result = get_subscriptions().json()
    return render_template('display.html', result=api_result)

@app.route("/get_sp_object_id")
def get_sp_object_id():
    # Get the object ID of the service principal
    refresh_token(["https://graph.microsoft.com/.default"])
    token = arm_auth_result
    if "error" in token:
        return redirect(url_for("auth"))
    api_result = requests.get(
        "https://graph.microsoft.com/v1.0/servicePrincipals?$filter=appId eq '" + app.config["CLIENT_ID"] + "'",
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    ).json()
    global sp_object_id
    sp_object_id = api_result["value"][0]["id"]
    return render_template('display.html', result=api_result)

@app.route("/grant")
def grant_default():
    sub = get_subscriptions()
    sub_id = sub.json()["value"][0]["subscriptionId"]
    return redirect(url_for("grant", subscriptionId=sub_id))

@app.route("/grant/<subscriptionId>")
def grant(subscriptionId):
    refresh_token(["https://management.azure.com/user_impersonation"])
    token = arm_auth_result
    if "error" in token:
        return redirect(url_for("index"))

    assignment_guid = str(uuid.uuid4()) #new guid
    role_id = "acdd72a7-3385-48ef-bd42-f606fba81ae7" # Reader
    api_result = requests.put(
        "https://management.azure.com/subscriptions/" + subscriptionId + "/providers/Microsoft.Authorization/roleAssignments/" + assignment_guid + "?api-version=2022-04-01",
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
        json={
            "properties": {
                "roleDefinitionId": "/subscriptions/" + subscriptionId + "/providers/Microsoft.Authorization/roleDefinitions/" + role_id,
                "principalId": sp_object_id,
                "principalType": "ServicePrincipal"
            }
        }
    ).json()
    return render_template('display.html', result=api_result)

if __name__ == "__main__":
    app.run()
