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

### Troubleshooting Grafana "database is locked" Error

Grafana database can lock which can cause container to fail, see [Grafana, SQLite, and database is locked](https://opsverse.io/2022/12/15/grafana-sqlite-and-database-is-locked/)

Use following Job to unlock the database.

```yaml
---
apiVersion: batch/v1
kind: Job
metadata:
  name: fix-grafana-once
spec:
  template:
    spec:
      containers:
        - name: fix-grafana
          image: keinos/sqlite3
          imagePullPolicy: IfNotPresent
          command:
          - "/bin/sh"
          - "-c"
          - "/usr/bin/sqlite3 /var/lib/grafana/grafana.db '.clone /var/lib/grafana/grafana.db.clone'; mv /var/lib/grafana/grafana.db.clone /var/lib/grafana/grafana.db; chmod a+w /var/lib/grafana/grafana.db"
          volumeMounts:
            - name: grafana-data
              mountPath: /var/lib/grafana
              subPath: grafana
          securityContext:
            runAsUser: 0
          resources:
            requests:
              cpu: "0.25"
              memory: "256Mi"
            limits:
              cpu: "0.5"
              memory: "512Mi"
      restartPolicy: Never
      volumes:
        - name: grafana-data
          persistentVolumeClaim:
            claimName: shared-pvc
```

Force restart grafana container after to re-create.