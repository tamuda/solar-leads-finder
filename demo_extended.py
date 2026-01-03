"""
Extended Demo - Solar Lead Identification System
Tests with 20 real commercial/industrial addresses in Upstate NY
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.address_utils import AddressNormalizer, Geocoder
from src.utils.geo_utils import (
    calculate_distance,
    estimate_roof_area,
    buildings_are_duplicates
)
from src.storage.local_storage import local_storage
from loguru import logger
import time
import json
from tqdm import tqdm

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("logs/extended_demo.log", rotation="10 MB", level="DEBUG")


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


# Real commercial/industrial addresses in Upstate NY
UPSTATE_NY_ADDRESSES = [
    # Rochester - Downtown/Commercial
    ("100 State Street, Rochester, NY 14614", "office", 45000, 8),
    ("1 Bausch & Lomb Place, Rochester, NY 14604", "office", 120000, 12),
    ("260 East Avenue, Rochester, NY 14604", "office", 85000, 10),
    ("400 Andrews Street, Rochester, NY 14604", "industrial", 200000, 3),
    
    # Rochester - Industrial/Warehouse
    ("1200 Scottsville Road, Rochester, NY 14624", "warehouse", 150000, 1),
    ("100 Midtown Plaza, Rochester, NY 14604", "retail", 250000, 4),
    ("1 Xerox Square, Rochester, NY 14604", "office", 180000, 15),
    ("3450 Winton Place, Rochester, NY 14623", "commercial", 75000, 2),
    
    # Rochester - Suburban Commercial
    ("75 College Avenue, Rochester, NY 14607", "mixed_use", 35000, 3),
    ("2000 Winton Road South, Rochester, NY 14618", "retail", 95000, 2),
    ("1000 Elmwood Avenue, Rochester, NY 14620", "institutional", 125000, 4),
    
    # Buffalo - Commercial/Industrial
    ("1 Seneca Street, Buffalo, NY 14203", "office", 110000, 12),
    ("500 Pearl Street, Buffalo, NY 14202", "office", 95000, 10),
    ("1000 Niagara Street, Buffalo, NY 14213", "industrial", 175000, 2),
    ("95 Perry Street, Buffalo, NY 14203", "warehouse", 140000, 1),
    
    # Syracuse - Commercial
    ("100 Clinton Square, Syracuse, NY 13202", "office", 80000, 8),
    ("500 South Warren Street, Syracuse, NY 13202", "office", 65000, 6),
    ("1 Webster's Landing, Syracuse, NY 13202", "mixed_use", 55000, 4),
    
    # Albany - Government/Commercial
    ("1 Commerce Plaza, Albany, NY 12260", "office", 150000, 18),
    ("625 Broadway, Albany, NY 12207", "office", 72000, 7),
]


def run_extended_demo():
    """Run comprehensive demo with 20 addresses"""
    
    print_header("EXTENDED DEMO - 20 Commercial Buildings in Upstate NY")
    
    print(f"Testing with {len(UPSTATE_NY_ADDRESSES)} real commercial/industrial addresses")
    print("Locations: Rochester, Buffalo, Syracuse, Albany\n")
    
    normalizer = AddressNormalizer()
    geocoder = Geocoder()
    
    # Step 1: Parse and normalize all addresses
    print_header("Step 1: Address Normalization")
    
    normalized_data = []
    for i, (address, building_type, sqft, stories) in enumerate(UPSTATE_NY_ADDRESSES, 1):
        components = normalizer.parse_address(address)
        normalized = normalizer.normalize_address(address)
        
        normalized_data.append({
            'id': i,
            'original': address,
            'normalized': normalized,
            'components': components,
            'building_type': building_type,
            'building_area_sqft': sqft,
            'num_stories': stories
        })
        
        if i <= 5:  # Show first 5 in detail
            print(f"{i}. {address}")
            print(f"   → {normalized}")
    
    print(f"\n... and {len(UPSTATE_NY_ADDRESSES) - 5} more addresses")
    print(f"✓ Normalized {len(normalized_data)} addresses\n")
    
    # Step 2: Geocode all addresses
    print_header("Step 2: Geocoding All Addresses")
    
    print("This will take ~1-2 minutes due to rate limiting...")
    print("Using Nominatim (free OpenStreetMap geocoding)\n")
    
    geocoded_data = []
    successful = 0
    failed = 0
    
    # Use tqdm for progress bar
    for data in tqdm(normalized_data, desc="Geocoding", unit="address"):
        coords = geocoder.geocode(data['normalized'])
        
        if coords:
            lat, lng = coords
            data['lat'] = lat
            data['lng'] = lng
            data['geocoded'] = True
            successful += 1
        else:
            data['geocoded'] = False
            failed += 1
        
        geocoded_data.append(data)
    
    print(f"\n✓ Geocoding complete!")
    print(f"  • Successful: {successful}/{len(normalized_data)} ({successful/len(normalized_data)*100:.1f}%)")
    print(f"  • Failed: {failed}/{len(normalized_data)}")
    print(f"  • Cache size: {len(geocoder.cache)} addresses\n")
    
    # Step 3: Calculate roof areas and solar potential
    print_header("Step 3: Roof Area & Solar Capacity Estimation")
    
    total_roof_area = 0
    total_solar_capacity = 0
    
    for data in geocoded_data:
        roof_area = estimate_roof_area(data['building_area_sqft'], data['num_stories'])
        solar_capacity = roof_area / 100  # ~1 kW per 100 sqft
        
        data['estimated_roof_area'] = roof_area
        data['solar_capacity_kw'] = solar_capacity
        
        total_roof_area += roof_area
        total_solar_capacity += solar_capacity
    
    print(f"Total Estimated Usable Roof Area: {total_roof_area:,.0f} sqft")
    print(f"Total Potential Solar Capacity: {total_solar_capacity:,.0f} kW")
    print(f"Average per Building: {total_roof_area/len(geocoded_data):,.0f} sqft / {total_solar_capacity/len(geocoded_data):.0f} kW\n")
    
    # Show top 5 by roof area
    sorted_by_roof = sorted(geocoded_data, key=lambda x: x['estimated_roof_area'], reverse=True)
    print("Top 5 Buildings by Roof Area:")
    print(f"{'Rank':<6} {'Roof Area':<15} {'Solar (kW)':<12} {'Address':<50}")
    print("-" * 90)
    for i, building in enumerate(sorted_by_roof[:5], 1):
        print(f"#{i:<5} {building['estimated_roof_area']:>10,.0f} sqft  {building['solar_capacity_kw']:>8.0f} kW   {building['original'][:47]}...")
    
    # Step 4: Assign scores
    print_header("Step 4: Solar Suitability Scoring")
    
    # Scoring weights
    BUILDING_TYPE_SCORES = {
        'industrial': 30,
        'warehouse': 28,
        'commercial': 25,
        'retail': 22,
        'office': 20,
        'mixed_use': 15,
        'institutional': 12
    }
    
    for data in geocoded_data:
        score = 0
        breakdown = {}
        
        # Building type score (0-30)
        type_score = BUILDING_TYPE_SCORES.get(data['building_type'], 10)
        score += type_score
        breakdown['building_type'] = type_score
        
        # Roof area score (0-25)
        roof_area = data['estimated_roof_area']
        if roof_area >= 50000:
            roof_score = 25
        elif roof_area >= 25000:
            roof_score = 20
        elif roof_area >= 10000:
            roof_score = 15
        elif roof_area >= 5000:
            roof_score = 10
        else:
            roof_score = 5
        score += roof_score
        breakdown['roof_area'] = roof_score
        
        # Geocoding quality (0-20)
        geo_score = 20 if data['geocoded'] else 0
        score += geo_score
        breakdown['geocoding'] = geo_score
        
        # Data completeness (0-15)
        completeness = 15 if data['components'].get('street_number') else 10
        score += completeness
        breakdown['data_quality'] = completeness
        
        # Building size (0-10)
        if data['building_area_sqft'] >= 100000:
            size_score = 10
        elif data['building_area_sqft'] >= 50000:
            size_score = 7
        else:
            size_score = 5
        score += size_score
        breakdown['building_size'] = size_score
        
        data['score'] = score
        data['score_breakdown'] = breakdown
    
    # Show scoring distribution
    scores = [d['score'] for d in geocoded_data]
    print(f"Score Range: {min(scores)} - {max(scores)}")
    print(f"Average Score: {sum(scores)/len(scores):.1f}")
    print(f"Median Score: {sorted(scores)[len(scores)//2]}\n")
    
    # Top 10 ranked buildings
    sorted_by_score = sorted(geocoded_data, key=lambda x: x['score'], reverse=True)
    print("Top 10 Solar Lead Candidates:")
    print(f"{'Rank':<6} {'Score':<8} {'Type':<12} {'Roof Area':<15} {'Address':<45}")
    print("-" * 95)
    for i, building in enumerate(sorted_by_score[:10], 1):
        print(f"#{i:<5} {building['score']:<8} {building['building_type']:<12} {building['estimated_roof_area']:>10,.0f} sqft  {building['original'][:42]}...")
    
    # Step 5: Save to storage
    print_header("Step 5: Saving Results")
    
    # Create final building records
    buildings = []
    for data in geocoded_data:
        building = {
            'building_id': f'UNY_{data["id"]:03d}',
            'address': data['original'],
            'normalized_address': data['normalized'],
            'street_number': data['components'].get('street_number', ''),
            'street_name': data['components'].get('street_name', ''),
            'city': data['components'].get('city', ''),
            'state': data['components'].get('state', ''),
            'zip_code': data['components'].get('zip_code', ''),
            'lat': data.get('lat'),
            'lng': data.get('lng'),
            'building_type': data['building_type'],
            'building_area_sqft': data['building_area_sqft'],
            'num_stories': data['num_stories'],
            'estimated_roof_area': data['estimated_roof_area'],
            'solar_capacity_kw': data['solar_capacity_kw'],
            'score': data['score'],
            'score_breakdown': data['score_breakdown'],
            'geocoded': data['geocoded'],
            'data_quality': 'high' if data['geocoded'] else 'medium',
            'sources': ['extended_demo', 'manual_input']
        }
        buildings.append(building)
    
    # Save as JSON
    local_storage.save_json('upstate_ny_buildings', buildings)
    print(f"✓ Saved {len(buildings)} buildings to data/raw/upstate_ny_buildings.json")
    
    # Save as CSV
    local_storage.save_csv('upstate_ny_buildings', buildings)
    print(f"✓ Saved {len(buildings)} buildings to data/raw/upstate_ny_buildings.csv")
    
    # Save top leads only
    top_leads = sorted_by_score[:10]
    local_storage.save_csv('top_solar_leads', top_leads)
    print(f"✓ Saved top 10 leads to data/raw/top_solar_leads.csv")
    
    # Step 6: Summary statistics
    print_header("Summary Statistics")
    
    # By building type
    type_counts = {}
    for b in buildings:
        t = b['building_type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("Buildings by Type:")
    for btype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {btype.title():<15} {count:>2} buildings")
    
    # By city
    city_counts = {}
    for b in buildings:
        c = b['city']
        if c:
            city_counts[c] = city_counts.get(c, 0) + 1
    
    print("\nBuildings by City:")
    for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {city:<15} {count:>2} buildings")
    
    # Score distribution
    high_score = len([b for b in buildings if b['score'] >= 70])
    medium_score = len([b for b in buildings if 50 <= b['score'] < 70])
    low_score = len([b for b in buildings if b['score'] < 50])
    
    print("\nScore Distribution:")
    print(f"  • High Priority (70+):   {high_score} buildings")
    print(f"  • Medium Priority (50-69): {medium_score} buildings")
    print(f"  • Low Priority (<50):    {low_score} buildings")
    
    print_header("EXTENDED DEMO COMPLETE!")
    
    print(f"✓ Processed {len(buildings)} commercial/industrial buildings")
    print(f"✓ Geocoded {successful} addresses successfully")
    print(f"✓ Estimated {total_roof_area:,.0f} sqft of usable roof area")
    print(f"✓ Potential for {total_solar_capacity:,.0f} kW of solar capacity")
    print(f"\nGenerated Files:")
    print(f"  • data/raw/upstate_ny_buildings.json ({len(buildings)} records)")
    print(f"  • data/raw/upstate_ny_buildings.csv ({len(buildings)} records)")
    print(f"  • data/raw/top_solar_leads.csv (top 10 leads)")
    print(f"  • logs/extended_demo.log (detailed logs)")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        run_extended_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Extended demo failed")
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
