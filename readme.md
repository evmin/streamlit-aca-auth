
# Overview

Demo of an agentic debate - provide a topic and WRITER, CRITIC and other agents will generate a blogpost through debate.

The application is implemented as a streamlit app deployed in Azure. It canb also be executed locally. 

## Prerequisites

- Install python@3.12
- Install [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- Install [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
- On Windows install the (Platform PowerShell)[https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4]. **OBS!** It is MUST be installed - it is NOT a Windows PowerShell.
- Login to your tentnant with Azure CLI `az login`

## Deploy the app to Azure

```sh
azd env set AZURE_LOCATION 'swedencentral'
azd up
```

**OBS!** 'Deploying services (azd deploy)' stage can take up to 10 min.

## Local execution

Once infrastructure is available, the configuration is saved in the azd environments .env file. This file is read by load_dotenv in the app:

```.azure/<env_name>/.env```

If azd has not been run, the abovementioned file would not exist and the application will try to run vanilla load_dotenv looking for the standard .env file.

## ENV Variables

The env variables required to run the application:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_KEY
- AZURE_OPENAI_DEPLOYMENT_NAME

# Run

```sh
cd src/streamlit
pip install -r requirements.txt
streamlit run app.py
```