# Time Tracker Automation Guide

## Overview
This solution automates daily time entry submission to your EMS. It includes:
- Python Selenium automation script
- Configuration file for work entries
- Windows Task Scheduler setup for daily execution
- Logging and error handling

## Setup Instructions

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Your Time Tracker
Edit `time_tracker_config.json`:

```json
{
  "ems_config": {
    "url": "https://your-ems-url.com/login",
    "username": "your_username",
    "password": "your_password"
  },
  "defaults": {
    "customer": "Ibexis",
    "project": "Functional Testing",
    "date": "TODAY"
  },
  "daily_entries": [
    {
      "ticket": "TICKET-123",
      "title": "Work description",
      "hours": 2.0,
      "work_type": "Tester",
      "notes": "Activity notes here"
    }
  ]
}
```

**Fields:**
- `url`: Your EMS login page URL
- `username`: Your EMS username
- `password`: Your EMS password (consider using Windows Credential Manager instead)
- `daily_entries`: Array of time entries to submit

### 3. Test the Script Manually

```powershell
python time_tracker_automation.py
```

Verify:
- Script logs in successfully
- All entries are submitted
- No errors in the logs folder

### 4. Update Daily Entries
Modify the `daily_entries` array in `time_tracker_config.json` to match your actual work:

```json
{
  "ticket": "IBEXIS-396",
  "title": "Portal Enhancement – Display Index Starting and Ending Values",
  "hours": 2.0,
  "work_type": "Tester",
  "notes": "tested index value display changes in INT1"
}
```

### 5. Schedule Daily Execution (Windows Task Scheduler)

**Option A: PowerShell (Recommended)**
```powershell
# Run as Administrator
.\setup_scheduler.ps1
```

**Option B: Manual Setup**
1. Open "Task Scheduler" (Windows)
2. Create Basic Task
3. Name: "TimeTrackerAutomation"
4. Trigger: Daily at 8:00 AM
5. Action: 
   - Program: `python`
   - Arguments: `time_tracker_automation.py`
   - Start in: `C:\Users\RahulRanjan\OneDrive - ASPYRAILABS PRIVATE LIMITED\Desktop\Test Claude`

### 6. Monitor Logs
Logs are saved in `logs/` folder with timestamp:
```
logs/time_tracker_20260514_083045.log
```

View recent logs:
```powershell
Get-Content logs/*.log -Tail 20
```

## Customization

### Change Scheduled Time
Edit the time in `setup_scheduler.ps1`:
```powershell
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM  # Change 8:00AM to your preferred time
```

### Alternate Work Types
Update entries to alternate between work types:
```json
{
  "ticket": "IBEXIS-396",
  "work_type": "Consultant"  // or "Tester"
}
```

### Activity Note Templates
Use these realistic patterns:
- tested in INT1
- regression validation
- root cause analysis
- functional verification
- config validation
- PROD issue reproduction
- FAST policy validation
- workflow testing
- solution implementation support
- defect retesting

### Hide Browser Window
Uncomment in `time_tracker_automation.py`:
```python
# chrome_options.add_argument("--headless")  # Uncomment for headless mode
```

## Troubleshooting

### Script runs but entries don't submit
1. Check logs in `logs/` folder
2. Verify login credentials in config
3. Check if form field names match your EMS

### Form field not found
Update field selectors in `fill_time_entry()` method:
```python
# By.NAME finds elements by HTML name attribute
customer_field = self.driver.find_element(By.NAME, "customer")

# By.ID finds elements by ID
customer_field = self.driver.find_element(By.ID, "customer_select")

# By.CSS_SELECTOR uses CSS selectors
customer_field = self.driver.find_element(By.CSS_SELECTOR, ".customer-dropdown")
```

### Task doesn't run
1. Check Task Scheduler: `Get-ScheduledTask -TaskName TimeTrackerAutomation`
2. View task history: Right-click task → View All Properties → History
3. Run manually to test: `python time_tracker_automation.py`

### WebDriver errors
Install ChromeDriver:
```powershell
pip install webdriver-manager
```

## Advanced: Using Windows Credential Manager (Secure)

Instead of storing passwords in config:

```python
import subprocess
import json

def get_password_from_credential_manager(account):
    result = subprocess.run(
        ["cmdkey", "/list:" + account],
        capture_output=True,
        text=True
    )
    # Parse and return password
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Update config with real credentials
3. ✅ Test manually
4. ✅ Run scheduler setup
5. ✅ Monitor first few executions
6. ✅ Adjust form selectors if needed

## Support

If entries aren't being found:
1. Open the EMS application in a browser
2. Right-click → Inspect Element
3. Find the form field names
4. Update the Python script with correct selectors

## Security Notes

- Store sensitive passwords in Windows Credential Manager instead of config file
- Use HTTPS for EMS URL
- Run script with minimal required permissions
- Regularly review logs for suspicious activity
