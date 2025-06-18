# TSA Passenger Volume Scraper & Daily Report System

A comprehensive Python system that scrapes TSA passenger volume data from the [TSA.gov website](https://www.tsa.gov/travel/passenger-volumes) and automatically generates daily email reports with year-over-year growth analysis.

## Features

### Core Scraper
- **Multi-year scraping**: Automatically scrapes data from 2022-2025
- **Robust error handling**: Retry logic with exponential backoff
- **Data validation**: Ensures data quality and completeness
- **Flexible output**: Saves data as CSV and returns pandas DataFrame
- **Respectful scraping**: Includes delays between requests
- **Comprehensive logging**: Detailed logging for debugging

### Daily Reporting System
- **Automated scheduling**: Runs daily at 9:05 AM Eastern time
- **Year-over-year analysis**: Calculates daily YoY growth percentages
- **Professional visualizations**: Creates line graphs showing trends
- **Email delivery**: Sends HTML reports with charts and CSV attachments
- **Summary statistics**: Includes 30-day averages and YTD comparisons
- **System service support**: Can run as background service on Linux/macOS

## Installation

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### 1. Basic Scraper Usage

Run the main scraper to collect all data from 2022-2025:

```python
python tsa_scraper.py
```

### 2. Test the Scraper

Run the test script to verify functionality:

```python
python test_scraper.py
```

### 3. Setup Daily Email Reports

Configure email settings for daily reports:

```bash
python setup_email_config.py
```

This interactive script will help you:
- Choose your email provider (Gmail, Outlook, or custom SMTP)
- Configure email credentials
- Set up recipient addresses
- Test the email configuration

### 4. Test Daily Report

Test the daily reporting system:

```bash
python daily_tsa_report.py --test
```

### 5. Start Daily Scheduling

Start the automated daily reporting:

```bash
python daily_tsa_report.py
```

## Email Configuration

### Gmail Setup (Recommended)

1. **Enable 2-Step Verification** in your Google Account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → App passwords
   - Select "Mail" and generate password
3. **Use the App Password** (not your regular password) in the configuration

### Configuration File

The system creates `email_config.json` with your settings:

```json
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "recipient_emails": ["recipient1@example.com", "recipient2@example.com"],
    "subject": "TSA Passenger Volumes - Daily Report"
}
```

## Daily Report Features

### Email Content
- **Subject**: "TSA Passenger Volumes - Daily Report"
- **HTML Body**: Professional formatting with summary statistics
- **Attachments**: 
  - Line graph showing YoY growth trends
  - CSV file with complete YoY data

### Visualizations
- **Dual-chart layout**: Daily volumes by year + YoY growth percentage
- **Color coding**: Green for positive growth, red for negative
- **Professional styling**: Clean, email-friendly design

### Summary Statistics
- **Latest data**: Most recent passenger volume and YoY growth
- **30-day averages**: Rolling averages for volume and growth
- **Year-to-date**: YTD averages and comparisons

## Deployment Options

### Option 1: Manual Scheduling (Development)

Run the scheduler manually:

```bash
python daily_tsa_report.py
```

### Option 2: System Service (Production)

#### Linux (systemd)

1. **Edit the service file**:
   ```bash
   # Update paths in tsa-daily-report.service
   sudo nano tsa-daily-report.service
   ```

2. **Install and enable the service**:
   ```bash
   sudo cp tsa-daily-report.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable tsa-daily-report
   sudo systemctl start tsa-daily-report
   ```

3. **Check status**:
   ```bash
   sudo systemctl status tsa-daily-report
   ```

#### macOS (launchd)

1. **Edit the plist file**:
   ```bash
   # Update paths in com.tsa.dailyreport.plist
   nano com.tsa.dailyreport.plist
   ```

2. **Install the service**:
   ```bash
   cp com.tsa.dailyreport.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.tsa.dailyreport.plist
   ```

3. **Check status**:
   ```bash
   launchctl list | grep tsa
   ```

### Option 3: Cron Job (Alternative)

Add to crontab to run at 9:05 AM Eastern:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed)
5 9 * * * cd /path/to/rivermont_capital_project && /path/to/venv/bin/python daily_tsa_report.py --test
```

## Output Format

### Scraper Output
The scraper returns a pandas DataFrame with:
- **date**: datetime object of the travel date
- **passenger_volume**: integer representing TSA checkpoint travel numbers
- **year**: integer year for easy filtering

### Daily Report Output
The daily report generates:
- **CSV files**: `tsa_data_YYYY-MM-DD.csv` and `tsa_yoy_data_YYYY-MM-DD.csv`
- **Visualizations**: `tsa_yoy_growth_YYYY-MM-DD.png`
- **Logs**: `tsa_daily_report.log`

## URL Structure

The scraper handles the different URL patterns:
- **2025**: `https://www.tsa.gov/travel/passenger-volumes`
- **2024**: `https://www.tsa.gov/travel/passenger-volumes/2024`
- **2023**: `https://www.tsa.gov/travel/passenger-volumes/2023`
- **2022**: `https://www.tsa.gov/travel/passenger-volumes/2022`

## Year-over-Year Calculation

The system calculates YoY growth as:
```
YoY Growth % = ((Current Year Volume / Previous Year Volume) - 1) × 100
```

This provides insights into:
- Daily recovery patterns
- Seasonal trends
- Overall travel demand growth

## Data Quality

The scraper includes several data quality checks:
- Validates date formats
- Removes commas from volume numbers
- Handles missing or malformed data gracefully
- Provides detailed logging for troubleshooting

## Error Handling

- **Network errors**: Automatic retry with exponential backoff
- **Parsing errors**: Graceful handling of malformed HTML
- **Missing data**: Logs warnings for missing years or tables
- **Rate limiting**: Built-in delays between requests
- **Email failures**: Comprehensive error logging

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation
- `matplotlib` & `seaborn`: Visualization
- `schedule`: Task scheduling
- `lxml`: XML/HTML parser backend

## Troubleshooting

### Common Issues

1. **No data scraped**: Check if the website structure has changed
2. **Network errors**: Verify internet connection and try again
3. **Email failures**: Check SMTP settings and app passwords
4. **Scheduling issues**: Verify system time and timezone settings

### Debug Mode

Enable debug logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

### Log Files

- `tsa_daily_report.log`: Main application log
- Check system logs for service-related issues

## Legal and Ethical Considerations

- This scraper is for educational and research purposes
- Respect the website's robots.txt and terms of service
- Include reasonable delays between requests
- The scraper uses a realistic User-Agent header
- Data is publicly available on the TSA website

## License

This project is for educational purposes. Please respect the TSA website's terms of service when using this scraper. 