#!/usr/bin/env python3
"""
Meiji Yasuda Baby Names Scraper - Complete Solution
==================================================

Based on JavaScript analysis, this scraper downloads Japanese baby names data
from Meiji Yasuda's ranking website using their actual API endpoints.

Key Findings:
- Names data: n_YYYY.json (available from 1912-present)
- Readings data: y_YYYY.json (available from 2004-present)  
- Data structure includes: name, yomi (reading), rank, sex (m/f), code
- Additional kanji rankings available in nameListKanji.json
"""

import requests
import json
import pandas as pd
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meiji_yasuda_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MeijiYasudaScraper:
    """
    Scraper for Meiji Yasuda baby names ranking data.
    
    Based on JavaScript analysis of the official website:
    https://www.meijiyasuda.co.jp/enjoy/ranking/
    """
    
    def __init__(self, base_output_dir: str = "meiji_yasuda_data"):
        self.base_url = "https://www.meijiyasuda.co.jp/enjoy/ranking/assets/json/"
        self.output_dir = Path(base_output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "names").mkdir(exist_ok=True)
        (self.output_dir / "readings").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Historical ranges found in JavaScript
        self.names_start_year = 1912  # Names data starts from 1912
        self.readings_start_year = 2004  # Readings data starts from 2004
        self.current_year = datetime.now().year
        
        logger.info(f"Initialized scraper. Output directory: {self.output_dir}")
        
    def download_file(self, filename: str, save_path: Path, retries: int = 3) -> bool:
        """Download a single JSON file with retry logic."""
        url = f"{self.base_url}{filename}"
        
        for attempt in range(retries):
            try:
                logger.info(f"Downloading {filename} (attempt {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Validate JSON
                    data = response.json()
                    
                    # Save raw data
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"✓ Successfully downloaded {filename}")
                    return True
                    
                elif response.status_code == 404:
                    logger.warning(f"✗ File not found: {filename}")
                    return False
                    
                else:
                    logger.warning(f"✗ HTTP {response.status_code} for {filename}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"✗ Network error downloading {filename}: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"✗ Invalid JSON in {filename}: {e}")
            except Exception as e:
                logger.error(f"✗ Unexpected error downloading {filename}: {e}")
            
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return False
    
    def download_names_data(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[int, bool]:
        """
        Download names ranking data (n_YYYY.json files).
        
        Args:
            start_year: Start year (default: 1912)
            end_year: End year (default: current year)
            
        Returns:
            Dictionary mapping year to download success status
        """
        start_year = start_year or self.names_start_year
        end_year = end_year or self.current_year
        
        logger.info(f"Downloading names data from {start_year} to {end_year}")
        
        results = {}
        successful_downloads = 0
        
        for year in range(start_year, end_year + 1):
            filename = f"n_{year}.json"
            save_path = self.output_dir / "names" / filename
            
            if save_path.exists():
                logger.info(f"⚪ Skipping {filename} (already exists)")
                results[year] = True
                successful_downloads += 1
                continue
            
            success = self.download_file(filename, save_path)
            results[year] = success
            
            if success:
                successful_downloads += 1
            
            time.sleep(0.5)  # Be respectful to the server
        
        logger.info(f"Names data download complete: {successful_downloads}/{len(results)} files")
        return results
    
    def download_readings_data(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[int, bool]:
        """
        Download readings ranking data (y_YYYY.json files).
        
        Args:
            start_year: Start year (default: 2004)
            end_year: End year (default: current year)
            
        Returns:
            Dictionary mapping year to download success status
        """
        start_year = start_year or self.readings_start_year
        end_year = end_year or self.current_year
        
        logger.info(f"Downloading readings data from {start_year} to {end_year}")
        
        results = {}
        successful_downloads = 0
        
        for year in range(start_year, end_year + 1):
            filename = f"y_{year}.json"
            save_path = self.output_dir / "readings" / filename
            
            if save_path.exists():
                logger.info(f"⚪ Skipping {filename} (already exists)")
                results[year] = True
                successful_downloads += 1
                continue
            
            success = self.download_file(filename, save_path)
            results[year] = success
            
            if success:
                successful_downloads += 1
            
            time.sleep(0.5)  # Be respectful to the server
        
        logger.info(f"Readings data download complete: {successful_downloads}/{len(results)} files")
        return results
    
    def download_additional_data(self) -> Dict[str, bool]:
        """Download additional ranking data files."""
        additional_files = [
            "nameListKanji.json",  # Kanji rankings  
            "index_name.json",     # Name index
            "index_yomi.json",     # Reading index
            "searchSuggest.json",  # Search suggestions
            "topics.json"          # Topics data
        ]
        
        logger.info("Downloading additional data files")
        results = {}
        
        for filename in additional_files:
            save_path = self.output_dir / filename
            success = self.download_file(filename, save_path)
            results[filename] = success
            time.sleep(0.5)
        
        return results
    
    def process_names_file(self, year: int) -> Optional[pd.DataFrame]:
        """Process a names JSON file into a structured DataFrame."""
        file_path = self.output_dir / "names" / f"n_{year}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['year'] = year
            df['data_type'] = 'names'
            
            # Standardize column names based on JavaScript analysis
            # Expected fields: name, yomi, rank, sex, code
            if 'sex' in df.columns:
                df['gender'] = df['sex'].map({'m': 'male', 'f': 'female'})
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing names file for {year}: {e}")
            return None
    
    def process_readings_file(self, year: int) -> Optional[pd.DataFrame]:
        """Process a readings JSON file into a structured DataFrame."""
        file_path = self.output_dir / "readings" / f"y_{year}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['year'] = year
            df['data_type'] = 'readings'
            
            # Standardize column names
            if 'sex' in df.columns:
                df['gender'] = df['sex'].map({'m': 'male', 'f': 'female'})
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing readings file for {year}: {e}")
            return None
    
    def create_combined_dataset(self) -> pd.DataFrame:
        """Create a combined dataset from all downloaded files."""
        logger.info("Creating combined dataset")
        
        all_data = []
        
        # Process names files
        names_dir = self.output_dir / "names"
        for file_path in names_dir.glob("n_*.json"):
            try:
                year = int(file_path.stem.split('_')[1])
                df = self.process_names_file(year)
                if df is not None:
                    all_data.append(df)
            except ValueError:
                continue
        
        # Process readings files
        readings_dir = self.output_dir / "readings"
        for file_path in readings_dir.glob("y_*.json"):
            try:
                year = int(file_path.stem.split('_')[1])
                df = self.process_readings_file(year)
                if df is not None:
                    all_data.append(df)
            except ValueError:
                continue
        
        if not all_data:
            logger.warning("No data files found to combine")
            return pd.DataFrame()
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save combined dataset
        output_path = self.output_dir / "processed" / "combined_rankings.csv"
        combined_df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Combined dataset saved to {output_path}")
        
        # Save as Excel for easier viewing
        excel_path = self.output_dir / "processed" / "combined_rankings.xlsx"
        combined_df.to_excel(excel_path, index=False)
        logger.info(f"Combined dataset saved to {excel_path}")
        
        return combined_df
    
    def generate_summary_report(self, df: pd.DataFrame) -> Dict:
        """Generate a summary report of the collected data."""
        if df.empty:
            return {"error": "No data available"}
        
        summary = {
            "total_records": len(df),
            "years_covered": {
                "names": sorted(df[df['data_type'] == 'names']['year'].unique().tolist()),
                "readings": sorted(df[df['data_type'] == 'readings']['year'].unique().tolist())
            },
            "gender_distribution": df['gender'].value_counts().to_dict() if 'gender' in df.columns else {},
            "data_types": df['data_type'].value_counts().to_dict(),
            "columns": df.columns.tolist(),
            "sample_data": df.head().to_dict('records')
        }
        
        # Save summary
        summary_path = self.output_dir / "processed" / "summary_report.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Summary report saved to {summary_path}")
        return summary
    
    def run_full_scrape(self) -> Dict:
        """Run the complete scraping process."""
        logger.info("Starting full scrape of Meiji Yasuda baby names data")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "names_data": {},
            "readings_data": {},
            "additional_data": {},
            "summary": {}
        }
        
        try:
            # Download all data
            results["names_data"] = self.download_names_data()
            results["readings_data"] = self.download_readings_data()
            results["additional_data"] = self.download_additional_data()
            
            # Process and combine data
            combined_df = self.create_combined_dataset()
            results["summary"] = self.generate_summary_report(combined_df)
            
            results["end_time"] = datetime.now().isoformat()
            results["status"] = "completed"
            
            # Save results
            results_path = self.output_dir / "scrape_results.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info("Full scrape completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during full scrape: {e}")
            results["error"] = str(e)
            results["status"] = "failed"
        
        return results

def main():
    """Main function to run the scraper."""
    print("Meiji Yasuda Baby Names Scraper")
    print("=" * 50)
    
    scraper = MeijiYasudaScraper()
    
    # Run the full scraping process
    results = scraper.run_full_scrape()
    
    if results.get("status") == "completed":
        summary = results.get("summary", {})
        print(f"\n✓ Scraping completed successfully!")
        print(f"✓ Total records: {summary.get('total_records', 0)}")
        print(f"✓ Names data years: {len(summary.get('years_covered', {}).get('names', []))}")
        print(f"✓ Readings data years: {len(summary.get('years_covered', {}).get('readings', []))}")
        print(f"✓ Data saved to: {scraper.output_dir}")
    else:
        print(f"\n✗ Scraping failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
