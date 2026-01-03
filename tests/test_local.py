"""
Test script to verify utilities work locally before integrating Firebase.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.address_utils import AddressNormalizer, Geocoder
from src.utils.geo_utils import (
    calculate_distance,
    estimate_roof_area,
    buildings_are_duplicates
)
from src.storage.local_storage import local_storage
from loguru import logger

# Configure logger
logger.add(
    "logs/test.log",
    rotation="10 MB",
    level="DEBUG"
)


def test_address_normalization():
    """Test address parsing and normalization"""
    print("\n" + "="*60)
    print("Testing Address Normalization")
    print("="*60)
    
    test_addresses = [
        "123 Main Street, Rochester, NY 14604",
        "456 EAST AVENUE APT 2B, ROCHESTER, NEW YORK 14607",
        "789 West Henrietta Road, Rochester, NY 14623"
    ]
    
    normalizer = AddressNormalizer()
    
    for addr in test_addresses:
        print(f"\nOriginal: {addr}")
        
        # Parse address
        components = normalizer.parse_address(addr)
        print(f"Components: {components}")
        
        # Normalize
        normalized = normalizer.normalize_address(addr)
        print(f"Normalized: {normalized}")
        
        # Create from components
        reconstructed = normalizer.create_normalized_address(components)
        print(f"Reconstructed: {reconstructed}")


def test_geocoding():
    """Test geocoding functionality"""
    print("\n" + "="*60)
    print("Testing Geocoding")
    print("="*60)
    
    geocoder = Geocoder()
    
    test_addresses = [
        "City Hall, Rochester, NY",
        "University of Rochester, Rochester, NY",
        "123 Main St, Rochester, NY"
    ]
    
    for addr in test_addresses:
        print(f"\nGeocoding: {addr}")
        coords = geocoder.geocode(addr)
        if coords:
            print(f"  → Coordinates: {coords[0]:.6f}, {coords[1]:.6f}")
        else:
            print(f"  → Failed to geocode")


def test_geometry_utils():
    """Test geometry calculations"""
    print("\n" + "="*60)
    print("Testing Geometry Utilities")
    print("="*60)
    
    # Test distance calculation
    rochester_city_hall = (43.1566, -77.6088)
    u_of_rochester = (43.1292, -77.6299)
    
    distance = calculate_distance(rochester_city_hall, u_of_rochester)
    print(f"\nDistance between City Hall and U of R: {distance:.2f} meters ({distance * 3.28084:.2f} feet)")
    
    # Test roof area estimation
    building_sizes = [
        (10000, 1, "Single-story 10,000 sqft building"),
        (50000, 2, "Two-story 50,000 sqft building"),
        (100000, 5, "Five-story 100,000 sqft building")
    ]
    
    print("\nRoof Area Estimations:")
    for total_area, stories, description in building_sizes:
        roof_area = estimate_roof_area(total_area, stories)
        print(f"  {description}")
        print(f"    → Estimated roof area: {roof_area:,.0f} sqft")
    
    # Test duplicate detection
    print("\nDuplicate Detection:")
    building1 = {
        'lat': 43.1566,
        'lng': -77.6088,
        'normalized_address': '30 CHURCH ST, ROCHESTER, NY 14614',
        'street_number': '30',
        'street_name': 'CHURCH ST'
    }
    
    building2_same = {
        'lat': 43.1567,  # Very close
        'lng': -77.6089,
        'normalized_address': '30 CHURCH ST, ROCHESTER, NY 14614',
        'street_number': '30',
        'street_name': 'CHURCH ST'
    }
    
    building3_different = {
        'lat': 43.1292,
        'lng': -77.6299,
        'normalized_address': '500 WILSON BLVD, ROCHESTER, NY 14627',
        'street_number': '500',
        'street_name': 'WILSON BLVD'
    }
    
    is_dup_1_2 = buildings_are_duplicates(building1, building2_same)
    is_dup_1_3 = buildings_are_duplicates(building1, building3_different)
    
    print(f"  Building 1 vs Building 2 (same location): {is_dup_1_2}")
    print(f"  Building 1 vs Building 3 (different): {is_dup_1_3}")


def test_local_storage():
    """Test local storage operations"""
    print("\n" + "="*60)
    print("Testing Local Storage")
    print("="*60)
    
    # Create test data
    test_buildings = [
        {
            'building_id': 'test_001',
            'address': '123 Main St, Rochester, NY',
            'building_type': 'commercial',
            'building_area_sqft': 15000,
            'score': 75
        },
        {
            'building_id': 'test_002',
            'address': '456 East Ave, Rochester, NY',
            'building_type': 'industrial',
            'building_area_sqft': 50000,
            'score': 92
        },
        {
            'building_id': 'test_003',
            'address': '789 West Rd, Rochester, NY',
            'building_type': 'warehouse',
            'building_area_sqft': 35000,
            'score': 88
        }
    ]
    
    # Save as JSON
    print("\nSaving test data as JSON...")
    local_storage.save_json('test_buildings', test_buildings)
    
    # Load JSON
    print("Loading JSON data...")
    loaded_data = local_storage.load_json('test_buildings')
    print(f"Loaded {len(loaded_data)} records")
    
    # Save as CSV
    print("\nSaving test data as CSV...")
    local_storage.save_csv('test_buildings', test_buildings)
    
    # Load CSV
    print("Loading CSV data...")
    loaded_csv = local_storage.load_csv('test_buildings')
    print(f"Loaded {len(loaded_csv)} records from CSV")
    
    # List collections
    print("\nAvailable collections:")
    collections = local_storage.list_collections()
    for collection in collections:
        print(f"  - {collection}")
    
    print("\n✓ Local storage tests completed successfully!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SOLAR LEADS SYSTEM - LOCAL TESTING")
    print("="*60)
    
    try:
        test_address_normalization()
        test_geocoding()
        test_geometry_utils()
        test_local_storage()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review the test results above")
        print("2. Check data/raw/ for generated test files")
        print("3. Check logs/test.log for detailed logs")
        print("4. Ready to proceed with data ingestion scripts")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.exception("Test failed")
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
