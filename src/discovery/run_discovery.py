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

from src.discovery.discovery_manager import DiscoveryManager

def run_targeted_search(cities=["Rochester", "Buffalo", "Syracuse", "Albany"], icp_limit=20, mode="auto"):
    """
    Discover and enrich leads based on ICP criteria using multiple strategies.
    mode: 'auto' (smart rotation), 'seed' (only seeds), 'full' (everything)
    """
    
    ingestor = OSMIngeestor()
    manager = DiscoveryManager()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in environment")
        return

    places_enricher = PlacesEnricher(api_key)
    solar_enricher = SolarEnricher(api_key)

    all_discovered = []
    
    # --- Strategy A: High Value Seeds (Always check if file exists) ---
    seed_file = Path('data/raw/high_value_seeds.json')
    if seed_file.exists():
        logger.info("Loading high-value seeds...")
        with open(seed_file, 'r') as f:
            seeds = json.load(f)
            for s in seeds:
                s['osm_id'] = f"SEED_{hash(s['address'])}" # Mock OSM ID
                all_discovered.append(s)

    # --- Strategy B: Smart Text Discovery (The "Daily Growth" Engine) ---
    if mode == "auto" or mode == "full":
        # Get 5 fresh queries that haven't been run recently
        smart_queries = manager.get_next_search_queries(count=5)
        
        for q_text, city in smart_queries:
            logger.info(f"--- Smart Discovery: '{q_text}' ---")
            
            # Bias towards the city center if known
            loc = None
            if city in CITY_BBOXES:
                b = CITY_BBOXES[city]
                loc = ((b[0]+b[2])/2, (b[1]+b[3])/2)

            results = places_enricher.text_search(q_text, location=loc)
            logger.info(f"Found {len(results)} matches for '{q_text}'")
            
            for res in results:
                all_discovered.append({
                    'osm_id': f"SMART_{res['place_id']}",
                    'address': res.get('formatted_address', res.get('vicinity')),
                    'lat': res.get('geometry', {}).get('location', {}).get('lat'),
                    'lng': res.get('geometry', {}).get('location', {}).get('lng'),
                    'building_type': 'church' if 'church' in q_text.lower() else 'industrial',
                    'business_name': res.get('name'),
                    'sources': ['smart_discovery', q_text]
                })
            time.sleep(1) # Be gentle with API
            
        # Save history so we don't repeat these tomorrow
        manager.save_history()

    # --- Strategy C: OSM Bbox Discovery (Only run if explicitly requested or 'full') ---
    if mode == "full": 
        for city in cities:
            if city not in CITY_BBOXES: continue
            
            logger.info(f"--- OSM Discovery in {city} ---")
            bbox = CITY_BBOXES[city]
            try:
                leads = ingestor.query_by_bbox(*bbox, limit=icp_limit)
                for lead in leads:
                    lead['address_city'] = city
                    all_discovered.append(lead)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed OSM query for {city}: {e}")

    # De-duplicate by address
    seen = {}
    unique_discovered = []
    for d in all_discovered:
        addr = d.get('address')
        if not addr or addr.lower() in seen: continue
        seen[addr.lower()] = True
        unique_discovered.append(d)

    logger.info(f"Total Unique Discovered: {len(unique_discovered)}. Starting enrichment...")

    # 2. Enrichment Phase
    formatted_leads = []
    for d in unique_discovered:
        formatted_leads.append({
            'building_id': d.get('osm_id', f"DISCO_{hash(d['address'])}"),
            'address': d['address'],
            'lat': d.get('lat'),
            'lng': d.get('lng'),
            'business_name': d.get('business_name'),
            'building_type': d.get('building_type', 'industrial'),
            'estimated_roof_area': 0,
            'sources': d.get('sources', ['mixed_discovery'])
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
    for i, lead in enumerate(qualified_leads[:30], 1):
        bucket = lead.get('icp_bucket', 'General')
        name = lead.get('business_name') or lead.get('address')
        score = lead.get('enriched_score', 0)
        panels = lead.get('solar_max_panels', 0)
        print(f"#{i:<2} [{score:>2} pts] {bucket:<30} | {name[:40]}")

if __name__ == "__main__":
    # Run a broad discovery across all target cities with a mix of strategies
    run_targeted_search(cities=["Rochester", "Buffalo", "Syracuse", "Albany"], icp_limit=15)
