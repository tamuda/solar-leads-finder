"""
Local storage implementation using CSV and JSON files.
This is used for testing before integrating with Firestore.
"""

import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from config.config import RAW_DATA_DIR, OUTPUT_DATA_DIR


class LocalStorage:
    """Local file-based storage for testing"""
    
    def __init__(self, data_dir: Path = RAW_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_collection_path(self, collection: str, format: str = 'json') -> Path:
        """Get the file path for a collection"""
        return self.data_dir / f"{collection}.{format}"
    
    # ===== JSON Operations =====
    
    def save_json(self, collection: str, data: List[Dict[str, Any]]) -> int:
        """Save data to JSON file"""
        filepath = self._get_collection_path(collection, 'json')
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(data)} records to {filepath}")
            return len(data)
        except Exception as e:
            logger.error(f"Error saving JSON to {filepath}: {e}")
            raise
    
    def load_json(self, collection: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        filepath = self._get_collection_path(collection, 'json')
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return []
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} records from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON from {filepath}: {e}")
            raise
    
    def append_json(self, collection: str, new_data: List[Dict[str, Any]]) -> int:
        """Append data to existing JSON file"""
        existing_data = self.load_json(collection)
        combined_data = existing_data + new_data
        return self.save_json(collection, combined_data)
    
    # ===== CSV Operations =====
    
    def save_csv(
        self,
        collection: str,
        data: List[Dict[str, Any]],
        fieldnames: Optional[List[str]] = None
    ) -> int:
        """Save data to CSV file"""
        filepath = self._get_collection_path(collection, 'csv')
        
        if not data:
            logger.warning("No data to save")
            return 0
        
        # Auto-detect fieldnames if not provided
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Saved {len(data)} records to {filepath}")
            return len(data)
        except Exception as e:
            logger.error(f"Error saving CSV to {filepath}: {e}")
            raise
    
    def load_csv(self, collection: str) -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        filepath = self._get_collection_path(collection, 'csv')
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return []
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            logger.info(f"Loaded {len(data)} records from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading CSV from {filepath}: {e}")
            raise
    
    # ===== Pandas Operations =====
    
    def save_dataframe(self, collection: str, df: pd.DataFrame, format: str = 'csv') -> int:
        """Save pandas DataFrame"""
        filepath = self._get_collection_path(collection, format)
        
        try:
            if format == 'csv':
                df.to_csv(filepath, index=False)
            elif format == 'json':
                df.to_json(filepath, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Saved DataFrame with {len(df)} records to {filepath}")
            return len(df)
        except Exception as e:
            logger.error(f"Error saving DataFrame to {filepath}: {e}")
            raise
    
    def load_dataframe(self, collection: str, format: str = 'csv') -> pd.DataFrame:
        """Load data as pandas DataFrame"""
        filepath = self._get_collection_path(collection, format)
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()
        
        try:
            if format == 'csv':
                df = pd.read_csv(filepath)
            elif format == 'json':
                df = pd.read_json(filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Loaded DataFrame with {len(df)} records from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading DataFrame from {filepath}: {e}")
            raise
    
    # ===== Utility Methods =====
    
    def list_collections(self) -> List[str]:
        """List all available collections"""
        collections = set()
        for filepath in self.data_dir.glob('*'):
            if filepath.is_file():
                collections.add(filepath.stem)
        return sorted(list(collections))
    
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection (all formats)"""
        deleted = False
        for format in ['json', 'csv']:
            filepath = self._get_collection_path(collection, format)
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted {filepath}")
                deleted = True
        return deleted
    
    def collection_exists(self, collection: str) -> bool:
        """Check if a collection exists"""
        return (
            self._get_collection_path(collection, 'json').exists() or
            self._get_collection_path(collection, 'csv').exists()
        )


# Singleton instance for local storage
local_storage = LocalStorage()
