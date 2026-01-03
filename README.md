# Commercial Solar Lead Identification System

An automated data pipeline for identifying and ranking commercial buildings suitable for solar panel installation in Upstate New York.

## Overview

This system ingests data from multiple public sources, processes and deduplicates building records, and generates a ranked list of high-potential solar installation leads.

## Features

- **Multi-Source Data Ingestion**
  - County assessor/property tax records
  - OpenStreetMap building footprints
  - Licensed business data (NAICS codes)
  - City/state open datasets

- **Data Processing**
  - Address normalization and standardization
  - Geocoding to lat/lng coordinates
  - Building deduplication using address + geometry
  - Business-to-building matching

- **AI-Powered Scoring**
  - Commercial/industrial building prioritization
  - Roof area estimation
  - Owner-occupancy detection
  - Energy use indicators

- **Cloud Storage**
  - Firestore integration for scalable data storage
  - Efficient querying and retrieval

## Architecture

```
solar-leads/
├── config/              # Configuration files
├── src/
│   ├── ingestion/       # Data ingestion scripts
│   ├── processing/      # Data processing and normalization
│   ├── scoring/         # Lead scoring algorithms
│   ├── storage/         # Firestore database operations
│   └── utils/           # Utility functions
├── data/
│   ├── raw/             # Raw data files
│   └── output/          # Generated reports
├── schemas/             # Firestore schema definitions
└── tests/               # Unit tests

```

## Setup

### Prerequisites

- Python 3.9+
- Google Cloud account with Firestore enabled
- API keys for geocoding services

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Configuration

1. Set up Google Cloud Firestore:
   - Create a project in Google Cloud Console
   - Enable Firestore API
   - Download service account credentials
   - Place credentials in `config/firebase-credentials.json`

2. Configure API keys in `.env`:
   - Geocoding API key (Google Maps or similar)
   - Any other required API keys

## Usage

### 1. Targeted ICP Discovery
This is the recommended way to find new high-priority leads (Churches, Warehouses, Industrial).

```bash
# Run the discovery tool for Upstate NY cities
./venv/bin/python src/discovery/run_discovery.py
```
This script uses precise geospatial bounding boxes to fetch buildings from OSM, enriches them with Google Places/Solar data, and merges them into your central dashboard.

### 2. Manual Data Ingestion (Legacy)

```bash
# Ingest OpenStreetMap buildings by area name
python src/ingestion/ingest_osm.py
```

### 3. Data Processing & Scoring
For a detailed breakdown of how leads are identified and scored, see [ENRICHMENT_STRATEGIES.md](./ENRICHMENT_STRATEGIES.md).

```bash
# Enrich and score existing raw data
python src/enrichment/enrich_data.py
```

## Data Schema

### Firestore Collections

#### `raw_assessor_data`
- Property tax and assessor records
- Fields: parcel_id, address, owner_name, property_class, assessed_value, etc.

#### `raw_osm_buildings`
- OpenStreetMap building footprints
- Fields: osm_id, geometry, building_type, area, tags

#### `raw_business_data`
- Licensed business information
- Fields: business_id, name, naics_code, address, website

#### `buildings` (Canonical)
- Deduplicated, enriched building records
- Fields: building_id, normalized_address, lat, lng, owner_name, building_type, roof_area, score

## Scoring Methodology

Buildings are scored based on:

1. **Building Type** (0-30 points)
   - Industrial: 30
   - Commercial: 25
   - Warehouse: 28
   - Office: 20
   - Mixed-use: 15

2. **Roof Area** (0-25 points)
   - >50,000 sq ft: 25
   - 25,000-50,000: 20
   - 10,000-25,000: 15
   - 5,000-10,000: 10

3. **Ownership** (0-20 points)
   - Owner-occupied: 20
   - Corporate-owned: 15
   - Individual owner: 10

4. **Energy Indicators** (0-15 points)
   - High energy use business type: 15
   - Medium energy use: 10
   - Low energy use: 5

5. **Property Value** (0-10 points)
   - Indicates financial capacity

**Total Score: 0-100 points**

## Output Format

Generated CSV includes:
- `address` - Full normalized address
- `owner_name` - Property owner
- `building_sq_ft` - Total building area
- `estimated_roof_area` - Estimated usable roof area
- `building_type` - Commercial, industrial, etc.
- `business_name` - Associated business (if any)
- `naics_code` - Business classification
- `website` - Business website
- `score` - Solar suitability score (0-100)
- `lat`, `lng` - Coordinates

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/
```

## License

MIT

## Contact

For questions or support, contact the development team.
