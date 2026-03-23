# Pre-provision script for Copilot Usage Advanced Dashboard
# This script validates that all required environment variables are set
# before running `azd provision` or `azd up`.

Write-Host ""
Write-Host "=== Pre-Provision Validation ===" -ForegroundColor Cyan
Write-Host ""

# Check if 'azd' command is available
if (-not (Get-Command "azd" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: 'azd' command is not found. Please install the Azure Developer CLI." -ForegroundColor Red
    Write-Host "Installation: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd" -ForegroundColor Yellow
    exit 1
}

Write-Host "Loading azd environment variables..." -ForegroundColor Green

$azdValues = azd env get-values 2>$null
if ($azdValues) {
    foreach ($line in $azdValues) {
        if ($line -match "([^=]+)=(.*)") {
            $key = $matches[1]
            $value = $matches[2] -replace '^"|"$'
            Set-Item -Path "Env:$key" -Value $value
        }
    }
}

# -------------------------------------------------------------------------
# Validate required variables
# -------------------------------------------------------------------------
$missingVars = $false

if (-not $env:GITHUB_PAT) {
    Write-Host ""
    Write-Host "  ERROR: GITHUB_PAT is not set." -ForegroundColor Red
    Write-Host "  This is a GitHub Personal Access Token with the following scopes:" -ForegroundColor Yellow
    Write-Host "    - manage_billing:copilot" -ForegroundColor Yellow
    Write-Host "    - read:enterprise" -ForegroundColor Yellow
    Write-Host "    - read:org" -ForegroundColor Yellow
    Write-Host "  Create a token at: https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "  Then run: azd env set GITHUB_PAT <your-token>" -ForegroundColor Yellow
    $missingVars = $true
}

if (-not $env:GITHUB_ORGANIZATION_SLUGS) {
    Write-Host ""
    Write-Host "  ERROR: GITHUB_ORGANIZATION_SLUGS is not set." -ForegroundColor Red
    Write-Host "  This is the slug(s) of the GitHub Organization(s) you want to monitor." -ForegroundColor Yellow
    Write-Host "  Examples:" -ForegroundColor Yellow
    Write-Host "    Single org:    azd env set GITHUB_ORGANIZATION_SLUGS myorg" -ForegroundColor Yellow
    Write-Host "    Multiple orgs: azd env set GITHUB_ORGANIZATION_SLUGS myorg1,myorg2" -ForegroundColor Yellow
    Write-Host "    Standalone:    azd env set GITHUB_ORGANIZATION_SLUGS standalone:mySlug" -ForegroundColor Yellow
    $missingVars = $true
}

# -------------------------------------------------------------------------
# Warn about optional-but-recommended variables
# -------------------------------------------------------------------------
if (-not $env:GRAFANA_USERNAME) {
    Write-Host ""
    Write-Host "  INFO: GRAFANA_USERNAME is not set (default: admin)." -ForegroundColor DarkYellow
    Write-Host "  To set a custom username: azd env set GRAFANA_USERNAME <username>" -ForegroundColor DarkYellow
}

if (-not $env:GRAFANA_PASSWORD) {
    Write-Host ""
    Write-Host "  INFO: GRAFANA_PASSWORD is not set (default: copilot)." -ForegroundColor DarkYellow
    Write-Host "  To set a custom password: azd env set GRAFANA_PASSWORD <password>" -ForegroundColor DarkYellow
}

# -------------------------------------------------------------------------
# Fail if required variables are missing
# -------------------------------------------------------------------------
if ($missingVars) {
    Write-Host ""
    Write-Host "Pre-provision validation failed. Set the missing variables above and re-run 'azd up'." -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Pre-provision validation passed. Proceeding with provisioning..." -ForegroundColor Green
Write-Host ""
