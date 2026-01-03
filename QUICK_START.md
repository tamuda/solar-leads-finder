# Quick Start Guide

## 🚀 Getting Started with Solar Leads System

### Prerequisites
- Python 3.9+ (tested with 3.12)
- macOS, Linux, or Windows
- Internet connection (for geocoding)

### Installation

```bash
# 1. Navigate to project directory
cd /Users/tamuda/Downloads/Work_rescources/Portfolio/solar-leads

# 2. Create virtual environment (already done)
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# 4. Install dependencies (already done)
pip install -r requirements.txt
```

### Running Tests

```bash
# Activate environment
source venv/bin/activate

# Run local tests
python tests/test_local.py
```

Expected output:
```
============================================================
✓ ALL TESTS COMPLETED SUCCESSFULLY!
============================================================
```

### Project Structure

```
solar-leads/
│
├── 📄 README.md                    # Main documentation
├── 📄 TESTING_SUMMARY.md           # Test results & next steps
├── 📄 QUICK_START.md               # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment variables template
│
├── 📁 config/
│   └── config.py                   # Configuration management
│
├── 📁 schemas/
│   └── firestore_schema.json       # Database schema
│
├── 📁 src/
│   ├── 📁 utils/
│   │   ├── address_utils.py        # Address normalization & geocoding
│   │   ├── geo_utils.py            # Geometry calculations
│   │   └── __init__.py
│   │
│   ├── 📁 storage/
│   │   ├── firestore_client.py     # Firebase integration
│   │   ├── local_storage.py        # Local file storage
│   │   └── __init__.py
│   │
│   ├── 📁 ingestion/               # (Coming next)
│   ├── 📁 processing/              # (Coming next)
│   └── 📁 scoring/                 # (Coming next)
│
├── 📁 data/
│   ├── raw/                        # Raw data files
│   └── output/                     # Generated reports
│
├── 📁 tests/
│   └── test_local.py               # Local testing suite
│
└── 📁 logs/                        # Application logs
```

### What's Working Now

✅ **Address Utilities**
```python
from src.utils import AddressNormalizer, Geocoder

# Parse and normalize addresses
normalizer = AddressNormalizer()
components = normalizer.parse_address("123 Main St, Rochester, NY 14604")
normalized = normalizer.normalize_address("123 Main Street")

# Geocode addresses
geocoder = Geocoder()
coords = geocoder.geocode("City Hall, Rochester, NY")
# Returns: (43.157006, -77.614887)
```

✅ **Geometry Utilities**
```python
from src.utils import calculate_distance, estimate_roof_area

# Calculate distance between two points
distance = calculate_distance((43.157, -77.614), (43.129, -77.629))
# Returns: distance in meters

# Estimate roof area
roof_area = estimate_roof_area(building_area_sqft=50000, num_stories=2)
# Returns: 17,500 sqft (70% of footprint)
```

✅ **Local Storage**
```python
from src.storage.local_storage import local_storage

# Save data
buildings = [
    {"id": "001", "address": "123 Main St", "score": 85},
    {"id": "002", "address": "456 Oak Ave", "score": 92}
]
local_storage.save_json('buildings', buildings)
local_storage.save_csv('buildings', buildings)

# Load data
data = local_storage.load_json('buildings')
```

### Next Development Steps

#### 1. OpenStreetMap Ingestion
Create `src/ingestion/ingest_osm.py`:
- Query Overpass API for building footprints
- Filter for commercial/industrial buildings
- Calculate building areas
- Save to local storage

#### 2. County Assessor Ingestion
Create `src/ingestion/ingest_assessor.py`:
- Fetch property tax records (CSV or API)
- Parse property classifications
- Extract owner information
- Save to local storage

#### 3. Business Data Ingestion
Create `src/ingestion/ingest_business.py`:
- Fetch licensed business data
- Extract NAICS codes
- Match to addresses
- Save to local storage

#### 4. Processing Pipeline
Create `src/processing/process_pipeline.py`:
- Normalize all addresses
- Geocode missing coordinates
- Deduplicate buildings
- Join business data

#### 5. Scoring System
Create `src/scoring/generate_leads.py`:
- Implement scoring algorithm
- Rank buildings
- Export top leads to CSV

### Example Workflow

```bash
# 1. Ingest data from multiple sources
python src/ingestion/ingest_osm.py --region "Monroe County, NY"
python src/ingestion/ingest_assessor.py --county monroe --state ny
python src/ingestion/ingest_business.py --county monroe --state ny

# 2. Process and normalize data
python src/processing/process_pipeline.py

# 3. Generate ranked leads
python src/scoring/generate_leads.py --output data/output/leads.csv --top 500

# 4. Review results
cat data/output/leads.csv
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Geocoding (optional - using free Nominatim by default)
GOOGLE_MAPS_API_KEY=your-key-here

# Data sources
ASSESSOR_DATA_URL=https://data.example.gov/resource/assessor.json

# Processing
GEOCODING_BATCH_SIZE=100
MIN_ROOF_AREA=2000
MIN_SCORE_THRESHOLD=40
```

### Troubleshooting

**Import errors:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Geocoding timeouts:**
- Normal for free Nominatim service
- Add delays between requests
- Consider paid geocoding service for production

**Permission errors:**
```bash
# Ensure data directories exist
mkdir -p data/raw data/output logs
```

### Resources

- **OpenStreetMap Overpass API**: https://overpass-api.de/
- **Nominatim Geocoding**: https://nominatim.org/
- **usaddress Documentation**: https://github.com/datamade/usaddress
- **GeoPandas**: https://geopandas.org/

### Getting Help

Check the logs:
```bash
tail -f logs/test.log
```

Review test output:
```bash
python tests/test_local.py
```

### What's Next?

See `TESTING_SUMMARY.md` for detailed next steps and development roadmap.

---

**Current Status**: ✅ Core utilities tested and working
**Ready for**: Data ingestion development
**Estimated time to MVP**: 2-3 days of development
