"""
OSM Ingestion module using Overpass API.
Finds commercial and industrial buildings in a specified area.
"""

import os
import sys
from pathlib import Path
import json
import requests
from typing import List, Dict, Any
from loguru import logger

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.local_storage import local_storage

class OSMIngeestor:
    """Ingest building data from OpenStreetMap via Overpass API"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    def __init__(self):
        pass
        
    def query_by_bbox(self, south: float, west: float, north: float, east: float, limit: int = 100) -> List[Dict[str, Any]]:
        """Query Overpass for buildings within a bounding box"""
        logger.info(f"Querying OSM for buildings in bbox [{south}, {west}, {north}, {east}]...")
        
        query = f"""
        [out:json][timeout:60];
        (
          way["building"~"commercial|industrial|warehouse|retail|office"]({south},{west},{north},{east});
          relation["building"~"commercial|industrial|warehouse|retail|office"]({south},{west},{north},{east});
        );
        out center body;
        """
        return self._execute_query(query, limit)

    def query_buildings(self, area_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query Overpass by area name"""
        logger.info(f"Querying OSM for buildings in {area_name}...")
        
        query = f"""
        [out:json][timeout:60];
        area[name="{area_name}"]->.searchArea;
        (
          way["building"~"commercial|industrial|warehouse|retail|office"](area.searchArea);
          relation["building"~"commercial|industrial|warehouse|retail|office"](area.searchArea);
        );
        out center body;
        """
        return self._execute_query(query, limit)

    def _execute_query(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Execute Overpass query and parse results"""
        try:
            response = requests.post(self.OVERPASS_URL, data={'data': query}, timeout=90)
            response.raise_for_status()
            data = response.json()
            
            elements = data.get('elements', [])
            logger.info(f"Found {len(elements)} buildings in OSM")
            
            buildings = []
            for element in elements[:limit]:
                center = element.get('center', {})
                lat = center.get('lat', element.get('lat'))
                lon = center.get('lon', element.get('lon'))
                
                tags = element.get('tags', {})
                
                building = {
                    'osm_id': element.get('id'),
                    'osm_type': element.get('type'),
                    'lat': lat,
                    'lng': lon,
                    'building_type': tags.get('building', 'unknown'),
                    'name': tags.get('name'),
                    'address_house_number': tags.get('addr:housenumber'),
                    'address_street': tags.get('addr:street'),
                    'address_city': tags.get('addr:city', 'Rochester'),
                    'address_postcode': tags.get('addr:postcode'),
                }
                
                if building['address_house_number'] and building['address_street']:
                    building['address'] = f"{building['address_house_number']} {building['address_street']}, {building['address_city']}, NY {building['address_postcode'] or ''}".strip(', ')
                else:
                    building['address'] = tags.get('addr:full') or building['name'] or f"OSM-{building['osm_id']}"
                
                buildings.append(building)
                
            return buildings
            
        except Exception as e:
            logger.error(f"Error querying Overpass: {e}")
            return []

def main():
    """Test OSM ingestion for a small area"""
    ingestor = OSMIngeestor()
    
    # Rochester, NY bounding box (Downtown)
    # south, west, north, east
    rochester_bbox = (43.14, -77.63, 43.17, -77.58)
    
    rochester_buildings = ingestor.query_by_bbox(*rochester_bbox, limit=50)
    
    if rochester_buildings:
        local_storage.save_json('osm_raw_rochester_ny', rochester_buildings)
        logger.info(f"Saved {len(rochester_buildings)} OSM buildings for Rochester, NY")
        
        print(f"\nExample OSM findings in Rochester, NY:")
        for b in rochester_buildings[:5]:
            print(f"- {b['name'] or 'Unnamed'} ({b['building_type']}): {b['address']}")
    else:
        logger.warning("No buildings found or query failed")

if __name__ == "__main__":
    main()
