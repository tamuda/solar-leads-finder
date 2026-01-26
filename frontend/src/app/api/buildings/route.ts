import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';

export async function GET() {
  try {
    // Read the enriched CSV file from the parent directory
    const csvPath = path.join(process.cwd(), '..', 'data', 'raw', 'enriched_buildings.csv');
    const fileContent = fs.readFileSync(csvPath, 'utf-8');
    
    // Parse CSV
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
    });

    // Transform the data
    const buildings = records.map((record: any) => ({
      building_id: record.building_id,
      address: record.address,
      normalized_address: record.normalized_address,
      city: record.city,
      state: record.state,
      zip_code: record.zip_code,
      lat: record.lat ? parseFloat(record.lat) : null,
      lng: record.lng ? parseFloat(record.lng) : null,
      building_type: record.building_type,
      building_area_sqft: parseInt(record.building_area_sqft) || 0,
      num_stories: parseInt(record.num_stories) || 1,
      estimated_roof_area: parseFloat(record.estimated_roof_area) || 0,
      solar_capacity_kw: parseFloat(record.solar_capacity_kw) || 0,
      score: parseInt(record.enriched_score) || parseInt(record.score) || 0,
      geocoded: record.geocoded === 'True' || record.geocoded === 'true',
      data_quality: record.data_quality,
      // New enriched fields
      business_name: record.business_name || null,
      business_rating: record.business_rating ? parseFloat(record.business_rating) : null,
      business_reviews_count: record.business_reviews_count ? parseInt(record.business_reviews_count) : null,
      business_website: record.business_website || null,
      business_phone: record.business_phone || null,
      business_status: record.business_status || null,
      business_types: record.business_types ? record.business_types.split(',') : [],
      
      // Solar metrics
      solar_max_panels: record.solar_max_panels ? parseInt(record.solar_max_panels) : null,
      solar_optimal_energy_kwh_year: record.solar_optimal_energy_kwh_year ? parseFloat(record.solar_optimal_energy_kwh_year) : null,
      solar_payback_years: record.solar_payback_years ? parseFloat(record.solar_payback_years) : null,
      solar_financially_viable: record.solar_financially_viable === 'True' || record.solar_financially_viable === 'true',
      solar_sunshine_hours_year: record.solar_sunshine_hours_year ? parseFloat(record.solar_sunshine_hours_year) : null,
      solar_carbon_offset_kg_mwh: record.solar_carbon_offset_kg_mwh ? parseFloat(record.solar_carbon_offset_kg_mwh) : null,
      solar_roof_area_m2: record.solar_roof_area_m2 ? parseFloat(record.solar_roof_area_m2) : null,
      solar_roof_segment_count: record.solar_roof_segment_count ? parseInt(record.solar_roof_segment_count) : 0,
      solar_min_panels: record.solar_min_panels ? parseInt(record.solar_min_panels) : null,
      solar_min_energy_kwh: record.solar_min_energy_kwh ? parseFloat(record.solar_min_energy_kwh) : null,
      solar_percentage: record.solar_percentage ? parseFloat(record.solar_percentage) : null,
      icp_bucket: record.icp_bucket || 'General Commercial',
      ineligible: record.ineligible === 'True' || record.ineligible === 'true',
    }));

    return NextResponse.json(buildings);
  } catch (error) {
    console.error('Error reading buildings data:', error);
    return NextResponse.json({ error: 'Failed to load buildings data' }, { status: 500 });
  }
}
