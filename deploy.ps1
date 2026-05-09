# deploy.ps1
# Deploys all MCP files to Ableton and syncs server files to all active Claude Code worktrees.
#
# Run this after making any changes to:
#   - AbletonMCPLocal/*.py  (remote script - requires Ableton restart after)
#   - ableton/*.py          (MCP server files)
#   - server_arrangement.py (MCP server entry point)
#
# Usage: .\deploy.ps1
#        .\deploy.ps1 -SkipAbleton    (skip Ableton deploy, only sync worktrees)
#        .\deploy.ps1 -SkipWorktrees  (skip worktree sync, only deploy to Ableton)

param(
    [switch]$SkipAbleton,
    [switch]$SkipWorktrees
)

$ProjectRoot   = $PSScriptRoot
$AbletonDeploy = "$env:USERPROFILE\Documents\Ableton\User Library\Remote Scripts\AbletonMCPLocal"

# ── 1. Deploy remote script to Ableton ──────────────────────────────────────
if (-not $SkipAbleton) {
    Write-Host "`n[1/2] Deploying remote script to Ableton..." -ForegroundColor Cyan

    $pycache = Join-Path $AbletonDeploy "__pycache__"
    if (Test-Path $pycache) {
        Remove-Item $pycache -Recurse -Force
        Write-Host "  Deleted __pycache__"
    }

    Get-ChildItem "$ProjectRoot\AbletonMCPLocal\*.py" | ForEach-Object {
        Copy-Item $_.FullName $AbletonDeploy -Force
        Write-Host "  Copied $($_.Name)"
    }

    Write-Host "  Remote script deployed. Restart Ableton to pick up changes." -ForegroundColor Green
}

# ── 2. Sync server files to all active worktrees ────────────────────────────
if (-not $SkipWorktrees) {
    Write-Host "`n[2/2] Syncing server files to Claude Code worktrees..." -ForegroundColor Cyan

    $worktreesDir = "$ProjectRoot\.claude\worktrees"
    if (-not (Test-Path $worktreesDir)) {
        Write-Host "  No worktrees directory found - nothing to sync." -ForegroundColor Yellow
    } else {
        $worktrees = Get-ChildItem $worktreesDir -Directory
        if ($worktrees.Count -eq 0) {
            Write-Host "  No active worktrees found." -ForegroundColor Yellow
        } else {
            foreach ($wt in $worktrees) {
                Write-Host "  Worktree: $($wt.Name)"

                # Sync ableton/ package files
                $wtAbleton = Join-Path $wt.FullName "ableton"
                if (Test-Path $wtAbleton) {
                    Get-ChildItem "$ProjectRoot\ableton\*.py" | ForEach-Object {
                        Copy-Item $_.FullName $wtAbleton -Force
                        Write-Host "    ableton\$($_.Name)"
                    }
                }

                # Sync server entry point
                $wtServer = Join-Path $wt.FullName "server_arrangement.py"
                if (Test-Path $wtServer) {
                    Copy-Item "$ProjectRoot\server_arrangement.py" $wt.FullName -Force
                    Write-Host "    server_arrangement.py"
                }
            }
            Write-Host "  Worktrees synced." -ForegroundColor Green
        }
    }
}

Write-Host "`nDone.`n" -ForegroundColor Green
