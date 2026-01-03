"""
Targeted Discovery & Enrichment Script
Finds real ICP leads (Churches, Warehouses, Industrial) in specific cities.
"""

import sys
import os
from pathlib import Path
import json
import time
from loguru import logger
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.ingest_osm import OSMIngeestor
from src.enrichment.enrich_data import PlacesEnricher, SolarEnricher, enrich_buildings, recalculate_scores
from src.storage.local_storage import local_storage

# Targeted cities with bounding boxes (south, west, north, east)
CITY_BBOXES = {
    "Rochester": (43.12, -77.67, 43.19, -77.56),
    "Buffalo": (42.85, -78.92, 42.94, -78.80),
    "Syracuse": (43.01, -76.20, 43.07, -76.10),
    "Albany": (42.62, -73.82, 42.69, -73.72)
}

def run_targeted_search(cities=["Rochester", "Buffalo", "Syracuse", "Albany"], icp_limit=20):
    """Discover and enrich leads based on ICP criteria using bbox for speed/accuracy"""
    
    ingestor = OSMIngeestor()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in environment")
        return

    places_enricher = PlacesEnricher(api_key)
    solar_enricher = SolarEnricher(api_key)

    all_discovered = []
    
    # 1. Discovery Phase
    for city in cities:
        if city not in CITY_BBOXES: continue
        
        logger.info(f"--- Discovering Leads in {city} ---")
        bbox = CITY_BBOXES[city]
        
        try:
            # Query the bbox with ICP filters
            leads = ingestor.query_by_bbox(*bbox, limit=icp_limit)
            for lead in leads:
                if not lead.get('address_city'):
                    lead['address_city'] = city
                all_discovered.append(lead)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Failed bbox query for {city}: {e}")
            
    logger.info(f"Discovered {len(all_discovered)} potential leads. Starting enrichment...")

    # 2. Enrichment Phase
    # We convert discovered leads to the format expected by the enricher
    formatted_leads = []
    for d in all_discovered:
        formatted_leads.append({
            'building_id': f"DISCO_{d['osm_id']}",
            'address': d['address'],
            'lat': d['lat'],
            'lng': d['lng'],
            'building_type': d['building_type'],
            'estimated_roof_area': 0, # To be determined by enrichment
            'sources': ['osm_discovery']
        })

    enriched_leads = enrich_buildings(formatted_leads, places_enricher, solar_enricher)
    
    # 3. Final Scoring & Persistence
    final_leads = recalculate_scores(enriched_leads)
    
    # Filter out ineligible
    qualified_leads = [b for b in final_leads if not b.get('ineligible', False)]
    
    # Save the specialized list
    local_storage.save_json('discovered_icp_leads', qualified_leads)
    local_storage.save_csv('discovered_icp_leads', qualified_leads)
    
    logger.info(f"Success! {len(qualified_leads)} leads qualified and saved to data/raw/discovered_icp_leads.csv")
    
    # Print a summary of findings
    print("\n" + "="*80)
    print(f" TARGETED DISCOVERY SUMMARY ({len(qualified_leads)} Leads Found)")
    print("="*80)
    for i, lead in enumerate(qualified_leads[:20], 1):
        bucket = lead.get('icp_bucket', 'General')
        name = lead.get('business_name') or lead.get('address')
        score = lead.get('enriched_score', 0)
        panels = lead.get('solar_max_panels', 0)
        print(f"#{i:<2} [{score:>2} pts] {bucket:<30} | {name[:40]}")

if __name__ == "__main__":
    # Target 15 potential buildings per city to find a good mix
    run_targeted_search(cities=["Rochester", "Buffalo", "Syracuse"], icp_limit=20)
