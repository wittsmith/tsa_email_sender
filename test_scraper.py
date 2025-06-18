#!/usr/bin/env python3
"""
Test script for the TSA Passenger Volume Scraper
"""

from tsa_scraper import TSAPassengerVolumeScraper
import pandas as pd

def test_scraper():
    """Test the scraper with a single year to verify functionality."""
    scraper = TSAPassengerVolumeScraper()
    
    print("Testing TSA Passenger Volume Scraper...")
    print("=" * 50)
    
    # Test scraping just 2025 data first
    print("Testing 2025 data scraping...")
    df_2025 = scraper.scrape_year(2025)
    
    if not df_2025.empty:
        print(f"✓ Successfully scraped {len(df_2025)} records for 2025")
        print(f"Date range: {df_2025['date'].min()} to {df_2025['date'].max()}")
        print("\nSample data:")
        print(df_2025.head())
        
        # Test data quality
        print(f"\nData quality check:")
        print(f"- Total records: {len(df_2025)}")
        print(f"- Missing dates: {df_2025['date'].isnull().sum()}")
        print(f"- Missing volumes: {df_2025['passenger_volume'].isnull().sum()}")
        print(f"- Min volume: {df_2025['passenger_volume'].min():,}")
        print(f"- Max volume: {df_2025['passenger_volume'].max():,}")
        print(f"- Average volume: {df_2025['passenger_volume'].mean():,.0f}")
        
        return True
    else:
        print("✗ Failed to scrape 2025 data")
        return False

def test_full_scrape():
    """Test scraping all years (2022-2025)."""
    scraper = TSAPassengerVolumeScraper()
    
    print("\n" + "=" * 50)
    print("Testing full scrape (2022-2025)...")
    
    df_full = scraper.scrape_all_years(start_year=2022, end_year=2025)
    
    if not df_full.empty:
        print(f"✓ Successfully scraped {len(df_full)} total records")
        print(f"Date range: {df_full['date'].min()} to {df_full['date'].max()}")
        
        # Group by year to show summary
        yearly_summary = df_full.groupby('year').agg({
            'passenger_volume': ['count', 'mean', 'min', 'max']
        }).round(0)
        
        print("\nYearly summary:")
        print(yearly_summary)
        
        # Save test results
        scraper.save_to_csv(df_full, "test_tsa_data.csv")
        print("\n✓ Test data saved to test_tsa_data.csv")
        
        return True
    else:
        print("✗ Failed to scrape full dataset")
        return False

if __name__ == "__main__":
    # Run tests
    test_2025 = test_scraper()
    
    if test_2025:
        test_full = test_full_scrape()
        
        if test_full:
            print("\n" + "=" * 50)
            print("🎉 All tests passed! The scraper is working correctly.")
        else:
            print("\n" + "=" * 50)
            print("⚠️  Full scrape test failed, but single year test passed.")
    else:
        print("\n" + "=" * 50)
        print("❌ Basic scraper test failed. Check the implementation.") 