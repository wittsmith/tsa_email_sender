#!/usr/bin/env python3
"""
Simple Lambda TSA Daily Report System
Uses only built-in libraries and minimal dependencies
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from datetime import datetime, timedelta
import logging
import urllib.request
import urllib.parse
from io import BytesIO
import base64
import csv
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTSAReporter:
    def __init__(self):
        # Load email configuration from environment variables
        self.sender_email = os.environ.get('SENDER_EMAIL')
        self.sender_password = os.environ.get('APP_PASSWORD')
        self.recipient_email = os.environ.get('RECIPIENT_EMAIL')
        
        # Validate configuration
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            raise ValueError("Missing required environment variables")
        
        logger.info(f"Simple TSA reporter initialized for {self.recipient_email}")
    
    def scrape_tsa_data(self):
        """Scrape TSA data using built-in libraries."""
        logger.info("Starting TSA data scrape...")
        
        try:
            # TSA data URL (this is a simplified approach)
            # In a real implementation, you'd need to handle the actual TSA website
            # For now, we'll create sample data to demonstrate the concept
            
            # Create sample data for demonstration
            today = datetime.now()
            data = []
            
            # Generate sample data for the last 30 days
            for i in range(30):
                date = today - timedelta(days=i)
                # Simulate realistic passenger volumes
                base_volume = 2000000  # 2M base
                day_of_week = date.weekday()
                
                # Weekend effect
                if day_of_week >= 5:  # Saturday/Sunday
                    volume = base_volume * 0.7
                else:
                    volume = base_volume * (1.1 + (day_of_week * 0.05))
                
                # Add some randomness
                import random
                volume = volume * (0.9 + random.random() * 0.2)
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'passenger_volume': int(volume),
                    'year': date.year
                })
            
            logger.info(f"Generated {len(data)} sample records")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping data: {e}")
            return None
    
    def calculate_yoy_growth(self, data):
        """Calculate year-over-year growth."""
        logger.info("Calculating year-over-year growth...")
        
        # Convert to more structured format
        current_year_data = {}
        for item in data:
            date = datetime.strptime(item['date'], '%Y-%m-%d')
            current_year_data[date] = item['passenger_volume']
        
        yoy_growth = []
        
        for date, volume in current_year_data.items():
            # Find same date last year
            last_year_date = date - timedelta(days=365)
            
            # For demo purposes, simulate last year's data
            # In real implementation, you'd have actual historical data
            last_year_volume = volume * 0.95  # Assume 5% growth
            
            yoy_ratio = volume / last_year_volume if last_year_volume > 0 else None
            yoy_percentage = (yoy_ratio - 1) * 100 if yoy_ratio else None
            
            yoy_growth.append({
                'date': date.strftime('%Y-%m-%d'),
                'passenger_volume': volume,
                'year': date.year,
                'yoy_percentage': yoy_percentage
            })
        
        return yoy_growth
    
    def generate_summary_stats(self, yoy_data):
        """Generate summary statistics."""
        logger.info("Generating summary statistics...")
        
        if not yoy_data:
            return None
        
        latest = yoy_data[0]  # Most recent data
        latest_date = datetime.strptime(latest['date'], '%Y-%m-%d')
        
        # Calculate 30-day average
        recent_data = yoy_data[:30]
        avg_volume = sum(item['passenger_volume'] for item in recent_data) / len(recent_data)
        avg_yoy = sum(item['yoy_percentage'] for item in recent_data if item['yoy_percentage']) / len([item for item in recent_data if item['yoy_percentage']])
        
        return {
            'latest_date': latest_date.strftime('%B %d, %Y'),
            'latest_volume': f"{latest['passenger_volume']:,}",
            'latest_yoy': f"{latest['yoy_percentage']:.1f}%" if latest['yoy_percentage'] else "N/A",
            'avg_volume_30d': f"{avg_volume:,.0f}",
            'avg_yoy_30d': f"{avg_yoy:.1f}%" if avg_yoy else "N/A",
            'total_records': len(yoy_data)
        }
    
    def create_simple_csv(self, yoy_data):
        """Create a simple CSV representation."""
        csv_buffer = BytesIO()
        writer = csv.writer(csv_buffer)
        
        # Write header
        writer.writerow(['Date', 'Passenger Volume', 'YoY Growth (%)'])
        
        # Write data
        for item in yoy_data:
            writer.writerow([
                item['date'],
                item['passenger_volume'],
                f"{item['yoy_percentage']:.1f}" if item['yoy_percentage'] else "N/A"
            ])
        
        csv_buffer.seek(0)
        return csv_buffer.getvalue()  # Return bytes directly
    
    def send_email_report(self, yoy_data, summary_stats):
        """Send the daily report via email."""
        logger.info("Sending email report...")
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = "TSA Passenger Volumes - Daily Report"
            
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
                
                <h3>Data Summary</h3>
                <ul>
                    <li><strong>Total Records:</strong> {summary_stats['total_records']}</li>
                </ul>
                
                <p><em>This report was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</em></p>
                <p><em>Note: This is a simplified version using sample data for demonstration.</em></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach CSV data
            csv_data = self.create_simple_csv(yoy_data)
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(csv_data)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename=tsa_data.csv')
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
            # Step 1: Scrape data
            data = self.scrape_tsa_data()
            if not data:
                logger.error("Failed to scrape data. Aborting report generation.")
                return False
            
            # Step 2: Calculate YoY growth
            yoy_data = self.calculate_yoy_growth(data)
            
            # Step 3: Generate summary statistics
            summary_stats = self.generate_summary_stats(yoy_data)
            if not summary_stats:
                logger.error("Failed to generate summary statistics.")
                return False
            
            # Step 4: Send email report
            success = self.send_email_report(yoy_data, summary_stats)
            
            if success:
                logger.info("Daily report completed successfully!")
                return True
            else:
                logger.error("Failed to send email report")
                return False
                
        except Exception as e:
            logger.error(f"Error in daily report generation: {e}")
            return False

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    try:
        reporter = SimpleTSAReporter()
        success = reporter.run_daily_report()
        
        return {
            'statusCode': 200 if success else 500,
            'body': json.dumps({
                'message': 'TSA report completed successfully' if success else 'TSA report failed',
                'success': success
            })
        }
    except Exception as e:
        logger.error(f"Lambda execution error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Lambda execution failed: {str(e)}',
                'success': False
            })
        } 