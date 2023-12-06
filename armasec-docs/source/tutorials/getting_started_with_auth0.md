# Getting started with Auth0

This step-by-step walk-through will show you how to get an Auth0 account set up for use with the
minimal example.

You will need:

* Python 3.8+ installed


## Installing python packages

The first thing you will need to do is to install some neeeded python dependencies. In
order to run the example API, you will need the the `uvicorn` package installed. You
will also be using the Armasec CLI to verify that you can log in. For this, you will
need the `armasec` package with the `cli` extra. For this tutorial, it will be best to
work in a new virtual environment. To bootstrap it, run the following commands:

```bash
python -m venv env
source env/bin/activate
pip install uvicorn armasec[cli]
```

When the commands finish running, your environment will be ready to complete this guide.


## Create Auth0 account tenant

Navigate to [Auth0's homepage](https://auth0.com), and click `Sign Up`.

Create a new account (if you don't already have one). It doesn't really matter how you
choose to sign up, but it may be easiest to use your google or github account.

The first step will be to select your tenant domain. This tutorial will be using
"auth0-armasec-tutorial". However, you will need to select your own domain name as this
cannot be re-used by other people. Choose your region and click `Create Account`.

![Select tenant domain](../images/auth0-create-domain.png){: .framed-image}
_Select tenant domain_

The full domain for that will be used later is "auth0-armasec-tutorial.us.auth0.com".
Throughout the tutorial, remember to substitute your own chosen domain for this value.


## Add your API application

This step will guide you as you set up the Auth0 api endpoints that Auth0 will use to
authenticate your users.

First, you need to create a new API. On the left navbar, click `Applications` and then
select `APIs`.

![Navigate to Applications -> APIs](../images/auth0-navigate-apis.png){: .framed-image}
_Navigate to Applications > APIs_


Once there, click the `Create API` button

![Create an API](../images/auth0-create-api.png){: .framed-image}
_Create an API_



Fill out the form. The Name you choose doesn't matter, but will help you find your API
in the Auth0 UI going forward.  The "Identifier" will be the "Audience" claim that is
used in the auth tokens. Whatever value you use here, make sure to substitute it for
"Audience" throughout this tutorial. Leave the "Signing Algorithm" as "RS256".
Armasec also supports HS256, but it is not preferred. Finally, click `Create`.

![API Creation Form](../images/auth0-api-form.png){: .framed-image}
_API Creation Form_


Next, we will need to enable RBAC for this API. You can find this on the Settings tab.

![API Settings](../images/auth0-api-settings.png){: .framed-image}
_API Settings_


Scroll down to the "RBAC Settings". Activate `Enable RBAC`. Also enable
`Add Permissions in the Access Token` to include permissions scopes to your users'
access tokens. Click `Save`

![RBAC Enabled](../images/auth0-api-rbac.png){: .framed-image}
_RBAC Enabled_


Next, we will add the permission scopes to tokens issued by this API. Click on the
`Permissions` tab and add the "read:stuff" permission.

![Add permissions](../images/auth0-add-permissions.png){: .framed-image}
_Add permissions_



## Set up a client

Next, you will need to set up a client that is configured for the tutorial. To do this,
click on `Applications` on the left navbar and then click the `Applications` link
beneath it.

![Navigate to Applications](../images/auth0-navigate-applications.png){: .framed-image}
_Navigate to Applications_


Click the `Create Application` button.

![Create Application](../images/auth0-create-application.png){: .framed-image}
_Create Application_


A form will appear. It doesn't matter what you name the application. Select a "Native"
application type and click the `Create` button.


![Application Form](../images/auth0-application-form.png){: .framed-image}
_Application Form_

Next, we will need to enable device code authorization this API. You can find this on
the Settings tab.


![Application Settings](../images/auth0-application-settings.png){: .framed-image}
_Application Settings_


Scroll down to the bottom of the settings page to find the "Advanced Settings". Expand
the block and click on the `Grant Types` tab. In this tab, enable the "Device Code"
option. Click "Save Changes" to finish.

![Enable Device Code](../images/auth0-device-code.png){: .framed-image}
_Enable Device Code_


You will use the "Client ID" for this application later in the tutorial, so be sure
to note it.


## Set up a user

Next, you will need to create a user to log in with. Click on `User Management` on the
left navbar and then click the `Users` link beneath it.

![Navigate Users](../images/auth0-navigate-users.png){: .framed-image}
_Navigate Users_

Click on the `Create User` button to start the process.

![Create User](../images/auth0-create-user.png){: .framed-image}
_Create User_


Fill out the form. You will use the provided email to sign in; this does not have to be
a real email address. Chose a password (Auth0 requires a semi-strong password, so make
sure to make note of your choice. Finally, click `Create` to create the user.

![User Form](../images/auth0-user-form.png){: .framed-image}
_User Form_


Finally, you need to add the permissions for your user. Click on the "Permissions" tab,
click `Assign Permissions`.

![Assign Permissions](../images/auth0-assign-permissions.png){: .framed-image}
_Assign Permissions_


A form will open. Select the API created earlier in the tutorial. Enable the
`read:stuff` permission, and then click `Add Permissions`.

![Select Permissions](../images/auth0-select-permissions.png){: .framed-image}
_Select Permissions_


Your user should now be ready to sign into the application.


## Start up the example app

```python title="example.py" linenums="1"
from armasec import Armasec
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(
    domain="armasec-tutorial.us.auth0.com",
    audience="https://armasec-tutorial.com",
    debug_logger=print,
    debug_exceptions=True,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
```

Also not that we need to add a `payload_claim_mapping` because Keycloak does not provide
a permissions claim at the top level. This mapping copies the roles found at
`resource_access.armasec_tutorial.roles` to a top-level attribute of the token payload
called permissions.

Copy the `example.py` app to a local source file called "example.py".

Start it up with uvicorn:

```bash
python -m uvicorn --host 0.0.0.0 --port 5000 example:app
```

Once it is up and running, hit `<ctrl-z>` and type the command `bg` to put the uvicorn
process into the background. You should make sure to kill the process when you complete
the tutorial.


## Login via Armasec CLI

Next, you will log in using the Armasec CLI to get an API token to access your example
API. Before you log in, however, you will need to configure the Armasec CLI to connect
to the Auth0 server. Type the following command to configure the CLI (remember to
substitute your domain and client-id):

```bash
armasec set-config --provider=AUTH0 --domain=auth0-armasec-tutorial.us.auth0.com --audience=https://auth0-api --client-id=VByjtzLPOglJemX4SBncHudJedZ6NVoo
```

Now you should be ready to log in. In your terminal, type the following command to start
the process:

```bash
armasec login
```

The CLI will show a box prompting you to complete the login process in a browser:

```
╭─────────────────────────────────────────── Waiting for login ───────────────────────────────────────────╮
│                                                                                                         │
│   To complete login, please open the following link in a browser:                                       │
│                                                                                                         │
│     https://auth0-armasec-tutorial.us.auth0.com/activate?user_code=RRRR-PZFG                            │
│                                                                                                         │
│   Waiting up to 5.0 minutes for you to complete the process...                                          │
│                                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Waiting for web login... ╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   2% 0:04:55
```

Open the provided link in the browser and log in using the user that you
created.

![Log in](../images/auth0-log-in.png){: .framed-image}
_Log in_

You will then be prompted with a question asking if you want to grant access. Click
"Yes" to complete the log in process. The browser will show a message confirming that
you are now logged in. You may close that browser tab.

Notice in the terminal, a message is now printed showing that your user was logged in:

```bash
╭────────────────────────────────────────────── Logged in! ───────────────────────────────────────────────╮
│                                                                                                         │
│   User was logged in with email 'None'                                                                  │
│                                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Note that the email was listed as 'None'. This is because Auth0 by default does not
include the user's email in the auth token.


## Fetch the auth token

Next, you will use the Armasec CLI to fetch the token for the logged in user. To do
this, you will use the `show-token` subcommand. In a terminal, type (the prefix flag
includes the "Bearer" type indicator for the token):

```bash
armasec show-token --prefix
```

The Armasec CLI will print out a box showing the auth token for your user:

```bash
╭───────────────────────────────────────────── Access Token ──────────────────────────────────────────────╮
│                                                                                                         │
│ Bearer                                                                                                  │
│ eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjQ0d2UwS21haXlZMjlmRVh4OWM5MCJ9.eyJpc3MiOiJodHRwczovL2F1dG │
│ gwLWFybWFzZWMtdHV0b3JpYWwudXMuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDY1NjhlYmZhODlkNzM4ZTIyNThkZGFkZSIsImF1Z │
│ CI6Imh0dHBzOi8vYXV0aDAtYXBpIiwiaWF0IjoxNzAxMzc2MTY3LCJleHAiOjE3MDE0NjI1NjcsImF6cCI6IlZCeWp0ekxQT2dsSmVt │
│ WDRTQm5jSHVkSmVkWjZOVm9vIiwicGVybWlzc2lvbnMiOlsicmVhZDpzdHVmZiJdfQ.KFKVJNcUDuCN89nNV6D8WwMrg9IV7FpCufem │
│ LJqGlYXwm4DpPxFGbRuN4FhqKKxOUbr4hleox9pxSk8nqrsVHD0d9Y4EqARM1ihRIzQCVknZt9r6yx_JLwS9NKFwb-AaGiJERbwKxa1 │
│ fvTO3aX6dB4ecRtPFduMfwaokseyGq-LhVRnyb9eXGML_XswnKJ9FKcKXyvP794qRv13zmu05pLMSjcwStf_nLFKe5cYyCui8rOLCwe │
│ qRwZEKYSb4l4v0ke9QhA3bKPQxBvQe3R7m5Zwl6wXTN3VJ7Smv4tLtsJCTIDInOO-glTbs2NRcl_Uvbnl7AtcugsaDwdlIaX3CTg    │
│                                                                                                         │
╰──────────────────────────────── The output was copied to your clipboard ────────────────────────────────╯
```

If your terminal supports it, the token will be automatically copied into your clipboard.
However, if you need to manually copy it, you can run the above command again with the
`--plain` flag to print the token without formatting:

```bash
Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjQ0d2UwS21haXlZMjlmRVh4OWM5MCJ9.eyJpc3MiOiJodHRwczovL2F1dGgwLWFybWFzZWMtdHV0b3JpYWwudXMuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDY1NjhlYmZhODlkNzM4ZTIyNThkZGFkZSIsImF1ZCI6Imh0dHBzOi8vYXV0aDAtYXBpIiwiaWF0IjoxNzAxMzc2MTY3LCJleHAiOjE3MDE0NjI1NjcsImF6cCI6IlZCeWp0ekxQT2dsSmVtWDRTQm5jSHVkSmVkWjZOVm9vIiwicGVybWlzc2lvbnMiOlsicmVhZDpzdHVmZiJdfQ.KFKVJNcUDuCN89nNV6D8WwMrg9IV7FpCufemLJqGlYXwm4DpPxFGbRuN4FhqKKxOUbr4hleox9pxSk8nqrsVHD0d9Y4EqARM1ihRIzQCVknZt9r6yx_JLwS9NKFwb-AaGiJERbwKxa1fvTO3aX6dB4ecRtPFduMfwaokseyGq-LhVRnyb9eXGML_XswnKJ9FKcKXyvP794qRv13zmu05pLMSjcwStf_nLFKe5cYyCui8rOLCweqRwZEKYSb4l4v0ke9QhA3bKPQxBvQe3R7m5Zwl6wXTN3VJ7Smv4tLtsJCTIDInOO-glTbs2NRcl_Uvbnl7AtcugsaDwdlIaX3CTg
```

Keep the token close at hand; you will be using it shortly to access your API endpoint.


## Try it out

Open a browser to [localhost:8000/docs](http://localhost:8000/docs){:target="_blank"}

This will show you the auto-generated swagger docs for the example API app. Click on the
`Authorize` button to add the token you copied to the clipboard in the header of requests to the
API.


![Authorize](../images/keycloak-authorize.png){: .framed-image}
_Authorize_

First, paste the token (including the "Bearer" prefix) from the clipboard into the form
and click the `Authorize` button in the dialog, click `Close` to dismiss the dialog.
Now, all subsequent calls to the API will include a header that looks like:

```json
{
  "Authorization": "Bearer eyJhbGciOi..."
}
```


Now, expand the "GET" REST operation on the `/stuff` endpoint and click `Try it out`.

![Try it out](../images/keycloak-try-it-out.png){: .framed-image}
_Try it out_


Finally, click `Execute` to issue the request to the API.

![Execute](../images/keycloak-execute.png){: .framed-image}
_Execute_


You should see a response that includes a 200 status code and a response body that includes:

```json
{
  "message": "Successfully authenticated"
}
```

Congratulations! You are now using Armasec and Auth0 to authorize requests to your API.


## Tinker

Now, there are a few things you can do to check out how things work. Try the following things:

* Remove the "read:stuff" role from your user and try another request
* Try a request without being authorized in swagger
* Try making requests using `curl` or the `httpx` library in IPython


## Send feedback

If the above tutorial didn't work as expected, a step needs better clarification, or you have some
questions about it, please create an issue on
[Armasec's GitHub's issues](https://github.com/omnivector-solutions/armasec/issues>).
