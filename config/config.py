"""
Configuration management for the solar leads system.
Loads environment variables and provides centralized configuration access.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DATA_DIR = DATA_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [CONFIG_DIR, RAW_DATA_DIR, OUTPUT_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """Central configuration class"""
    
    # Firebase/Firestore
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        str(CONFIG_DIR / "firebase-credentials.json")
    )
    FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")
    
    # Geocoding
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    GEOCODIO_API_KEY = os.getenv("GEOCODIO_API_KEY")
    
    # OpenStreetMap
    OVERPASS_API_URL = os.getenv(
        "OVERPASS_API_URL",
        "https://overpass-api.de/api/interpreter"
    )
    
    # Data sources
    ASSESSOR_DATA_URL = os.getenv("ASSESSOR_DATA_URL")
    ASSESSOR_API_KEY = os.getenv("ASSESSOR_API_KEY")
    BUSINESS_DATA_URL = os.getenv("BUSINESS_DATA_URL")
    BUSINESS_API_KEY = os.getenv("BUSINESS_API_KEY")
    
    # Processing configuration
    GEOCODING_BATCH_SIZE = int(os.getenv("GEOCODING_BATCH_SIZE", "100"))
    GEOCODING_RATE_LIMIT = int(os.getenv("GEOCODING_RATE_LIMIT", "50"))
    DEDUPLICATION_DISTANCE_THRESHOLD = float(
        os.getenv("DEDUPLICATION_DISTANCE_THRESHOLD", "20")
    )
    
    # Scoring configuration
    MIN_ROOF_AREA = int(os.getenv("MIN_ROOF_AREA", "2000"))
    MIN_SCORE_THRESHOLD = int(os.getenv("MIN_SCORE_THRESHOLD", "40"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "solar_leads.log"))
    
    # Upstate NY regions (counties)
    UPSTATE_NY_COUNTIES = [
        "Monroe", "Erie", "Onondaga", "Albany", "Niagara",
        "Oneida", "Broome", "Dutchess", "Orange", "Saratoga",
        "Rensselaer", "Chautauqua", "Oswego", "Jefferson",
        "Schenectady", "Sullivan", "Tompkins", "Chemung"
    ]
    
    # Upstate NY bounding box (for OSM queries)
    UPSTATE_NY_BBOX = {
        "south": 41.5,
        "west": -79.8,
        "north": 45.0,
        "east": -73.3
    }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        required_fields = [
            ("FIRESTORE_PROJECT_ID", cls.FIRESTORE_PROJECT_ID),
            ("FIREBASE_CREDENTIALS_PATH", cls.FIREBASE_CREDENTIALS_PATH),
        ]
        
        missing = []
        for name, value in required_fields:
            if not value:
                missing.append(name)
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please check your .env file."
            )
        
        # Check if Firebase credentials file exists
        if not Path(cls.FIREBASE_CREDENTIALS_PATH).exists():
            raise FileNotFoundError(
                f"Firebase credentials file not found at: {cls.FIREBASE_CREDENTIALS_PATH}"
            )
        
        return True
    
    @classmethod
    def get_geocoding_api_key(cls) -> Optional[str]:
        """Get available geocoding API key"""
        return cls.GOOGLE_MAPS_API_KEY or cls.GEOCODIO_API_KEY


# Scoring weights and thresholds
SCORING_WEIGHTS = {
    "building_type": 30,
    "roof_area": 25,
    "ownership": 20,
    "energy_indicators": 15,
    "property_value": 10
}

# Building type scores
BUILDING_TYPE_SCORES = {
    "industrial": 30,
    "warehouse": 28,
    "commercial": 25,
    "retail": 22,
    "office": 20,
    "mixed_use": 15,
    "institutional": 12,
    "residential": 0
}

# Roof area score thresholds (sqft)
ROOF_AREA_THRESHOLDS = [
    (50000, 25),
    (25000, 20),
    (10000, 15),
    (5000, 10),
    (2000, 5),
    (0, 0)
]

# High energy use NAICS codes (first 2 digits)
HIGH_ENERGY_NAICS = [
    "31",  # Manufacturing
    "32",  # Manufacturing
    "33",  # Manufacturing
    "42",  # Wholesale Trade
    "44",  # Retail Trade
    "45",  # Retail Trade
    "48",  # Transportation and Warehousing
    "49",  # Transportation and Warehousing
    "62",  # Health Care
    "71",  # Arts, Entertainment, and Recreation
    "72",  # Accommodation and Food Services
]

MEDIUM_ENERGY_NAICS = [
    "51",  # Information
    "52",  # Finance and Insurance
    "53",  # Real Estate
    "54",  # Professional Services
    "56",  # Administrative Services
    "61",  # Educational Services
]
