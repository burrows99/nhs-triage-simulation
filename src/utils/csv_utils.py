import csv
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


class CSVDataLoader:
    """Utility class for loading and managing CSV data"""
    
    def __init__(self, csv_directory: str):
        """
        Initialize CSV data loader
        
        Args:
            csv_directory: Path to directory containing CSV files
        """
        self.csv_directory = Path(csv_directory)
        self._data_cache: Dict[str, List[Dict[str, Any]]] = {}
        
    def load_csv_file(self, filename: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Load CSV file and return list of dictionaries
        
        Args:
            filename: Name of CSV file (with or without .csv extension)
            use_cache: Whether to use cached data if available
            
        Returns:
            List of dictionaries representing CSV rows
        """
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
            
        # Check cache first
        if use_cache and filename in self._data_cache:
            return self._data_cache[filename]
            
        file_path = self.csv_directory / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
            
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Clean up empty string values
                    cleaned_row = {k: (v if v != '' else None) for k, v in row.items()}
                    data.append(cleaned_row)
                    
            # Cache the data
            if use_cache:
                self._data_cache[filename] = data
                
            return data
            
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file {filename}: {str(e)}")
    
    def get_random_sample(self, filename: str, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get random sample from CSV data
        
        Args:
            filename: Name of CSV file
            sample_size: Number of records to sample (None for all)
            
        Returns:
            Random sample of CSV records
        """
        import random
        
        data = self.load_csv_file(filename)
        
        if sample_size is None or sample_size >= len(data):
            return data.copy()
            
        return random.sample(data, sample_size)
    
    def filter_records(self, filename: str, filter_func) -> List[Dict[str, Any]]:
        """
        Filter CSV records based on a function
        
        Args:
            filename: Name of CSV file
            filter_func: Function that takes a record dict and returns bool
            
        Returns:
            Filtered list of records
        """
        data = self.load_csv_file(filename)
        return [record for record in data if filter_func(record)]
    
    def get_unique_values(self, filename: str, column: str) -> List[Any]:
        """
        Get unique values from a specific column
        
        Args:
            filename: Name of CSV file
            column: Column name to get unique values from
            
        Returns:
            List of unique values
        """
        data = self.load_csv_file(filename)
        values = [record.get(column) for record in data if record.get(column) is not None]
        return list(set(values))
    
    def get_record_count(self, filename: str) -> int:
        """
        Get total number of records in CSV file
        
        Args:
            filename: Name of CSV file
            
        Returns:
            Number of records
        """
        data = self.load_csv_file(filename)
        return len(data)
    
    def clear_cache(self):
        """Clear the data cache"""
        self._data_cache.clear()
    
    def list_available_files(self) -> List[str]:
        """
        List all available CSV files in the directory
        
        Returns:
            List of CSV filenames
        """
        if not self.csv_directory.exists():
            return []
            
        return [f.name for f in self.csv_directory.glob('*.csv')]
    
    def get_column_names(self, filename: str) -> List[str]:
        """
        Get column names from CSV file
        
        Args:
            filename: Name of CSV file
            
        Returns:
            List of column names
        """
        if not filename.endswith('.csv'):
            filename += '.csv'
            
        file_path = self.csv_directory / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return reader.fieldnames or []