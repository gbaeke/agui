# PowerShell wrapper to run dev.sh with proper setup
# Usage: ./dev.ps1

param(
    [switch]$NoFix = $false  # Skip line ending fix if already done
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$devScript = Join-Path $scriptPath "src\dev.sh"

Write-Host "🚀 Starting AG-UI Development Server..." -ForegroundColor Cyan
Write-Host ""

if (-not $NoFix) {
    Write-Host "📝 Fixing line endings..." -ForegroundColor Yellow
    wsl bash -c "perl -pi -e 's/\r\n/\n/g' /mnt/c/temp/AI/AGUI/agui/src/dev.sh && chmod +x /mnt/c/temp/AI/AGUI/agui/src/dev.sh"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to fix line endings" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Line endings fixed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "  📱 Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  🔌 Runtime:  http://localhost:3001" -ForegroundColor Green
Write-Host "  🐍 Backend:  http://localhost:8888" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Free up commonly used dev ports if already occupied
function Kill-Port {
    param([int]$Port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = $conns | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique
            foreach ($pid in $pids) {
                try {
                    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "🛑 Killing process $($proc.ProcessName) (PID $pid) on port $Port" -ForegroundColor Yellow
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    }
                } catch {}
            }
        }
    } catch {}
}

# Ports: Frontend (5173), Runtime (3001), Backend (8888)
Kill-Port -Port 5173
Kill-Port -Port 3001
Kill-Port -Port 8888

# Run the dev.sh script in WSL
wsl bash -c "cd /mnt/c/temp/AI/AGUI/agui/src && ./dev.sh"
