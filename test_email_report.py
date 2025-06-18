#!/usr/bin/env python3
"""
Test script to send TSA daily report to smith.witt@gmail.com immediately
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import getpass
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
from tsa_scraper import TSAPassengerVolumeScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tsa_report():
    """Test the TSA daily report by sending it to smith.witt@gmail.com"""
    
    print("🚀 Testing TSA Daily Report System")
    print("=" * 50)
    
    # Email configuration for testing
    sender_email = input("Enter your Gmail address: ").strip()
    sender_password = getpass.getpass("Enter your Gmail app password: ")
    
    recipient_email = "smith.witt@gmail.com"
    
    print(f"\n📧 Will send test report to: {recipient_email}")
    print("⏳ Starting data collection and report generation...")
    
    try:
        # Step 1: Scrape TSA data
        print("\n1️⃣ Scraping TSA passenger volume data...")
        scraper = TSAPassengerVolumeScraper()
        df = scraper.scrape_all_years(start_year=2022, end_year=2025)
        
        if df.empty:
            print("❌ Failed to scrape data")
            return False
        
        print(f"✅ Successfully scraped {len(df)} records")
        
        # Step 2: Calculate YoY growth
        print("\n2️⃣ Calculating year-over-year growth...")
        df_yoy = calculate_yoy_growth(df)
        
        # Show YoY calculation results
        total_records = len(df_yoy)
        yoy_calculated = df_yoy['yoy_percentage'].notna().sum()
        print(f"✅ YoY calculations: {yoy_calculated}/{total_records} records have YoY data")
        
        if yoy_calculated > 0:
            avg_yoy = df_yoy['yoy_percentage'].dropna().mean()
            print(f"📊 Average YoY growth: {avg_yoy:.1f}%")
        else:
            print("⚠️  No YoY data available - this may indicate missing historical data")
        
        # Step 3: Create visualization
        print("\n3️⃣ Creating visualizations...")
        plot_filename = create_visualization(df_yoy)
        
        if plot_filename is None:
            print("❌ Failed to create visualization")
            return False
        
        # Step 4: Generate summary stats
        print("\n4️⃣ Generating summary statistics...")
        summary_stats = generate_summary_stats(df_yoy)
        
        # Step 5: Save CSV
        print("\n5️⃣ Saving data to CSV...")
        data_dir = Path('tsa_data')
        data_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime('%Y-%m-%d')
        csv_filename = data_dir / f"tsa_yoy_data_{today}.csv"
        df_yoy.to_csv(csv_filename, index=False)
        
        # Step 6: Send email
        print("\n6️⃣ Sending email report...")
        success = send_test_email(
            sender_email, sender_password, recipient_email,
            plot_filename, csv_filename, summary_stats
        )
        
        if success:
            print("\n🎉 SUCCESS! Test report sent to smith.witt@gmail.com")
            print("📊 Check your email for the TSA daily report with:")
            print("   • Year-over-year growth visualization")
            print("   • Summary statistics")
            print("   • CSV data attachment")
            return True
        else:
            print("\n❌ Failed to send email")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False

def calculate_yoy_growth(df):
    """Calculate year-over-year growth for each day."""
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
            # Look for dates within 3 days of the target date
            for day_offset in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3
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

def create_visualization(df_yoy):
    """Create year-over-year growth visualization."""
    df_plot = df_yoy.dropna(subset=['yoy_percentage']).copy()
    
    if df_plot.empty:
        return None
    
    # Set up matplotlib
    plt.style.use('default')
    sns.set_palette("husl")
    
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
    data_dir = Path('tsa_data')
    data_dir.mkdir(exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    plot_filename = data_dir / f"tsa_yoy_growth_{today}.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return plot_filename

def generate_summary_stats(df_yoy):
    """Generate summary statistics for the email."""
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

def send_test_email(sender_email, sender_password, recipient_email, plot_filename, csv_filename, summary_stats):
    """Send the test email report."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "TSA Passenger Volumes - TEST REPORT"
        
        html_body = f"""
        <html>
        <body>
            <h2>🚀 TSA Passenger Volume Test Report</h2>
            <p><strong>Report Date:</strong> {summary_stats['latest_date']}</p>
            <p><em>This is a test email from the TSA Daily Report system</em></p>
            
            <h3>📊 Latest Data</h3>
            <ul>
                <li><strong>Latest Volume:</strong> {summary_stats['latest_volume']} passengers</li>
                <li><strong>YoY Growth:</strong> {summary_stats['latest_yoy']}</li>
            </ul>
            
            <h3>📈 30-Day Averages</h3>
            <ul>
                <li><strong>Average Volume:</strong> {summary_stats['avg_volume_30d']} passengers</li>
                <li><strong>Average YoY Growth:</strong> {summary_stats['avg_yoy_30d']}</li>
            </ul>
            
            <h3>📅 Year-to-Date Summary</h3>
            <ul>
                <li><strong>YTD Average Volume:</strong> {summary_stats['ytd_avg_volume']} passengers</li>
                <li><strong>YTD YoY Growth:</strong> {summary_stats['ytd_yoy']}</li>
            </ul>
            
            <h3>📊 Visualization</h3>
            <p>The attached chart shows daily passenger volumes and year-over-year growth trends.</p>
            
            <p><em>Test report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</em></p>
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
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        return False

if __name__ == "__main__":
    test_tsa_report() 