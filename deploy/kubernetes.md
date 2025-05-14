# About

Application can be deployed to a kubernetes cluster

## Architecture diagram

![](/image/aks.drawio.png)

## Technology stack

Dependent technology stack:

- Kubernetes (pods, jobs, services, persistent storage, ingress)
- Elasticsearch
- Grafana
- Python3

## Deployment manifest

Available [here](aks-deployment.yml).

## Deploy in Kubernetes
This document describes how to deploy the application in Kubernetes.

Variables used in the manifest:
 - `__GITHUB_PAT__`
 - `__GRAFANA_USERNAME__`
 - `__GRAFANA_PASSWORD__`
 - `__ORGANIZATION_SLUGS__`

Replacement can be done using `envsubst` tool:

```sh
export __GITHUB_PAT__=your_pat
export __GRAFANA_USERNAME__=your_user
export __GRAFANA_PASSWORD__=your_pass
export __ORGANIZATION_SLUGS__=your_orgs

envsubst < deploy/aks-deployment.yml | kubectl apply -f -
```

### Deployment in Azure Kubernetes Service - AKS

If you're using Azure Kubernetes Service - AKS:
1. Enable [App Routing](https://learn.microsoft.com/en-us/azure/aks/app-routing)
2. Update variables.
3. Apply the manifest in your cluster.

### Deployment in non-Azure Kubernetes cluster

1. Update PVC (Persitent Volume Claim) to one supported in your cluster
2. Update Ingress
3. Update variables.
4. Apply the manifest in your cluster.