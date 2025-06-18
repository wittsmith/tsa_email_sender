import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TSAPassengerVolumeScraper:
    def __init__(self):
        self.base_url = "https://www.tsa.gov/travel/passenger-volumes"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url):
        """Fetch page content with error handling and retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def parse_table_data(self, html_content, year):
        """Parse the HTML table and extract passenger volume data."""
        if not html_content:
            return pd.DataFrame()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the table containing passenger volume data
        # The table typically has headers like "Date" and "TSA checkpoint travel numbers"
        tables = soup.find_all('table')
        
        for table in tables:
            # Look for a table that contains date and volume data
            headers = table.find_all('th')
            if headers:
                header_text = ' '.join([h.get_text(strip=True) for h in headers])
                if 'date' in header_text.lower() or 'tsa' in header_text.lower():
                    return self.extract_table_data(table, year)
        
        # If no table with expected headers found, try to find any table with date-like data
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:  # At least header + one data row
                first_row = rows[0]
                cells = first_row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Check if first cell looks like a date
                    first_cell_text = cells[0].get_text(strip=True)
                    if '/' in first_cell_text and any(char.isdigit() for char in first_cell_text):
                        return self.extract_table_data(table, year)
        
        logger.warning(f"No suitable table found for year {year}")
        return pd.DataFrame()
    
    def extract_table_data(self, table, year):
        """Extract data from a specific table."""
        data = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                date_text = cells[0].get_text(strip=True)
                volume_text = cells[1].get_text(strip=True)
                
                # Clean and parse the data
                try:
                    # Parse date (assuming format like "1/1/2025" or "01/01/2025")
                    if '/' in date_text:
                        date_parts = date_text.split('/')
                        if len(date_parts) == 3:
                            month, day, year_part = date_parts
                            # If year is only 2 digits, assume it's the current year
                            if len(year_part) == 2:
                                year_part = f"20{year_part}"
                            date_obj = datetime.strptime(f"{month}/{day}/{year_part}", "%m/%d/%Y")
                        else:
                            continue
                    else:
                        # Try other date formats
                        date_obj = datetime.strptime(date_text, "%Y-%m-%d")
                    
                    # Parse volume (remove commas and convert to int)
                    volume = int(volume_text.replace(',', ''))
                    
                    data.append({
                        'date': date_obj,
                        'passenger_volume': volume,
                        'year': year
                    })
                    
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Could not parse row: {date_text}, {volume_text} - {e}")
                    continue
        
        return pd.DataFrame(data)
    
    def scrape_year(self, year):
        """Scrape data for a specific year."""
        if year == 2025:
            url = self.base_url
        else:
            url = f"{self.base_url}/{year}"
        
        logger.info(f"Scraping data for year {year} from {url}")
        
        html_content = self.get_page_content(url)
        if html_content:
            df = self.parse_table_data(html_content, year)
            if not df.empty:
                logger.info(f"Successfully scraped {len(df)} records for year {year}")
                return df
            else:
                logger.warning(f"No data found for year {year}")
        else:
            logger.error(f"Failed to get content for year {year}")
        
        return pd.DataFrame()
    
    def scrape_all_years(self, start_year=2022, end_year=2025):
        """Scrape data for all years from start_year to end_year."""
        all_data = []
        
        for year in range(start_year, end_year + 1):
            df = self.scrape_year(year)
            if not df.empty:
                all_data.append(df)
            time.sleep(1)  # Be respectful to the server
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            # Sort by date
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            return combined_df
        else:
            logger.error("No data was successfully scraped")
            return pd.DataFrame()
    
    def save_to_csv(self, df, filename="tsa_passenger_volumes.csv"):
        """Save the DataFrame to a CSV file."""
        if not df.empty:
            df.to_csv(filename, index=False)
            logger.info(f"Data saved to {filename}")
        else:
            logger.warning("No data to save")

def main():
    """Main function to run the scraper."""
    scraper = TSAPassengerVolumeScraper()
    
    # Scrape data from 2022 to 2025
    logger.info("Starting TSA passenger volume data scraping...")
    df = scraper.scrape_all_years(start_year=2022, end_year=2025)
    
    if not df.empty:
        print(f"\nScraped {len(df)} records")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print("\nFirst few records:")
        print(df.head())
        print("\nLast few records:")
        print(df.tail())
        
        # Save to CSV
        scraper.save_to_csv(df)
        
        return df
    else:
        print("No data was scraped successfully")
        return None

if __name__ == "__main__":
    df = main() 