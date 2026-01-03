"""
Data enrichment using Google Places API and Solar API.
Adds business information and accurate solar potential data.
"""

import os
import sys
from pathlib import Path
import time
import requests
from typing import Dict, List, Optional, Tuple
from loguru import logger
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.local_storage import local_storage

# API Configuration
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")
SOLAR_API_BASE = "https://solar.googleapis.com/v1"

# ICP Configuration (Ideal Customer Profile)
ICP_BUCKETS = {
    "TIER_1_INDUSTRIAL": {
        "keywords": ["manufacturing", "industrial", "fabrication", "steel", "metal", "plastics", "machining", "assembly", "production", "processing", "plant", "factory", "textiles", "materials", "components", "foundry", "mill", "works", "tech", "systems", "pharmaceutical", "chemical", "pharma"],
        "bonus": 25,
        "label": "🏭 Tier 1: Manufacturing/Industrial"
    },
    "TIER_1_LOGISTICS": {
        "keywords": ["warehouse", "distribution", "logistics", "storage", "fulfillment", "moving", "freight", "supply", "industrial park", "terminal", "dock", "cargo", "transport", "industrial development"],
        "bonus": 25,
        "label": "📦 Tier 1: Warehousing/Storage"
    },
    "TIER_1_COLD_LOAD": {
        "keywords": ["brewery", "food processing", "pickle", "dairy", "cold storage", "refrigerated", "refrigeration", "greenhouse", "agriculture", "produce", "packaging", "beverage", "bakery", "meat", "distillery"],
        "bonus": 25,
        "label": "❄️ Tier 1: Food/Beverage/Cold Load"
    },
    "TIER_2_AUTO": {
        "keywords": ["auto", "dealership", "mobility", "fleet", "truck", "equipment", "service center", "repair facility", "collision", "motors", "ford", "chevy", "toyota", "honda", "leasing"],
        "bonus": 15,
        "label": "🚗 Tier 2: Auto/Equipment"
    },
    "TIER_2_NONPROFIT": {
        "keywords": ["church", "temple", "mosque", "synagogue", "community center", "nonprofit", "youth center", "club", "charity", "ymca", "ywca", "salvation army", "mission"],
        "bonus": 15,
        "label": "⛪ Tier 2: Nonprofit/Community"
    },
    "EXCLUDE_DEPRIORITIZE": {
        "keywords": ["apartment", "residential", "condo", "medical office", "strip mall", "boutique", "small retail", "high-rise", "primary school", "clinic", "dentist", "physician", "real_estate_agency"],
        "penalty": -30,
        "label": "🚫 De-prioritize"
    }
}


class PlacesEnricher:
    """Enrich building data with Google Places API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def is_generic_name(self, name: str, address: str) -> bool:
        """Check if the name is just a city, zip, or the address itself"""
        if not name:
            return True
        
        name_lower = name.lower()
        # Common generic locality names
        generic_markers = ['rochester', 'albany', 'syracuse', 'buffalo', 'new york', 'county']
        if name_lower in generic_markers:
            return True
            
        # Matches zip code pattern
        if any(token.isdigit() and len(token) == 5 for token in name.split()):
            return True
            
        # Matches start of address (e.g. "400 Andrews" matches "400 Andrews St")
        addr_snippet = address.split(',')[0].lower()
        if addr_snippet in name_lower or name_lower in addr_snippet:
            return True
            
        return False

    def get_base_address(self, address: str) -> str:
        """Strip suite/unit/apartment numbers to find primary building record"""
        # Simple extraction of the main street address
        parts = address.split(',')
        street_part = parts[0]
        # Remove common unit markers
        for marker in ['Suite', 'Ste', 'Unit', 'Apt', 'Apartment', 'Floor', 'Fl']:
            if marker in street_part:
                street_part = street_part.split(marker)[0].strip()
        
        return f"{street_part}, {','.join(parts[1:])}"

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Resolve missing lat/lng using Google Geocoding API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': self.api_key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('results'):
                location = data['results'][0]['geometry']['location']
                logger.info(f"Geocoding Success: {address} -> ({location['lat']}, {location['lng']})")
                return (location['lat'], location['lng'])
            return None
        except Exception as e:
            logger.error(f"Geocoding fallback error: {e}")
            return None

    def find_place(self, address: str, lat: float, lng: float) -> Optional[Dict]:
        """
        The "Ultimate Robust Waterfall" - 6-Stage Business Identification
        Modified for Landmark Awareness and Entity Matching.
        """
        
        # Strategy 0: Landmark Detection (e.g. "Midtown Plaza")
        # -----------------------------------------------------------------
        landmark_parts = address.split(',')[0]
        if any(keyword in landmark_parts.lower() for keyword in ['plaza', 'tower', 'building', 'center', 'landing']):
            find_url = f"{self.base_url}/findplacefromtext/json"
            find_params = {
                'input': landmark_parts,
                'inputtype': 'textquery',
                'fields': 'name,place_id,types,business_status,website,formatted_phone_number',
                'locationbias': f'circle:50@{lat},{lng}',
                'key': self.api_key
            }
            res = requests.get(find_url, params=find_params, timeout=10).json()
            for cand in res.get('candidates', []):
                if not self.is_generic_name(cand.get('name'), address):
                    logger.info(f"Waterfall Stage 0 [Landmark] Success: '{cand.get('name')}'")
                    return cand

        # Strategy 1: Targeted findplacefromtext (Current Address)
        # -----------------------------------------------------------------
        find_url = f"{self.base_url}/findplacefromtext/json"
        find_params = {
            'input': address,
            'inputtype': 'textquery',
            'fields': 'name,place_id,types,business_status,website,formatted_phone_number',
            'locationbias': f'point:{lat},{lng}',
            'key': self.api_key
        }
        
        try:
            res = requests.get(find_url, params=find_params, timeout=10).json()
            for cand in res.get('candidates', []):
                if not self.is_generic_name(cand.get('name'), address):
                    logger.info(f"Waterfall Stage 1 [Precise] Success: '{cand.get('name')}'")
                    return cand
            
            # Strategy 2: Base Address Search (Unit Correction)
            # -----------------------------------------------------------------
            base_address = self.get_base_address(address).split(',')[0] # Try just the street part
            find_params['input'] = f"businesses at {base_address}"
            res = requests.get(find_url, params=find_params, timeout=10).json()
            for cand in res.get('candidates', []):
                if not self.is_generic_name(cand.get('name'), address):
                    logger.info(f"Waterfall Stage 2 [Base Address Meta] Success: '{cand.get('name')}'")
                    return cand

            # Strategy 3: Aggressive Keyword textsearch ("companies at...")
            # -----------------------------------------------------------------
            text_url = f"{self.base_url}/textsearch/json"
            text_params = {
                'query': f"major tenant or business at {address}",
                'location': f"{lat},{lng}",
                'radius': 50,
                'key': self.api_key
            }
            res = requests.get(text_url, params=text_params, timeout=10).json()
            for result in res.get('results', []):
                if not self.is_generic_name(result.get('name'), address):
                    if any(t in result.get('types', []) for t in ['establishment', 'point_of_interest']):
                        logger.info(f"Waterfall Stage 3 [Keyword Search] Success: '{result.get('name')}'")
                        return self.get_place_details(result['place_id'])

            # Strategy 4: Corporate/Entity textsearch ("Owner of {address}")
            # -----------------------------------------------------------------
            text_params['query'] = f"office building or headquarters at {address.split(',')[0]}"
            res = requests.get(text_url, params=text_params, timeout=10).json()
            for result in res.get('results', []):
                name = result.get('name', '').lower()
                if any(x in name for x in ['llc', 'corp', 'inc', 'tower', 'plaza', 'building']):
                    logger.info(f"Waterfall Stage 4 [Property Entity] Success: '{result.get('name')}'")
                    return self.get_place_details(result['place_id'])

            return None
            
        except Exception as e:
            logger.error(f"Waterfall Enrichment Error: {e}")
            return None

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed place information"""
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,types,rating,user_ratings_total,business_status,website,formatted_phone_number',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('result'):
                return data['result']
            
            return None
            
        except Exception as e:
            logger.error(f"Place details error: {e}")
            return None


class SolarEnricher:
    """Enrich building data with Google Solar API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_building_insights(self, lat: float, lng: float) -> Optional[Dict]:
        """Get solar insights for a building"""
        url = f"{SOLAR_API_BASE}/buildingInsights:findClosest"
        params = {
            'location.latitude': lat,
            'location.longitude': lng,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 404:
                logger.warning(f"No solar data for {lat}, {lng}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Extract key solar metrics
            solar_data = {
                'max_array_panels_count': data.get('solarPotential', {}).get('maxArrayPanelsCount'),
                'max_array_area_m2': data.get('solarPotential', {}).get('maxArrayAreaMeters2'),
                'max_sunshine_hours_per_year': data.get('solarPotential', {}).get('maxSunshineHoursPerYear'),
                'carbon_offset_factor_kg_per_mwh': data.get('solarPotential', {}).get('carbonOffsetFactorKgPerMwh'),
                'panel_capacity_watts': data.get('solarPotential', {}).get('panelCapacityWatts', 400),
                'panel_lifetime_years': data.get('solarPotential', {}).get('panelLifetimeYears', 20),
            }
            
            # Entire whole roof stats
            whole_roof = data.get('solarPotential', {}).get('wholeRoofStats', {})
            if whole_roof:
                solar_data['roof_area_m2'] = whole_roof.get('areaMeters2')
                solar_data['roof_ground_area_m2'] = whole_roof.get('groundAreaMeters2')
            
            # Roof segments count
            segments = data.get('solarPotential', {}).get('roofSegmentStats', [])
            solar_data['roof_segment_count'] = len(segments)
            
            # Get solar panel configurations
            configs = data.get('solarPotential', {}).get('solarPanelConfigs', [])
            if configs:
                # Get the most efficient configuration
                solar_data['panel_configs_count'] = len(configs)
                optimal = configs[-1]  # Highest panel count
                solar_data['optimal_panels_count'] = optimal.get('panelsCount')
                solar_data['optimal_yearly_energy_dc_kwh'] = optimal.get('yearlyEnergyDcKwh')
                
                # Small/Medium/Large benchmarks
                if len(configs) > 0:
                    solar_data['min_panels_count'] = configs[0].get('panelsCount')
                    solar_data['min_yearly_energy_kwh'] = configs[0].get('yearlyEnergyDcKwh')
                
                if len(configs) > len(configs) // 2:
                    mid = configs[len(configs) // 2]
                    solar_data['mid_panels_count'] = mid.get('panelsCount')
                    solar_data['mid_yearly_energy_kwh'] = mid.get('yearlyEnergyDcKwh')
            
            # Get financial analysis if available
            financial = data.get('solarPotential', {}).get('financialAnalyses', [])
            if financial:
                # Find the one that matches default or default bill
                best_financial = financial[0]
                for f in financial:
                    if f.get('defaultBill'):
                        best_financial = f
                        break
                        
                solar_data['monthly_bill_savings'] = best_financial.get('monthlyBill', {}).get('units')
                solar_data['payback_years'] = best_financial.get('cashPurchaseSavings', {}).get('paybackYears')
                solar_data['financially_viable'] = best_financial.get('financiallyViable', False)
                solar_data['solar_percentage'] = best_financial.get('solarPercentage')
                
            return solar_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"No solar data available for {lat}, {lng}")
            else:
                logger.error(f"Solar API HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Solar API error: {e}")
            return None


def enrich_buildings(buildings: List[Dict], use_solar_api: bool = True, use_places_api: bool = True) -> List[Dict]:
    """Enrich building data with Google APIs"""
    
    places_enricher = PlacesEnricher(GOOGLE_PLACES_API_KEY) if use_places_api else None
    solar_enricher = SolarEnricher(GOOGLE_PLACES_API_KEY) if use_solar_api else None
    
    enriched = []
    
    for building in tqdm(buildings, desc="Enriching buildings"):
        enriched_building = building.copy()
        
        lat = building.get('lat')
        lng = building.get('lng')
        
        if not lat or not lng:
            logger.info(f"Missing coordinates for {building.get('address')}. Attempting Geocoding Fallback...")
            if places_enricher:
                coords = places_enricher.get_coordinates(building.get('address', ''))
                if coords:
                    lat, lng = coords
                    enriched_building['lat'] = lat
                    enriched_building['lng'] = lng
                    enriched_building['geocoded'] = True
                else:
                    logger.warning(f"Geocoding failed for {building.get('address')}. Skipping.")
                    enriched.append(enriched_building)
                    continue
            else:
                logger.warning(f"Skipping {building.get('address')} - no coordinates and geocoder disabled")
                enriched.append(enriched_building)
                continue
        
        # Enrich with Places API
        if places_enricher:
            place_data = places_enricher.find_place(
                building.get('address', ''),
                lat,
                lng
            )
            
            if place_data:
                enriched_building['business_name'] = place_data.get('name')
                enriched_building['business_types'] = ",".join(place_data.get('types', []))
                enriched_building['business_rating'] = place_data.get('rating')
                enriched_building['business_reviews_count'] = place_data.get('user_ratings_total')
                enriched_building['business_status'] = place_data.get('business_status')
                enriched_building['business_website'] = place_data.get('website')
                enriched_building['business_phone'] = place_data.get('formatted_phone_number')
                
                logger.info(f"Found business: {place_data.get('name')} at {building.get('address')}")
            
            # Rate limiting
            time.sleep(0.1)
        
        # Enrich with Solar API
        if solar_enricher:
            solar_data = solar_enricher.get_building_insights(lat, lng)
            
            if solar_data:
                # Solar Potential Map
                enriched_building['solar_max_panels'] = solar_data.get('max_array_panels_count')
                enriched_building['solar_max_area_m2'] = solar_data.get('max_array_area_m2')
                enriched_building['solar_sunshine_hours_year'] = solar_data.get('max_sunshine_hours_per_year')
                enriched_building['solar_carbon_offset_kg_mwh'] = solar_data.get('carbon_offset_factor_kg_per_mwh')
                enriched_building['solar_optimal_panels'] = solar_data.get('optimal_panels_count')
                enriched_building['solar_optimal_energy_kwh_year'] = solar_data.get('optimal_yearly_energy_dc_kwh')
                enriched_building['solar_monthly_savings'] = solar_data.get('monthly_bill_savings')
                enriched_building['solar_payback_years'] = solar_data.get('payback_years')
                enriched_building['solar_financially_viable'] = solar_data.get('financially_viable', False)
                enriched_building['solar_panel_capacity_watts'] = solar_data.get('panel_capacity_watts', 400)
                
                # New fields
                enriched_building['solar_roof_area_m2'] = solar_data.get('roof_area_m2')
                enriched_building['solar_roof_segment_count'] = solar_data.get('roof_segment_count', 0)
                enriched_building['solar_min_panels'] = solar_data.get('min_panels_count')
                enriched_building['solar_min_energy_kwh'] = solar_data.get('min_yearly_energy_kwh')
                enriched_building['solar_percentage'] = solar_data.get('solar_percentage')
                
                logger.info(f"Solar data: {solar_data.get('max_array_panels_count')} panels, {solar_data.get('optimal_yearly_energy_dc_kwh')} kWh/year")
            
            # Rate limiting
            time.sleep(0.2)
        
        enriched.append(enriched_building)
    
    return enriched


def identify_icp_bucket(building: Dict) -> Tuple[Optional[str], int]:
    """Identify which ICP bucket a building falls into and return bonus/penalty"""
    business_name = str(building.get('business_name', '')).lower()
    business_types = str(building.get('business_types', '')).lower()
    combined_text = f"{business_name} {business_types}"
    
    # Check EXCLUSIONS first
    for kw in ICP_BUCKETS["EXCLUDE_DEPRIORITIZE"]["keywords"]:
        if kw in combined_text:
            return "EXCLUDE_DEPRIORITIZE", ICP_BUCKETS["EXCLUDE_DEPRIORITIZE"]["penalty"]
            
    # Check TIER 1
    for bucket_id in ["TIER_1_INDUSTRIAL", "TIER_1_LOGISTICS", "TIER_1_COLD_LOAD"]:
        for kw in ICP_BUCKETS[bucket_id]["keywords"]:
            if kw in combined_text:
                logger.debug(f"ICP Match: {bucket_id} (Keyword: {kw}) for {business_name}")
                return bucket_id, ICP_BUCKETS[bucket_id]["bonus"]
                
    # Check TIER 2
    for bucket_id in ["TIER_2_AUTO", "TIER_2_NONPROFIT"]:
        for kw in ICP_BUCKETS[bucket_id]["keywords"]:
            if kw in combined_text:
                logger.debug(f"ICP Match: {bucket_id} (Keyword: {kw}) for {business_name}")
                return bucket_id, ICP_BUCKETS[bucket_id]["bonus"]
                
    return None, 0

def recalculate_scores(buildings: List[Dict]) -> List[Dict]:
    """Recalculate scores with enriched data and ICP-based prioritization"""
    MIN_ROOF_SIZE_SQFT = 3000
    SQM_TO_SQFT = 10.7639
    PANEL_SIZE_SQFT = 17.5 
    
    for building in buildings:
        score = 0
        breakdown = {}
        
        # 0. ICP Identification
        bucket_id, icp_bonus = identify_icp_bucket(building)
        building['icp_bucket'] = ICP_BUCKETS[bucket_id]['label'] if bucket_id else "General Commercial"
        
        # Use Solar API area if available, otherwise use initial estimate
        solar_area_sqft = 0
        if building.get('solar_max_area_m2'):
            solar_area_sqft = building['solar_max_area_m2'] * SQM_TO_SQFT
        
        roof_area_sqft = solar_area_sqft or building.get('estimated_roof_area', 0)
            
        if roof_area_sqft < MIN_ROOF_SIZE_SQFT:
            # Check if it's a known landmark or has a verified business occupant
            business_name = building.get('business_name')
            is_identified = business_name is not None and len(str(business_name)) > 0
            is_landmark = any(kw in str(business_name).lower() for kw in ['tower', 'plaza', 'building', 'center', 'square', 'landing', 'mall'])
            
            # If it's a priority ICP, we override the size threshold (e.g. a small industrial fabricator)
            is_priority = bucket_id is not None and bucket_id.startswith("TIER_1")

            if not is_landmark and not is_identified and not is_priority:
                building['enriched_score'] = 12
                building['enriched_score_breakdown'] = {'disqualified': 'Small residential/non-commercial scale'}
                building['ineligible'] = True
                continue
            else:
                logger.info(f"Preserving lead: {business_name} (Bucket: {bucket_id})")
                building['ineligible'] = False
            
        building['ineligible'] = False
        
        # 1. Solar Potential (0-40 points)
        panels = building.get('solar_max_panels')
        is_proxy = False
        
        if not panels:
            panels = int((roof_area_sqft / PANEL_SIZE_SQFT) * 0.7)
            building['solar_max_panels'] = panels
            building['solar_optimal_energy_kwh_year'] = int(panels * 400 * 1.25)
            building['solar_proxy'] = True
            is_proxy = True
            
        if panels >= 250: # Large scale industrial
            solar_score = 40
        elif panels >= 100:
            solar_score = 35
        elif panels >= 50:
            solar_score = 25
        else:
            solar_score = 15
            
        if is_proxy:
            solar_score = int(solar_score * 0.8)
            
        score += solar_score
        breakdown['solar_potential'] = solar_score
        
        # 2. ICP Bonus/Penalty (UP TO +25 or -30)
        score += icp_bonus
        if bucket_id:
            breakdown['icp_relevance'] = icp_bonus
        
        # 3. Financial viability (0-15 points)
        if building.get('solar_financially_viable') or is_proxy:
            viability_score = 10 if is_proxy else 15
            score += viability_score
            breakdown['financial_viability'] = viability_score
            
            # Bonus for quick payback
            payback = building.get('solar_payback_years', 10)
            if payback < 7:
                score += 5
                breakdown['quick_payback_bonus'] = 5
        
        # 4. Building type (0-10 points)
        building_type = building.get('building_type', '')
        type_scores = {
            'industrial': 10,
            'warehouse': 10,
            'commercial': 8,
            'retail': 5,
            'office': 4,
            'mixed_use': 3
        }
        type_score = type_scores.get(building_type, 2)
        score += type_score
        breakdown['building_type'] = type_score
        
        # 5. Business presence & Rating (0-10 points)
        if building.get('business_name'):
            score += 7
            breakdown['business_identified'] = 7
            
            rating = building.get('business_rating')
            if rating and rating >= 4.0:
                score += 3
                breakdown['good_rating_bonus'] = 3
        
        building['enriched_score'] = max(0, min(score, 100))
        building['enriched_score_breakdown'] = breakdown
    
    return buildings


def main():
    """Main enrichment pipeline"""
    logger.info("Starting data enrichment with Google APIs...")
    
    # Load existing buildings
    buildings = local_storage.load_json('upstate_ny_buildings')
    logger.info(f"Loaded {len(buildings)} buildings")
    
    # Enrich data
    logger.info("Enriching with Places API and Solar API...")
    enriched_buildings = enrich_buildings(
        buildings,
        use_solar_api=True,
        use_places_api=True
    )
    
    # Recalculate scores
    logger.info("Recalculating scores with enriched data...")
    scored_buildings = recalculate_scores(enriched_buildings)
    
    # Save enriched data
    local_storage.save_json('enriched_buildings', scored_buildings)
    local_storage.save_csv('enriched_buildings', scored_buildings)
    
    # Save top leads
    top_leads = sorted(scored_buildings, key=lambda x: x.get('enriched_score', 0), reverse=True)[:20]
    local_storage.save_csv('top_enriched_leads', top_leads)
    
    # Print summary
    print("\n" + "="*80)
    print("ENRICHMENT COMPLETE!")
    print("="*80)
    
    enriched_count = len([b for b in scored_buildings if b.get('solar_max_panels')])
    business_count = len([b for b in scored_buildings if b.get('business_name')])
    
    print(f"\n✓ Total buildings: {len(scored_buildings)}")
    print(f"✓ Solar data enriched: {enriched_count}")
    print(f"✓ Business data enriched: {business_count}")
    
    print(f"\nTop 5 Leads (Enriched Scores):")
    print(f"{'Rank':<6} {'Score':<8} {'Panels':<10} {'Business':<40}")
    print("-" * 80)
    
    for i, building in enumerate(top_leads[:5], 1):
        score = building.get('enriched_score', 0)
        panels = building.get('solar_max_panels', 'N/A')
        business = building.get('business_name', 'Unknown')[:37]
        print(f"#{i:<5} {score:<8} {panels:<10} {business:<40}")
    
    print(f"\n✓ Saved to data/raw/enriched_buildings.json")
    print(f"✓ Saved to data/raw/enriched_buildings.csv")
    print(f"✓ Top 20 leads saved to data/raw/top_enriched_leads.csv")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
