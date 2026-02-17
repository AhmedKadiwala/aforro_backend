# Project Structure Viewer for Habit Tracker
# Run this script to see the complete project structure excluding venv
# Created for ChatGPT to understand the project layout

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     HABIT TRACKER - PROJECT STRUCTURE     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

function Show-ProjectStructure {
    param(
        [string]$Path = ".",
        [int]$MaxDepth = 10  # Limit depth to avoid infinite recursion
    )
    
    function Get-Structure {
        param(
            [string]$CurrentPath,
            [int]$Depth = 0,
            [string]$Prefix = ""
        )
        
        if ($Depth -gt $MaxDepth) { return }
        
        # Get items excluding venv
        $items = Get-ChildItem -Path $CurrentPath -Exclude "venv" | Where-Object { 
            $_.FullName -notlike "*\venv\*" -and $_.Name -ne "__pycache__"  # Also exclude pycache
        }
        
        for ($i = 0; $i -lt $items.Count; $i++) {
            $item = $items[$i]
            $isLast = ($i -eq $items.Count - 1)
            
            # Determine prefix
            if ($isLast) {
                $connector = "└── "
                $newPrefix = "$Prefix    "
            } else {
                $connector = "├── "
                $newPrefix = "$Prefix│   "
            }
            
            # Display item with appropriate icon
            if ($item.PSIsContainer) {
                Write-Host "$Prefix$connector📁 $($item.Name)" -ForegroundColor Green
                # Recursively show subfolders
                Get-Structure -CurrentPath $item.FullName -Depth ($Depth + 1) -Prefix $newPrefix
            } else {
                # Show file size for context
                $size = if ($item.Length -gt 1MB) { 
                    "{0:N2} MB" -f ($item.Length / 1MB) 
                } elseif ($item.Length -gt 1KB) { 
                    "{0:N2} KB" -f ($item.Length / 1KB) 
                } else { 
                    "$($item.Length) B" 
                }
                Write-Host "$Prefix$connector📄 $($item.Name) ($size)" -ForegroundColor White
            }
        }
    }
    
    Get-Structure -CurrentPath $Path
}

# Run the structure viewer
Write-Host "📂 Current Directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Show root level first
Write-Host "ROOT FILES AND FOLDERS:" -ForegroundColor Magenta
Get-ChildItem -Exclude "venv" | ForEach-Object {
    if ($_.PSIsContainer) {
        Write-Host "  📁 $($_.Name)" -ForegroundColor Green
    } else {
        Write-Host "  📄 $($_.Name)" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "COMPLETE STRUCTURE (excluding venv):" -ForegroundColor Magenta
Write-Host ""

# Show full structure
Show-ProjectStructure

Write-Host ""
Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     NOTES FOR CHATGPT                      ║" -ForegroundColor Cyan
Write-Host "╠════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ • Virtual Environment (venv) is excluded   ║" -ForegroundColor Yellow
Write-Host "║ • venv contains Python packages/dependencies║" -ForegroundColor Yellow
Write-Host "║ • Project is Django-based (manage.py seen)  ║" -ForegroundColor Yellow
Write-Host "║ • Apps folder for custom Django apps        ║" -ForegroundColor Yellow
Write-Host "║ • Docker support (Dockerfile + compose)     ║" -ForegroundColor Yellow
Write-Host "║ • Environment variables (.env.example)      ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan