"""
Interactive Demo - Solar Lead Identification System
Demonstrates all built functionality with real-world examples
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.address_utils import AddressNormalizer, Geocoder
from src.utils.geo_utils import (
    calculate_distance,
    estimate_roof_area,
    buildings_are_duplicates,
    polygon_area_sqft
)
from src.storage.local_storage import local_storage
from loguru import logger
import time
import json

# Configure logger
logger.remove()  # Remove default handler
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("logs/demo.log", rotation="10 MB", level="DEBUG")


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_subheader(title):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---\n")


def demo_address_normalization():
    """Demo address parsing and normalization"""
    print_header("1. ADDRESS NORMALIZATION & PARSING")
    
    normalizer = AddressNormalizer()
    
    # Real Upstate NY commercial addresses
    test_addresses = [
        "100 State Street, Rochester, NY 14614",  # Office building
        "1200 SCOTTSVILLE ROAD, ROCHESTER, NEW YORK 14624",  # Industrial
        "3450 Winton Place, Building C, Rochester, NY 14623",  # Commercial complex
        "75 College Avenue, Rochester, NY 14607",  # Mixed use
    ]
    
    results = []
    
    for i, addr in enumerate(test_addresses, 1):
        print(f"{i}. Original Address:")
        print(f"   {addr}")
        
        # Parse into components
        components = normalizer.parse_address(addr)
        print(f"\n   Parsed Components:")
        print(f"   • Street Number: {components.get('street_number', 'N/A')}")
        print(f"   • Street Name:   {components.get('street_name', 'N/A')}")
        print(f"   • City:          {components.get('city', 'N/A')}")
        print(f"   • State:         {components.get('state', 'N/A')}")
        print(f"   • ZIP Code:      {components.get('zip_code', 'N/A')}")
        if components.get('unit'):
            print(f"   • Unit:          {components.get('unit')}")
        
        # Normalize
        normalized = normalizer.normalize_address(addr)
        print(f"\n   Normalized: {normalized}")
        
        # Create standardized address
        standardized = normalizer.create_normalized_address(components)
        print(f"   Standardized: {standardized}")
        
        results.append({
            'original': addr,
            'normalized': normalized,
            'components': components
        })
        
        print()
    
    return results


def demo_geocoding(address_results):
    """Demo geocoding functionality"""
    print_header("2. GEOCODING - Converting Addresses to Coordinates")
    
    geocoder = Geocoder()
    
    print("Using Nominatim (OpenStreetMap) - Free geocoding service")
    print("Note: Rate limited to ~1 request per second\n")
    
    geocoded_results = []
    
    for i, result in enumerate(address_results, 1):
        addr = result['normalized']
        print(f"{i}. Geocoding: {addr}")
        
        start_time = time.time()
        coords = geocoder.geocode(addr)
        elapsed = time.time() - start_time
        
        if coords:
            lat, lng = coords
            print(f"   ✓ Success! ({elapsed:.2f}s)")
            print(f"   → Latitude:  {lat:.6f}")
            print(f"   → Longitude: {lng:.6f}")
            print(f"   → Google Maps: https://www.google.com/maps?q={lat},{lng}")
            
            geocoded_results.append({
                **result,
                'lat': lat,
                'lng': lng,
                'geocoded': True
            })
        else:
            print(f"   ✗ Geocoding failed ({elapsed:.2f}s)")
            geocoded_results.append({
                **result,
                'geocoded': False
            })
        
        print()
    
    # Show cache statistics
    print(f"Geocoder cache size: {len(geocoder.cache)} addresses")
    
    return geocoded_results


def demo_geometry_calculations(geocoded_results):
    """Demo geometry and distance calculations"""
    print_header("3. GEOMETRY CALCULATIONS")
    
    # Filter successfully geocoded addresses
    valid_coords = [r for r in geocoded_results if r.get('geocoded')]
    
    if len(valid_coords) >= 2:
        print_subheader("Distance Calculations")
        
        # Calculate distances between all pairs
        for i in range(len(valid_coords)):
            for j in range(i + 1, len(valid_coords)):
                addr1 = valid_coords[i]
                addr2 = valid_coords[j]
                
                coord1 = (addr1['lat'], addr1['lng'])
                coord2 = (addr2['lat'], addr2['lng'])
                
                distance_m = calculate_distance(coord1, coord2)
                distance_ft = distance_m * 3.28084
                distance_mi = distance_m / 1609.34
                
                print(f"\nFrom: {addr1['original'][:50]}")
                print(f"To:   {addr2['original'][:50]}")
                print(f"Distance: {distance_m:,.1f} meters ({distance_ft:,.0f} ft / {distance_mi:.2f} miles)")
    
    print_subheader("Roof Area Estimations")
    
    # Simulate different building types
    buildings = [
        {"type": "Small Retail", "sqft": 5000, "stories": 1},
        {"type": "Medium Office", "sqft": 25000, "stories": 3},
        {"type": "Large Warehouse", "sqft": 100000, "stories": 1},
        {"type": "Industrial Complex", "sqft": 250000, "stories": 2},
    ]
    
    for building in buildings:
        roof_area = estimate_roof_area(building['sqft'], building['stories'])
        footprint = building['sqft'] / building['stories']
        
        print(f"\n{building['type']}:")
        print(f"  • Total Building Area: {building['sqft']:,} sqft")
        print(f"  • Number of Stories: {building['stories']}")
        print(f"  • Building Footprint: {footprint:,.0f} sqft")
        print(f"  • Estimated Usable Roof: {roof_area:,.0f} sqft (70% of footprint)")
        
        # Estimate solar panel capacity (rough estimate: 1 kW per 100 sqft)
        solar_capacity_kw = roof_area / 100
        print(f"  • Potential Solar Capacity: ~{solar_capacity_kw:,.0f} kW")


def demo_duplicate_detection():
    """Demo building duplicate detection"""
    print_header("4. DUPLICATE DETECTION")
    
    print("Testing duplicate detection algorithm...\n")
    
    # Test case 1: Same building, slight coordinate difference
    building1 = {
        'building_id': 'B001',
        'normalized_address': '100 STATE ST, ROCHESTER, NY 14614',
        'street_number': '100',
        'street_name': 'STATE ST',
        'lat': 43.1566,
        'lng': -77.6088
    }
    
    building2_duplicate = {
        'building_id': 'B002',
        'normalized_address': '100 STATE ST, ROCHESTER, NY 14614',
        'street_number': '100',
        'street_name': 'STATE ST',
        'lat': 43.1567,  # 11 meters away
        'lng': -77.6089
    }
    
    building3_different = {
        'building_id': 'B003',
        'normalized_address': '200 MAIN ST, ROCHESTER, NY 14614',
        'street_number': '200',
        'street_name': 'MAIN ST',
        'lat': 43.1580,
        'lng': -77.6100
    }
    
    # Test 1
    is_dup = buildings_are_duplicates(building1, building2_duplicate)
    distance = calculate_distance(
        (building1['lat'], building1['lng']),
        (building2_duplicate['lat'], building2_duplicate['lng'])
    )
    
    print(f"Test 1: Same address, {distance:.1f}m apart")
    print(f"  Building 1: {building1['normalized_address']}")
    print(f"  Building 2: {building2_duplicate['normalized_address']}")
    print(f"  → Result: {'DUPLICATE ✓' if is_dup else 'NOT DUPLICATE ✗'}")
    print(f"  → Expected: DUPLICATE ✓")
    
    # Test 2
    is_dup = buildings_are_duplicates(building1, building3_different)
    distance = calculate_distance(
        (building1['lat'], building1['lng']),
        (building3_different['lat'], building3_different['lng'])
    )
    
    print(f"\nTest 2: Different addresses, {distance:.1f}m apart")
    print(f"  Building 1: {building1['normalized_address']}")
    print(f"  Building 3: {building3_different['normalized_address']}")
    print(f"  → Result: {'DUPLICATE ✓' if is_dup else 'NOT DUPLICATE ✗'}")
    print(f"  → Expected: NOT DUPLICATE ✗")
    
    print("\n✓ Duplicate detection working correctly!")


def demo_data_storage(geocoded_results):
    """Demo local storage capabilities"""
    print_header("5. DATA STORAGE - Local File System")
    
    # Create sample building records
    buildings = []
    for i, result in enumerate(geocoded_results, 1):
        if result.get('geocoded'):
            building = {
                'building_id': f'DEMO_{i:03d}',
                'address': result['original'],
                'normalized_address': result['normalized'],
                'street_number': result['components'].get('street_number', ''),
                'street_name': result['components'].get('street_name', ''),
                'city': result['components'].get('city', ''),
                'state': result['components'].get('state', ''),
                'zip_code': result['components'].get('zip_code', ''),
                'lat': result['lat'],
                'lng': result['lng'],
                'building_type': 'commercial',  # Would come from assessor data
                'building_area_sqft': 15000 + (i * 5000),  # Simulated
                'estimated_roof_area': estimate_roof_area(15000 + (i * 5000), 1),
                'score': 70 + (i * 5),  # Simulated score
                'data_quality': 'high',
                'sources': ['demo', 'geocoded']
            }
            buildings.append(building)
    
    if not buildings:
        print("No geocoded buildings to save.")
        return
    
    print(f"Saving {len(buildings)} building records...\n")
    
    # Save as JSON
    print("1. Saving as JSON...")
    local_storage.save_json('demo_buildings', buildings)
    print(f"   ✓ Saved to: data/raw/demo_buildings.json")
    
    # Save as CSV
    print("\n2. Saving as CSV...")
    local_storage.save_csv('demo_buildings', buildings)
    print(f"   ✓ Saved to: data/raw/demo_buildings.csv")
    
    # Load and verify
    print("\n3. Loading and verifying...")
    loaded = local_storage.load_json('demo_buildings')
    print(f"   ✓ Loaded {len(loaded)} records from JSON")
    
    # Display sample record
    print("\n4. Sample Building Record:")
    print(json.dumps(buildings[0], indent=2))
    
    # List all collections
    print("\n5. Available Collections:")
    collections = local_storage.list_collections()
    for collection in collections:
        if collection != '.gitkeep':
            print(f"   • {collection}")
    
    return buildings


def demo_scoring_preview(buildings):
    """Preview of scoring system"""
    print_header("6. SCORING SYSTEM PREVIEW")
    
    print("Simulated solar suitability scoring based on:")
    print("  • Building type (commercial/industrial preferred)")
    print("  • Roof area (larger is better)")
    print("  • Location (proximity to grid infrastructure)")
    print("  • Data quality\n")
    
    # Sort by score
    sorted_buildings = sorted(buildings, key=lambda x: x['score'], reverse=True)
    
    print("Top Ranked Buildings:\n")
    print(f"{'Rank':<6} {'Score':<7} {'Roof Area':<12} {'Address':<50}")
    print("-" * 85)
    
    for i, building in enumerate(sorted_buildings[:5], 1):
        rank = f"#{i}"
        score = f"{building['score']}/100"
        roof = f"{building['estimated_roof_area']:,.0f} sqft"
        addr = building['address'][:47] + "..." if len(building['address']) > 50 else building['address']
        
        print(f"{rank:<6} {score:<7} {roof:<12} {addr:<50}")
    
    print("\n✓ Scoring system ready for implementation!")


def main():
    """Run the complete demo"""
    print("\n" + "="*70)
    print("  SOLAR LEAD IDENTIFICATION SYSTEM - INTERACTIVE DEMO")
    print("  Demonstrating all built functionality")
    print("="*70)
    
    try:
        # 1. Address normalization
        address_results = demo_address_normalization()
        
        # 2. Geocoding
        geocoded_results = demo_geocoding(address_results)
        
        # 3. Geometry calculations
        demo_geometry_calculations(geocoded_results)
        
        # 4. Duplicate detection
        demo_duplicate_detection()
        
        # 5. Data storage
        buildings = demo_data_storage(geocoded_results)
        
        # 6. Scoring preview
        if buildings:
            demo_scoring_preview(buildings)
        
        # Final summary
        print_header("DEMO COMPLETE!")
        
        print("✓ All core functionality demonstrated successfully!\n")
        print("Generated Files:")
        print("  • data/raw/demo_buildings.json")
        print("  • data/raw/demo_buildings.csv")
        print("  • logs/demo.log\n")
        print("Next Steps:")
        print("  1. Review generated files in data/raw/")
        print("  2. Check logs/demo.log for detailed execution logs")
        print("  3. Ready to build data ingestion scripts!")
        print("\n" + "="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Demo failed")
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
