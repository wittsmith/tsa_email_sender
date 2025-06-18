#!/usr/bin/env python3
"""
Daily TSA Passenger Volume Report Generator
Automatically scrapes TSA data, calculates YoY growth, and emails daily reports.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import schedule
import time
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
import json
from tsa_scraper import TSAPassengerVolumeScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tsa_daily_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TSADailyReporter:
    def __init__(self, config_file='email_config.json'):
        self.scraper = TSAPassengerVolumeScraper()
        self.config = self.load_config(config_file)
        self.data_dir = Path('tsa_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Set up matplotlib for email-friendly plots
        plt.style.use('default')
        sns.set_palette("husl")
        
    def load_config(self, config_file):
        """Load email configuration from JSON file."""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config template
            default_config = {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password",
                "recipient_emails": ["recipient1@example.com", "recipient2@example.com"],
                "subject": "TSA Passenger Volumes - Daily Report"
            }
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            logger.warning(f"Created default config file: {config_file}")
            logger.warning("Please update the email configuration before running.")
            return default_config
    
    def scrape_latest_data(self):
        """Scrape the latest TSA data."""
        logger.info("Starting daily TSA data scrape...")
        
        try:
            # Scrape all years to ensure we have complete data
            df = self.scraper.scrape_all_years(start_year=2022, end_year=2025)
            
            if df.empty:
                logger.error("No data was scraped successfully")
                return None
            
            # Save today's data
            today = datetime.now().strftime('%Y-%m-%d')
            filename = self.data_dir / f"tsa_data_{today}.csv"
            df.to_csv(filename, index=False)
            
            logger.info(f"Successfully scraped {len(df)} records and saved to {filename}")
            return df
            
        except Exception as e:
            logger.error(f"Error scraping data: {e}")
            return None
    
    def calculate_yoy_growth(self, df):
        """Calculate year-over-year growth for each day."""
        logger.info("Calculating year-over-year growth...")
        
        # Create a copy to avoid modifying original
        df_yoy = df.copy()
        
        # Add month and day columns for matching
        df_yoy['month'] = df_yoy['date'].dt.month
        df_yoy['day'] = df_yoy['date'].dt.day
        
        # Calculate YoY growth
        yoy_growth = []
        
        for _, row in df_yoy.iterrows():
            current_date = row['date']
            current_volume = row['passenger_volume']
            
            # Find the same date last year
            last_year_date = current_date - timedelta(days=365)
            
            # Look for data from last year (within a few days to handle leap years)
            last_year_data = df_yoy[
                (df_yoy['month'] == last_year_date.month) &
                (df_yoy['day'] == last_year_date.day) &
                (df_yoy['year'] == last_year_date.year)
            ]
            
            if not last_year_data.empty:
                last_year_volume = last_year_data.iloc[0]['passenger_volume']
                yoy_ratio = current_volume / last_year_volume if last_year_volume > 0 else None
                yoy_percentage = (yoy_ratio - 1) * 100 if yoy_ratio else None
            else:
                yoy_ratio = None
                yoy_percentage = None
            
            yoy_growth.append({
                'date': current_date,
                'passenger_volume': current_volume,
                'year': row['year'],
                'yoy_ratio': yoy_ratio,
                'yoy_percentage': yoy_percentage
            })
        
        return pd.DataFrame(yoy_growth)
    
    def create_visualizations(self, df_yoy):
        """Create year-over-year growth visualizations."""
        logger.info("Creating visualizations...")
        
        # Filter to only include data with YoY calculations
        df_plot = df_yoy.dropna(subset=['yoy_percentage']).copy()
        
        if df_plot.empty:
            logger.warning("No YoY data available for visualization")
            return None
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Daily passenger volumes by year
        for year in sorted(df_yoy['year'].unique()):
            year_data = df_yoy[df_yoy['year'] == year]
            ax1.plot(year_data['date'], year_data['passenger_volume'], 
                    label=f'{year}', linewidth=2, alpha=0.8)
        
        ax1.set_title('TSA Daily Passenger Volumes by Year', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Passenger Volume', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Format y-axis with commas
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        # Plot 2: Year-over-year growth percentage
        ax2.plot(df_plot['date'], df_plot['yoy_percentage'], 
                color='red', linewidth=2, alpha=0.8)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Year-over-Year Growth (%)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('YoY Growth (%)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Add color coding for positive/negative growth
        positive_growth = df_plot[df_plot['yoy_percentage'] > 0]
        negative_growth = df_plot[df_plot['yoy_percentage'] < 0]
        
        if not positive_growth.empty:
            ax2.fill_between(positive_growth['date'], 0, positive_growth['yoy_percentage'], 
                           alpha=0.3, color='green', label='Positive Growth')
        if not negative_growth.empty:
            ax2.fill_between(negative_growth['date'], 0, negative_growth['yoy_percentage'], 
                           alpha=0.3, color='red', label='Negative Growth')
        
        ax2.legend()
        
        # Rotate x-axis labels for better readability
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the plot
        today = datetime.now().strftime('%Y-%m-%d')
        plot_filename = self.data_dir / f"tsa_yoy_growth_{today}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to {plot_filename}")
        return plot_filename
    
    def generate_summary_stats(self, df_yoy):
        """Generate summary statistics for the email."""
        logger.info("Generating summary statistics...")
        
        # Get latest data
        latest_date = df_yoy['date'].max()
        latest_volume = df_yoy[df_yoy['date'] == latest_date]['passenger_volume'].iloc[0]
        latest_yoy = df_yoy[df_yoy['date'] == latest_date]['yoy_percentage'].iloc[0]
        
        # Get data from last 30 days
        thirty_days_ago = latest_date - timedelta(days=30)
        recent_data = df_yoy[df_yoy['date'] >= thirty_days_ago]
        
        # Calculate statistics
        avg_volume_30d = recent_data['passenger_volume'].mean()
        avg_yoy_30d = recent_data['yoy_percentage'].dropna().mean()
        
        # Get year-to-date data
        current_year = latest_date.year
        ytd_data = df_yoy[df_yoy['year'] == current_year]
        ytd_avg_volume = ytd_data['passenger_volume'].mean()
        
        # Compare with previous year YTD
        prev_year_ytd = df_yoy[df_yoy['year'] == current_year - 1]
        prev_ytd_avg = prev_year_ytd['passenger_volume'].mean() if not prev_year_ytd.empty else None
        ytd_yoy = ((ytd_avg_volume / prev_ytd_avg) - 1) * 100 if prev_ytd_avg else None
        
        summary = {
            'latest_date': latest_date.strftime('%B %d, %Y'),
            'latest_volume': f"{latest_volume:,}",
            'latest_yoy': f"{latest_yoy:.1f}%" if latest_yoy else "N/A",
            'avg_volume_30d': f"{avg_volume_30d:,.0f}",
            'avg_yoy_30d': f"{avg_yoy_30d:.1f}%" if avg_yoy_30d else "N/A",
            'ytd_avg_volume': f"{ytd_avg_volume:,.0f}",
            'ytd_yoy': f"{ytd_yoy:.1f}%" if ytd_yoy else "N/A",
            'total_records': len(df_yoy)
        }
        
        return summary
    
    def send_email_report(self, plot_filename, csv_filename, summary_stats):
        """Send the daily report via email."""
        logger.info("Sending email report...")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = ', '.join(self.config['recipient_emails'])
            msg['Subject'] = self.config['subject']
            
            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2>TSA Passenger Volume Daily Report</h2>
                <p><strong>Report Date:</strong> {summary_stats['latest_date']}</p>
                
                <h3>Latest Data</h3>
                <ul>
                    <li><strong>Latest Volume:</strong> {summary_stats['latest_volume']} passengers</li>
                    <li><strong>YoY Growth:</strong> {summary_stats['latest_yoy']}</li>
                </ul>
                
                <h3>30-Day Averages</h3>
                <ul>
                    <li><strong>Average Volume:</strong> {summary_stats['avg_volume_30d']} passengers</li>
                    <li><strong>Average YoY Growth:</strong> {summary_stats['avg_yoy_30d']}</li>
                </ul>
                
                <h3>Year-to-Date Summary</h3>
                <ul>
                    <li><strong>YTD Average Volume:</strong> {summary_stats['ytd_avg_volume']} passengers</li>
                    <li><strong>YTD YoY Growth:</strong> {summary_stats['ytd_yoy']}</li>
                </ul>
                
                <h3>Visualization</h3>
                <p>The attached chart shows daily passenger volumes and year-over-year growth trends.</p>
                
                <p><em>This report was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach the plot
            with open(plot_filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {plot_filename.name}'
            )
            msg.attach(part)
            
            # Attach the CSV
            with open(csv_filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {csv_filename.name}'
            )
            msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"Email report sent successfully to {len(self.config['recipient_emails'])} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def run_daily_report(self):
        """Main function to run the daily report."""
        logger.info("Starting daily TSA report generation...")
        
        try:
            # Step 1: Scrape latest data
            df = self.scrape_latest_data()
            if df is None:
                logger.error("Failed to scrape data. Aborting report generation.")
                return False
            
            # Step 2: Calculate YoY growth
            df_yoy = self.calculate_yoy_growth(df)
            
            # Step 3: Create visualizations
            plot_filename = self.create_visualizations(df_yoy)
            if plot_filename is None:
                logger.error("Failed to create visualizations. Aborting report generation.")
                return False
            
            # Step 4: Generate summary statistics
            summary_stats = self.generate_summary_stats(df_yoy)
            
            # Step 5: Save CSV with YoY data
            today = datetime.now().strftime('%Y-%m-%d')
            csv_filename = self.data_dir / f"tsa_yoy_data_{today}.csv"
            df_yoy.to_csv(csv_filename, index=False)
            
            # Step 6: Send email report
            success = self.send_email_report(plot_filename, csv_filename, summary_stats)
            
            if success:
                logger.info("Daily report completed successfully!")
                return True
            else:
                logger.error("Failed to send email report")
                return False
                
        except Exception as e:
            logger.error(f"Error in daily report generation: {e}")
            return False

def schedule_daily_report():
    """Schedule the daily report to run at 9:05 AM Eastern."""
    reporter = TSADailyReporter()
    
    # Schedule the job to run at 9:05 AM Eastern every day
    schedule.every().day.at("09:05").do(reporter.run_daily_report)
    
    logger.info("Daily TSA report scheduled for 9:05 AM Eastern time")
    logger.info("Press Ctrl+C to stop the scheduler")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    # For testing, you can run the report immediately
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--test":
        reporter = TSADailyReporter()
        reporter.run_daily_report()
    else:
        # Run the scheduler
        schedule_daily_report() 