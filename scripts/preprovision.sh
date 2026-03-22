#!/bin/bash

# Pre-provision script for Copilot Usage Advanced Dashboard
# This script validates that all required environment variables are set
# before running `azd provision` or `azd up`.

set -e

echo ""
echo "=== Pre-Provision Validation ==="
echo ""

# Check if 'azd' command is available
if ! command -v azd &> /dev/null; then
    echo "Error: 'azd' command is not found. Please install the Azure Developer CLI."
    echo "Installation: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd"
    exit 1
fi

echo "Loading azd environment variables..."
azd_values=$(azd env get-values 2>/dev/null || true)
while IFS='=' read -r key value; do
    if [[ $key && $value ]]; then
        value="${value%\"}"
        value="${value#\"}"
        export "$key"="$value"
    fi
done <<< "$azd_values"

# -------------------------------------------------------------------------
# Validate required variables
# -------------------------------------------------------------------------
MISSING_VARS=0

if [[ -z "${GITHUB_PAT}" ]]; then
    echo ""
    echo "  ERROR: GITHUB_PAT is not set."
    echo "  This is a GitHub Personal Access Token with the following scopes:"
    echo "    - manage_billing:copilot"
    echo "    - read:enterprise"
    echo "    - read:org"
    echo "  Create a token at: https://github.com/settings/tokens"
    echo "  Then run: azd env set GITHUB_PAT <your-token>"
    MISSING_VARS=1
fi

if [[ -z "${GITHUB_ORGANIZATION_SLUGS}" ]]; then
    echo ""
    echo "  ERROR: GITHUB_ORGANIZATION_SLUGS is not set."
    echo "  This is the slug(s) of the GitHub Organization(s) you want to monitor."
    echo "  Examples:"
    echo "    Single org:    azd env set GITHUB_ORGANIZATION_SLUGS myorg"
    echo "    Multiple orgs: azd env set GITHUB_ORGANIZATION_SLUGS myorg1,myorg2"
    echo "    Standalone:    azd env set GITHUB_ORGANIZATION_SLUGS standalone:mySlug"
    MISSING_VARS=1
fi

# -------------------------------------------------------------------------
# Warn about optional-but-recommended variables
# -------------------------------------------------------------------------
if [[ -z "${GRAFANA_USERNAME}" ]]; then
    echo ""
    echo "  INFO: GRAFANA_USERNAME is not set (default: admin)."
    echo "  To set a custom username: azd env set GRAFANA_USERNAME <username>"
fi

if [[ -z "${GRAFANA_PASSWORD}" ]]; then
    echo ""
    echo "  INFO: GRAFANA_PASSWORD is not set (default: copilot)."
    echo "  To set a custom password: azd env set GRAFANA_PASSWORD <password>"
fi

# -------------------------------------------------------------------------
# Fail if required variables are missing
# -------------------------------------------------------------------------
if [[ $MISSING_VARS -ne 0 ]]; then
    echo ""
    echo "Pre-provision validation failed. Set the missing variables above and re-run 'azd up'."
    echo ""
    exit 1
fi

echo ""
echo "Pre-provision validation passed. Proceeding with provisioning..."
echo ""
