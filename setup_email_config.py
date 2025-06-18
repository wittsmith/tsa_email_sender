#!/usr/bin/env python3
"""
Email Configuration Setup Script
Helps users configure email settings for the TSA daily reporting system.
"""

import json
import getpass
import os

def setup_email_config():
    """Interactive setup for email configuration."""
    print("=" * 60)
    print("TSA Daily Report - Email Configuration Setup")
    print("=" * 60)
    print()
    
    config = {}
    
    # SMTP Server Configuration
    print("SMTP Server Configuration:")
    print("1. Gmail (recommended)")
    print("2. Outlook/Hotmail")
    print("3. Custom SMTP")
    
    choice = input("Select your email provider (1-3): ").strip()
    
    if choice == "1":
        config["smtp_server"] = "smtp.gmail.com"
        config["smtp_port"] = 587
        print("\nGmail Configuration:")
        print("- You'll need to use an App Password, not your regular password")
        print("- To create an App Password:")
        print("  1. Go to your Google Account settings")
        print("  2. Enable 2-Step Verification if not already enabled")
        print("  3. Go to Security > App passwords")
        print("  4. Generate a new app password for 'Mail'")
        print()
    elif choice == "2":
        config["smtp_server"] = "smtp-mail.outlook.com"
        config["smtp_port"] = 587
        print("\nOutlook Configuration:")
        print("- You may need to enable 'Less secure app access' or use an app password")
        print()
    elif choice == "3":
        config["smtp_server"] = input("Enter SMTP server (e.g., smtp.gmail.com): ").strip()
        config["smtp_port"] = int(input("Enter SMTP port (e.g., 587): ").strip())
    else:
        print("Invalid choice. Using Gmail defaults.")
        config["smtp_server"] = "smtp.gmail.com"
        config["smtp_port"] = 587
    
    # Email credentials
    print("Email Credentials:")
    config["sender_email"] = input("Enter your email address: ").strip()
    config["sender_password"] = getpass.getpass("Enter your password/app password: ")
    
    # Recipients
    print("\nRecipient Configuration:")
    recipients = []
    while True:
        recipient = input("Enter recipient email address (or 'done' to finish): ").strip()
        if recipient.lower() == 'done':
            break
        if recipient:
            recipients.append(recipient)
    
    if not recipients:
        print("No recipients specified. Using sender email as recipient.")
        recipients = [config["sender_email"]]
    
    config["recipient_emails"] = recipients
    
    # Subject line
    config["subject"] = input("\nEnter email subject (or press Enter for default): ").strip()
    if not config["subject"]:
        config["subject"] = "TSA Passenger Volumes - Daily Report"
    
    # Save configuration
    config_file = "email_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"\n✓ Configuration saved to {config_file}")
    print("\nNext steps:")
    print("1. Test the configuration by running: python daily_tsa_report.py --test")
    print("2. Start the daily scheduler: python daily_tsa_report.py")
    print("3. The report will run automatically at 9:05 AM Eastern time")
    
    return config

def test_email_config():
    """Test the email configuration."""
    config_file = "email_config.json"
    
    if not os.path.exists(config_file):
        print("No email configuration found. Please run setup first.")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print("Testing email configuration...")
    
    try:
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        
        # Create test message
        msg = MIMEText("This is a test email from the TSA Daily Report system.")
        msg['Subject'] = "TSA Daily Report - Test Email"
        msg['From'] = config['sender_email']
        msg['To'] = config['recipient_emails'][0]
        
        # Send test email
        context = ssl.create_default_context()
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls(context=context)
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        print("✓ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Email test failed: {e}")
        print("\nCommon issues:")
        print("- Check your email and password")
        print("- For Gmail, make sure you're using an App Password")
        print("- Check if 2-factor authentication is enabled")
        return False

if __name__ == "__main__":
    print("TSA Daily Report Email Setup")
    print("=" * 40)
    
    if os.path.exists("email_config.json"):
        print("Email configuration already exists.")
        choice = input("Do you want to reconfigure? (y/n): ").strip().lower()
        if choice == 'y':
            setup_email_config()
        else:
            print("Using existing configuration.")
    else:
        setup_email_config()
    
    # Offer to test the configuration
    test_choice = input("\nWould you like to test the email configuration? (y/n): ").strip().lower()
    if test_choice == 'y':
        test_email_config() 