# Multi-agent project bootstrap (PowerShell)
# Phase 1.4 minimal implementation: single-clone bootstrap for example projects.
# Phase 3 will extend to full N-clone scaffold via cookiecutter post-gen hook.

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,
    [string]$Agents = "core,data",
    [string]$RitualPhrase = "Acknowledged"
)

$ErrorActionPreference = "Stop"

Write-Host "[bootstrap] Project root: $ProjectRoot"
Write-Host "[bootstrap] Agents:       $Agents"
Write-Host "[bootstrap] Ritual phrase: $RitualPhrase"

if (-not (Test-Path $ProjectRoot)) {
    New-Item -ItemType Directory -Path $ProjectRoot | Out-Null
    Write-Host "[bootstrap] Created project root."
}

# Initialize git in the project root if not already a repo.
if (-not (Test-Path "$ProjectRoot/.git")) {
    git -C $ProjectRoot init -b master | Out-Null
    Write-Host "[bootstrap] Initialized git repo."
}

# Run governance-core install with overrides
$projectName = Split-Path $ProjectRoot -Leaf
$overrides = @{
    project_name = $projectName
    ritual_phrase = $RitualPhrase
    install_root = (Split-Path $ProjectRoot -Parent)
    shared_state_root = (Join-Path (Split-Path $ProjectRoot -Parent) "shared_state/$projectName")
}
$agentsList = $Agents -split ',' | ForEach-Object { $_.Trim() }
$agentsConfig = @()
foreach ($a in $agentsList) {
    $branch = if ($a -eq 'core') { 'master' } else { "feature/$a" }
    $agentsConfig += @{ name = $a; branch = $branch; clone_dir = "agent-$a" }
}
$overrides['agents'] = $agentsConfig
$overrides['core_agent_name'] = $agentsList[0]

$overridesJson = $overrides | ConvertTo-Json -Compress -Depth 5
Write-Host "[bootstrap] Calling governance-core install..."
governance-core install --project-root $ProjectRoot --config-overrides $overridesJson --force

# Initial commit
$status = git -C $ProjectRoot status --porcelain
if ($status) {
    git -C $ProjectRoot add -A | Out-Null
    git -C $ProjectRoot commit -m "chore: bootstrap $projectName via multi-agent-template + governance-core" | Out-Null
    Write-Host "[bootstrap] Initial commit created."
}

Write-Host "[bootstrap] Done. Verify with:"
Write-Host "  governance-core doctor --project-root $ProjectRoot"
