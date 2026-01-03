"""
Geometry utilities for building deduplication and area calculations.
"""

from typing import Tuple, Optional
from shapely.geometry import Point, Polygon, shape
from shapely.ops import transform
import pyproj
from functools import partial
import math
from loguru import logger


def calculate_distance(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float]
) -> float:
    """
    Calculate distance between two lat/lng coordinates in meters.
    Uses Haversine formula.
    
    Args:
        coord1: (latitude, longitude) tuple
        coord2: (latitude, longitude) tuple
    
    Returns:
        Distance in meters
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


def polygon_area_sqft(polygon_coords: list) -> float:
    """
    Calculate area of a polygon in square feet.
    
    Args:
        polygon_coords: List of (lng, lat) coordinate tuples
    
    Returns:
        Area in square feet
    """
    try:
        # Create polygon (note: shapely uses lng, lat order)
        polygon = Polygon(polygon_coords)
        
        # Get centroid for projection
        centroid = polygon.centroid
        
        # Create projection to calculate area in meters
        # Use UTM projection based on centroid
        wgs84 = pyproj.CRS('EPSG:4326')
        
        # Determine UTM zone from longitude
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_crs = pyproj.CRS(f'EPSG:326{utm_zone:02d}')  # Northern hemisphere
        
        # Create transformer
        project = pyproj.Transformer.from_crs(wgs84, utm_crs, always_xy=True).transform
        
        # Transform polygon to UTM
        polygon_utm = transform(project, polygon)
        
        # Calculate area in square meters
        area_sqm = polygon_utm.area
        
        # Convert to square feet (1 sqm = 10.764 sqft)
        area_sqft = area_sqm * 10.764
        
        return area_sqft
        
    except Exception as e:
        logger.error(f"Error calculating polygon area: {e}")
        return 0.0


def estimate_roof_area(building_area_sqft: float, num_stories: int = 1) -> float:
    """
    Estimate usable roof area for solar panels.
    
    Args:
        building_area_sqft: Total building area
        num_stories: Number of stories
    
    Returns:
        Estimated roof area in square feet
    """
    if num_stories <= 0:
        num_stories = 1
    
    # Footprint is total area divided by number of stories
    footprint = building_area_sqft / num_stories
    
    # Assume 70% of roof is usable for solar (accounting for HVAC, skylights, etc.)
    usable_roof_area = footprint * 0.7
    
    return usable_roof_area


def buildings_are_duplicates(
    building1: dict,
    building2: dict,
    distance_threshold: float = 20.0
) -> bool:
    """
    Determine if two building records represent the same building.
    
    Args:
        building1: First building record
        building2: Second building record
        distance_threshold: Maximum distance in meters to consider duplicates
    
    Returns:
        True if buildings are likely duplicates
    """
    # Check if both have coordinates
    if not all([
        building1.get('lat'), building1.get('lng'),
        building2.get('lat'), building2.get('lng')
    ]):
        # Fall back to address comparison
        addr1 = building1.get('normalized_address', '').upper()
        addr2 = building2.get('normalized_address', '').upper()
        return addr1 == addr2 and addr1 != ''
    
    # Calculate distance
    coord1 = (building1['lat'], building1['lng'])
    coord2 = (building2['lat'], building2['lng'])
    distance = calculate_distance(coord1, coord2)
    
    # If within threshold, check address similarity
    if distance <= distance_threshold:
        addr1 = building1.get('normalized_address', '').upper()
        addr2 = building2.get('normalized_address', '').upper()
        
        # If addresses are very similar or one is empty, consider duplicates
        if addr1 == addr2 or not addr1 or not addr2:
            return True
        
        # Check if street numbers and names match
        street1 = building1.get('street_number', '') + ' ' + building1.get('street_name', '')
        street2 = building2.get('street_number', '') + ' ' + building2.get('street_name', '')
        
        if street1.strip() and street2.strip() and street1.upper() == street2.upper():
            return True
    
    return False


def create_bounding_box(
    center_lat: float,
    center_lng: float,
    radius_meters: float
) -> Tuple[float, float, float, float]:
    """
    Create a bounding box around a center point.
    
    Args:
        center_lat: Center latitude
        center_lng: Center longitude
        radius_meters: Radius in meters
    
    Returns:
        Tuple of (south, west, north, east)
    """
    # Approximate degrees per meter
    lat_degree = 1 / 111320.0
    lng_degree = 1 / (111320.0 * math.cos(math.radians(center_lat)))
    
    lat_offset = radius_meters * lat_degree
    lng_offset = radius_meters * lng_degree
    
    south = center_lat - lat_offset
    north = center_lat + lat_offset
    west = center_lng - lng_offset
    east = center_lng + lng_offset
    
    return (south, west, north, east)
