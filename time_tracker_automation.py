"""
Time Tracker Automation Tool
Automates daily time entry submission to EMS based on config file
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"time_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TimeTrackerAutomation:
    def __init__(self, config_path=None):
        """Initialize with config file"""
        if config_path is None:
            config_path = Path(__file__).parent / "time_tracker_config.json"

        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.driver = None
        self.wait = None

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Config loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file: {self.config_path}")
            raise

    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            # Uncomment for headless mode (no browser window)
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def login(self):
        """Login to EMS"""
        try:
            ems_config = self.config['ems_config']
            url = ems_config['url']
            username = ems_config['username']
            password = ems_config['password']

            logger.info(f"Navigating to {url}")
            self.driver.get(url)

            # Wait for login page to load
            self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

            # Fill login form
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")

            username_field.clear()
            username_field.send_keys(username)

            password_field.clear()
            password_field.send_keys(password)

            # Submit login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for dashboard to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard")))
            logger.info("Login successful")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def navigate_to_time_entry(self):
        """Navigate to time entry form"""
        try:
            # Look for "Log Time" or "Time Entry" button/link
            time_entry_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log Time')] | //a[contains(text(), 'Time Entry')]"))
            )
            time_entry_button.click()
            logger.info("Navigated to time entry form")
        except Exception as e:
            logger.error(f"Failed to navigate to time entry: {e}")
            raise

    def fill_time_entry(self, entry):
        """Fill and submit a single time entry"""
        try:
            logger.info(f"Processing entry: {entry['ticket']}")

            # Select Customer
            customer_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "customer"))
            ))
            customer_select.select_by_value(self.config['defaults']['customer'])
            logger.info(f"Selected customer: {self.config['defaults']['customer']}")

            # Select Project
            project_select = Select(self.driver.find_element(By.NAME, "project"))
            project_select.select_by_value(self.config['defaults']['project'])
            logger.info(f"Selected project: {self.config['defaults']['project']}")

            # Select Work Type
            work_type_select = Select(self.driver.find_element(By.NAME, "work_type"))
            work_type_select.select_by_value(entry['work_type'])
            logger.info(f"Selected work type: {entry['work_type']}")

            # Enter Ticket Number
            ticket_field = self.driver.find_element(By.NAME, "ticket")
            ticket_field.clear()
            ticket_field.send_keys(entry['ticket'])
            logger.info(f"Entered ticket: {entry['ticket']}")

            # Select Date (Today)
            date_field = self.driver.find_element(By.NAME, "date")
            date_field.clear()
            date_field.send_keys(datetime.now().strftime("%m/%d/%Y"))
            logger.info("Set date to today")

            # Enter Hours
            hours_field = self.driver.find_element(By.NAME, "hours")
            hours_field.clear()
            hours_field.send_keys(str(entry['hours']))
            logger.info(f"Entered hours: {entry['hours']}")

            # Enter Notes
            notes_field = self.driver.find_element(By.NAME, "notes")
            notes_field.clear()
            notes_field.send_keys(entry['notes'])
            logger.info(f"Entered notes: {entry['notes']}")

            # Submit
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()

            # Wait for success message or confirmation
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "success-message")))
            logger.info(f"Successfully submitted entry for {entry['ticket']}")

        except Exception as e:
            logger.error(f"Failed to fill entry {entry['ticket']}: {e}")
            raise

    def submit_all_entries(self):
        """Submit all time entries"""
        try:
            entries = self.config['daily_entries']
            total_hours = sum(entry['hours'] for entry in entries)

            logger.info(f"Starting submission of {len(entries)} entries (Total: {total_hours} hours)")

            for entry in entries:
                self.navigate_to_time_entry()
                self.fill_time_entry(entry)

            logger.info("All entries submitted successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to submit entries: {e}")
            return False

    def run(self):
        """Main execution flow"""
        try:
            logger.info("=" * 50)
            logger.info("Time Tracker Automation Started")
            logger.info("=" * 50)

            self.setup_driver()
            self.login()
            self.submit_all_entries()

            logger.info("=" * 50)
            logger.info("Time Tracker Automation Completed Successfully")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return False
        finally:
            self.close_driver()

        return True

def main():
    """Main entry point"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    automation = TimeTrackerAutomation(config_path)
    success = automation.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
