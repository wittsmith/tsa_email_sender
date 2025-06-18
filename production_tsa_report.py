#!/usr/bin/env python3
"""
Production TSA Daily Report System
Runs every weekday at 9:05 AM Eastern time using .env configuration
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
from tsa_scraper import TSAPassengerVolumeScraper
from dotenv import load_dotenv
import pytz  # Add this import at the top with other imports

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tsa_production_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionTSAReporter:
    def __init__(self):
        self.scraper = TSAPassengerVolumeScraper()
        self.data_dir = Path('tsa_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Load email configuration from .env
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('APP_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # Validate configuration
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            raise ValueError("Missing required environment variables. Please check your .env file.")
        
        # Set up matplotlib for email-friendly plots
        plt.style.use('default')
        sns.set_palette("husl")
        
        logger.info(f"Production reporter initialized for {self.recipient_email}")
    
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
        
        df_yoy = df.copy()
        df_yoy['month'] = df_yoy['date'].dt.month
        df_yoy['day'] = df_yoy['date'].dt.day
        
        yoy_growth = []
        
        for _, row in df_yoy.iterrows():
            current_date = row['date']
            current_volume = row['passenger_volume']
            current_year = row['year']
            
            # Find the same date last year
            last_year_date = current_date - timedelta(days=365)
            
            # Look for data from last year (same month and day)
            last_year_data = df_yoy[
                (df_yoy['month'] == last_year_date.month) &
                (df_yoy['day'] == last_year_date.day) &
                (df_yoy['year'] == last_year_date.year)
            ]
            
            # If no exact match, try to find the closest date within ±3 days
            if last_year_data.empty:
                for day_offset in range(-3, 4):
                    search_date = last_year_date + timedelta(days=day_offset)
                    search_data = df_yoy[
                        (df_yoy['month'] == search_date.month) &
                        (df_yoy['day'] == search_date.day) &
                        (df_yoy['year'] == search_date.year)
                    ]
                    if not search_data.empty:
                        last_year_data = search_data
                        break
            
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
                'year': current_year,
                'yoy_ratio': yoy_ratio,
                'yoy_percentage': yoy_percentage
            })
        
        return pd.DataFrame(yoy_growth)
    
    def create_visualization(self, df_yoy):
        """Create year-over-year growth visualization."""
        logger.info("Creating visualizations...")
        
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
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
        
        # Plot 2: Year-over-year growth percentage
        ax2.plot(df_plot['date'], df_plot['yoy_percentage'], 
                color='red', linewidth=2, alpha=0.8)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('Year-over-Year Growth (%)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('YoY Growth (%)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Add color coding
        positive_growth = df_plot[df_plot['yoy_percentage'] > 0]
        negative_growth = df_plot[df_plot['yoy_percentage'] < 0]
        
        if not positive_growth.empty:
            ax2.fill_between(positive_growth['date'], 0, positive_growth['yoy_percentage'], 
                           alpha=0.3, color='green', label='Positive Growth')
        if not negative_growth.empty:
            ax2.fill_between(negative_growth['date'], 0, negative_growth['yoy_percentage'], 
                           alpha=0.3, color='red', label='Negative Growth')
        
        ax2.legend()
        
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
        
        latest_date = df_yoy['date'].max()
        latest_volume = df_yoy[df_yoy['date'] == latest_date]['passenger_volume'].iloc[0]
        latest_yoy = df_yoy[df_yoy['date'] == latest_date]['yoy_percentage'].iloc[0]
        
        thirty_days_ago = latest_date - timedelta(days=30)
        recent_data = df_yoy[df_yoy['date'] >= thirty_days_ago]
        
        avg_volume_30d = recent_data['passenger_volume'].mean()
        avg_yoy_30d = recent_data['yoy_percentage'].dropna().mean()
        
        current_year = latest_date.year
        ytd_data = df_yoy[df_yoy['year'] == current_year]
        ytd_avg_volume = ytd_data['passenger_volume'].mean()
        
        prev_year_ytd = df_yoy[df_yoy['year'] == current_year - 1]
        prev_ytd_avg = prev_year_ytd['passenger_volume'].mean() if not prev_year_ytd.empty else None
        ytd_yoy = ((ytd_avg_volume / prev_ytd_avg) - 1) * 100 if prev_ytd_avg else None
        
        return {
            'latest_date': latest_date.strftime('%B %d, %Y'),
            'latest_volume': f"{latest_volume:,}",
            'latest_yoy': f"{latest_yoy:.1f}%" if latest_yoy else "N/A",
            'avg_volume_30d': f"{avg_volume_30d:,.0f}",
            'avg_yoy_30d': f"{avg_yoy_30d:.1f}%" if avg_yoy_30d else "N/A",
            'ytd_avg_volume': f"{ytd_avg_volume:,.0f}",
            'ytd_yoy': f"{ytd_yoy:.1f}%" if ytd_yoy else "N/A",
            'total_records': len(df_yoy)
        }
    
    def send_email_report(self, plot_filename, csv_filename, summary_stats):
        """Send the daily report via email."""
        logger.info("Sending email report...")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = "TSA Passenger Volumes"
            
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
            part.add_header('Content-Disposition', f'attachment; filename= {plot_filename.name}')
            msg.attach(part)
            
            # Attach the CSV
            with open(csv_filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {csv_filename.name}')
            msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email report sent successfully to {self.recipient_email}")
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
            
            # Show YoY calculation results
            total_records = len(df_yoy)
            yoy_calculated = df_yoy['yoy_percentage'].notna().sum()
            logger.info(f"YoY calculations: {yoy_calculated}/{total_records} records have YoY data")
            
            # Step 3: Create visualizations
            plot_filename = self.create_visualization(df_yoy)
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

def wait_until_next_905am_eastern():
    EASTERN = pytz.timezone('US/Eastern')
    now_utc = datetime.now(pytz.utc)
    now_et = now_utc.astimezone(EASTERN)
    # Find next weekday 9:05 AM ET
    next_run = now_et.replace(hour=9, minute=5, second=0, microsecond=0)
    if now_et >= next_run or now_et.weekday() >= 5:  # If past 9:05 or weekend
        # Move to next weekday
        days_ahead = 1
        while (now_et + timedelta(days=days_ahead)).weekday() >= 5:
            days_ahead += 1
        next_run = (now_et + timedelta(days=days_ahead)).replace(hour=9, minute=5, second=0, microsecond=0)
    wait_seconds = (next_run - now_et).total_seconds()
    logger.info(f"Waiting {wait_seconds/60:.1f} minutes until next 9:05 AM ET ({next_run.strftime('%Y-%m-%d %H:%M:%S')})")
    time.sleep(wait_seconds)

if __name__ == "__main__":
    reporter = ProductionTSAReporter()
    while True:
        wait_until_next_905am_eastern()
        reporter.run_daily_report() 