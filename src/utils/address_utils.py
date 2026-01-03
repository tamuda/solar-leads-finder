"""
Utility functions for address normalization and geocoding.
"""

import re
from typing import Dict, Optional, Tuple
import usaddress
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from loguru import logger


class AddressNormalizer:
    """Normalize and standardize addresses"""
    
    @staticmethod
    def parse_address(address_string: str) -> Dict[str, str]:
        """
        Parse an address string into components using usaddress.
        
        Args:
            address_string: Raw address string
        
        Returns:
            Dictionary of address components
        """
        try:
            parsed, address_type = usaddress.tag(address_string)
            
            # Map usaddress tags to our schema
            normalized = {
                'street_number': parsed.get('AddressNumber', ''),
                'street_name': ' '.join([
                    parsed.get('StreetNamePreDirectional', ''),
                    parsed.get('StreetName', ''),
                    parsed.get('StreetNamePostType', ''),
                    parsed.get('StreetNamePostDirectional', '')
                ]).strip(),
                'city': parsed.get('PlaceName', ''),
                'state': parsed.get('StateName', ''),
                'zip_code': parsed.get('ZipCode', ''),
                'unit': parsed.get('OccupancyIdentifier', '')
            }
            
            return normalized
        except Exception as e:
            logger.warning(f"Failed to parse address '{address_string}': {e}")
            return {}
    
    @staticmethod
    def normalize_address(address_string: str) -> str:
        """
        Normalize an address to a standard format.
        
        Args:
            address_string: Raw address string
        
        Returns:
            Normalized address string
        """
        if not address_string:
            return ""
        
        # Clean up the address
        address = address_string.strip().upper()
        
        # Common abbreviations
        replacements = {
            r'\bSTREET\b': 'ST',
            r'\bAVENUE\b': 'AVE',
            r'\bROAD\b': 'RD',
            r'\bBOULEVARD\b': 'BLVD',
            r'\bDRIVE\b': 'DR',
            r'\bLANE\b': 'LN',
            r'\bCOURT\b': 'CT',
            r'\bCIRCLE\b': 'CIR',
            r'\bPLACE\b': 'PL',
            r'\bNORTH\b': 'N',
            r'\bSOUTH\b': 'S',
            r'\bEAST\b': 'E',
            r'\bWEST\b': 'W',
        }
        
        for pattern, replacement in replacements.items():
            address = re.sub(pattern, replacement, address)
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address)
        
        return address.strip()
    
    @staticmethod
    def create_normalized_address(components: Dict[str, str]) -> str:
        """
        Create a normalized address string from components.
        
        Args:
            components: Dictionary of address components
        
        Returns:
            Normalized address string
        """
        parts = []
        
        if components.get('street_number'):
            parts.append(components['street_number'])
        if components.get('street_name'):
            parts.append(components['street_name'])
        if components.get('unit'):
            parts.append(f"Unit {components['unit']}")
        if components.get('city'):
            parts.append(components['city'])
        if components.get('state'):
            parts.append(components['state'])
        if components.get('zip_code'):
            parts.append(components['zip_code'])
        
        return ', '.join(parts).upper()


class Geocoder:
    """Geocode addresses to lat/lng coordinates"""
    
    def __init__(self, user_agent: str = "solar-leads-geocoder"):
        """Initialize geocoder with Nominatim (OpenStreetMap)"""
        self.geolocator = Nominatim(user_agent=user_agent)
        self.cache = {}
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
    
    def geocode(
        self,
        address: str,
        use_cache: bool = True
    ) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to lat/lng coordinates.
        
        Args:
            address: Address string to geocode
            use_cache: Whether to use cached results
        
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not address:
            return None
        
        # Check cache
        if use_cache and address in self.cache:
            logger.debug(f"Cache hit for address: {address}")
            return self.cache[address]
        
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        try:
            location = self.geolocator.geocode(address, timeout=10)
            self.last_request_time = time.time()
            
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[address] = coords
                logger.debug(f"Geocoded '{address}' to {coords}")
                return coords
            else:
                logger.warning(f"No geocoding result for: {address}")
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected geocoding error for '{address}': {e}")
            return None
    
    def batch_geocode(
        self,
        addresses: list,
        progress_callback=None
    ) -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocode multiple addresses.
        
        Args:
            addresses: List of address strings
            progress_callback: Optional callback function for progress updates
        
        Returns:
            Dictionary mapping addresses to coordinates
        """
        results = {}
        total = len(addresses)
        
        for i, address in enumerate(addresses):
            results[address] = self.geocode(address)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
