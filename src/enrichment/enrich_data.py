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

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.local_storage import local_storage

# API Configuration
GOOGLE_PLACES_API_KEY = "AIzaSyDfBxbg5XM4N90C_bFdGiskLYasSUMT7ek"
SOLAR_API_BASE = "https://solar.googleapis.com/v1"


class PlacesEnricher:
    """Enrich building data with Google Places API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def find_place(self, address: str, lat: float, lng: float) -> Optional[Dict]:
        """Find place details using address and coordinates"""
        
        # Try nearby search first (more accurate for businesses)
        url = f"{self.base_url}/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': 50,  # 50 meters
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                # Get the first result (closest)
                place = data['results'][0]
                place_id = place.get('place_id')
                
                # Get detailed information
                if place_id:
                    return self.get_place_details(place_id)
                
                return {
                    'name': place.get('name'),
                    'types': place.get('types', []),
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'business_status': place.get('business_status')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Places API error: {e}")
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
            logger.warning(f"Skipping {building.get('address')} - no coordinates")
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


def recalculate_scores(buildings: List[Dict]) -> List[Dict]:
    """Recalculate scores with enriched data"""
    MIN_ROOF_SIZE_SQFT = 5000
    SQM_TO_SQFT = 10.7639
    
    for building in buildings:
        score = 0
        breakdown = {}
        
        # Check roof size - disqualify if < 5000 sq ft
        # Use Solar API area if available, otherwise use initial estimate
        roof_area_sqft = 0
        if building.get('solar_max_area_m2'):
            roof_area_sqft = building['solar_max_area_m2'] * SQM_TO_SQFT
        else:
            roof_area_sqft = building.get('estimated_roof_area', 0)
            
        if roof_area_sqft < MIN_ROOF_SIZE_SQFT:
            building['enriched_score'] = 0
            building['enriched_score_breakdown'] = {'disqualified': 'Roof area below 5000 sq ft'}
            building['ineligible'] = True
            continue
            
        building['ineligible'] = False
        
        # 1. Solar API data (0-40 points) - MOST IMPORTANT
        if building.get('solar_max_panels'):
            max_panels = building['solar_max_panels']
            if max_panels >= 100:
                solar_score = 40
            elif max_panels >= 50:
                solar_score = 35
            elif max_panels >= 25:
                solar_score = 30
            elif max_panels >= 10:
                solar_score = 20
            else:
                solar_score = 10
            score += solar_score
            breakdown['solar_potential'] = solar_score
        
        # 2. Financial viability (0-20 points)
        if building.get('solar_financially_viable'):
            score += 20
            breakdown['financial_viability'] = 20
            
            # Bonus for quick payback
            payback = building.get('solar_payback_years', 999)
            if payback and payback < 7:
                score += 5
                breakdown['quick_payback_bonus'] = 5
        
        # 3. Building type (0-15 points)
        building_type = building.get('building_type', '')
        type_scores = {
            'industrial': 15,
            'warehouse': 14,
            'commercial': 12,
            'retail': 10,
            'office': 8,
            'mixed_use': 6
        }
        type_score = type_scores.get(building_type, 5)
        score += type_score
        breakdown['building_type'] = type_score
        
        # 4. Business presence (0-10 points)
        if building.get('business_name'):
            score += 10
            breakdown['business_identified'] = 10
            
            # Bonus for good rating
            rating = building.get('business_rating')
            if rating and rating >= 4.0:
                score += 3
                breakdown['good_rating_bonus'] = 3
        
        # 5. Sunshine hours (0-10 points)
        sunshine = building.get('solar_sunshine_hours_year', 0)
        if sunshine >= 2000:
            sunshine_score = 10
        elif sunshine >= 1500:
            sunshine_score = 7
        elif sunshine >= 1000:
            sunshine_score = 5
        else:
            sunshine_score = 2
        score += sunshine_score
        breakdown['sunshine_hours'] = sunshine_score
        
        # 6. Environmental Impact (0-5 points)
        # Higher offset potential = more points
        offset = building.get('solar_carbon_offset_kg_mwh', 0)
        if offset > 400:
            score += 5
            breakdown['carbon_offset_potential'] = 5
        
        # 7. Data quality (0-5 points)
        if building.get('geocoded'):
            score += 5
            breakdown['geocoded'] = 5
        
        building['enriched_score'] = min(score, 100)  # Cap at 100
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
