
# Overview

This demo shows how to limit the [Azure Container Apps easy authentication](https://learn.microsoft.com/en-us/azure/app-service/scenario-secure-app-authentication-app-service?tabs=workforce-configuration)
too a list of predefined tenants when configured for multi tenant authentication.

By default the app allows the currently deployed tenant and takes the list of permitted tenants from "AUTH_TENANT_IDS" environment variable.