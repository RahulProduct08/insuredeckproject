# Windows Task Scheduler Setup Script for Time Tracker Automation
# Run as Administrator

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptPath "time_tracker_automation.py"
$ConfigPath = Join-Path $ScriptPath "time_tracker_config.json"

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "This script must be run as Administrator. Please run PowerShell as Administrator and try again." -ForegroundColor Red
    exit 1
}

# Get Python path
$PythonPath = (Get-Command python).Source
if (-not $PythonPath) {
    Write-Host "Python not found. Please install Python and add it to PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Setting up scheduled task for Time Tracker Automation..." -ForegroundColor Green
Write-Host "Python: $PythonPath"
Write-Host "Script: $PythonScript"
Write-Host "Config: $ConfigPath"

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$PythonScript`" `"$ConfigPath`"" `
    -WorkingDirectory $ScriptPath

# Create trigger (Daily at 8:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# Register task
$TaskName = "TimeTrackerAutomation"
$TaskDescription = "Automatically submit daily time entries to EMS"

try {
    # Remove existing task if present
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    # Register new task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description $TaskDescription `
        -RunLevel Highest

    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host "Task Name: $TaskName" -ForegroundColor Yellow
    Write-Host "Schedule: Daily at 8:00 AM" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Update time_tracker_config.json with your EMS credentials"
    Write-Host "2. Customize daily_entries as needed"
    Write-Host "3. Test the script manually: python time_tracker_automation.py"
    Write-Host "4. View task details: Get-ScheduledTask -TaskName TimeTrackerAutomation"

} catch {
    Write-Host "Error creating task: $_" -ForegroundColor Red
    exit 1
}
