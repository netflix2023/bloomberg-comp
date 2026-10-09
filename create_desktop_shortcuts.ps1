$desktopPath = "C:\Users\e3402020\OneDrive - Dallas College\Desktop"
$targetPath = "C:\Users\e3402020\.gemini\antigravity-ide\scratch\bloomberg_market_data\index.html"
$workDir = "C:\Users\e3402020\.gemini\antigravity-ide\scratch\bloomberg_market_data"

$wshShell = New-Object -ComObject WScript.Shell

# 1. Direct Dashboard Opener Shortcut
$shortcutPath = Join-Path $desktopPath "Bloomberg Dashboard.lnk"
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $workDir
$shortcut.Description = "Open Bloomberg Trading Challenge Dashboard"
$shortcut.IconLocation = "shell32.dll,220"
$shortcut.Save()

# 2. Local Refresh & Launch Shortcut
$refreshBatPath = "C:\Users\e3402020\.gemini\antigravity-ide\scratch\bloomberg_market_data\REFRESH_AND_OPEN_DASHBOARD.bat"
$refreshShortcutPath = Join-Path $desktopPath "Update & Open Bloomberg Data.lnk"
$refreshShortcut = $wshShell.CreateShortcut($refreshShortcutPath)
$refreshShortcut.TargetPath = $refreshBatPath
$refreshShortcut.WorkingDirectory = $workDir
$refreshShortcut.Description = "Fetch latest Bloomberg quotes and open dashboard"
$refreshShortcut.IconLocation = "shell32.dll,238"
$refreshShortcut.Save()

# 3. Sync & Broadcast to Team Shortcut
$syncShareBatPath = "C:\Users\e3402020\.gemini\antigravity-ide\scratch\bloomberg_market_data\SYNC_AND_SHARE_WITH_TEAM.bat"
$syncShareShortcutPath = Join-Path $desktopPath "Sync & Share with Friend.lnk"
$syncShareShortcut = $wshShell.CreateShortcut($syncShareShortcutPath)
$syncShareShortcut.TargetPath = $syncShareBatPath
$syncShareShortcut.WorkingDirectory = $workDir
$syncShareShortcut.Description = "Pull Bloomberg quotes and push to GitHub so your friend's dashboard updates"
$syncShareShortcut.IconLocation = "shell32.dll,14"
$syncShareShortcut.Save()

Write-Output "Shortcuts created on Desktop."
