# Solar Leads Discovery & Enrichment Strategies

This document tracks the different strategies implemented to identify and qualify high-quality solar leads.

## 🔍 Initial Discovery Strategies (The "Finding")

### Strategy 1: Geospatial Footprint Analysis (OSM)
*   **Description**: Queries building footprints from OpenStreetMap (Overpass API) based on area and classification.
*   **Logic**: 
    1. Filters for buildings marked as `industrial`, `warehouse`, or `commercial`.
    2. Uses polygon area to estimate the initial scale of the potential lead.
*   **Current Status**: Working. Provides the base list of physical structures.

### Strategy 2: Address Normalization & Geocoding
*   **Description**: Standardizes raw address strings to ensure high match rates during enrichment.
*   **Tools**: `usaddress` for parsing and `Nominatim` for initial geocoding.
*   **Logic**: Converts "Street" to "ST", identifies unit numbers, and confirms city/zip consistency.
*   **Current Status**: Verified and documented in `TESTING_SUMMARY.md`.

---

## 🏢 Business Name Identification Strategies (The "Enrichment")

### Strategy 1: Targeted Text Search (`findplacefromtext`) [CURRENT DEFAULT]
*   **Description**: Queries Google Places using the full address as a text string with a location bias.
*   **API Endpoint**: `findplacefromtext/json`
*   **Logic**:
    1.  Uses `inputtype=textquery` with the building's specific address.
    2.  Sets `locationbias` to the building's coordinates to focus results.
    3.  Filters for `candidates` categorized as `establishment`.
    4.  Logic checks if the returned name is just a numeric address; if so, it attempts to find a actual tenant.
*   **Effectiveness**: **High**. Success rate significantly improved for commercial tenants (e.g., identifies "US Export Assistance Center" instead of just "400 Andrews St").

### Strategy 2: Nearby Search fallback (`nearbysearch`)
*   **Description**: Searches for businesses in the immediate vicinity (30m radius) of the building's coordinates.
*   **API Endpoint**: `nearbysearch/json`
*   **Logic**:
    1.  Tight 30m radius centered on the building footprint.
    2.  Explicit `type=establishment` filter.
    3.  Iterates through results to find the most relevant business occupant that isn't a street/locality marker.
*   **Effectiveness**: **Medium**. Good for multi-tenant buildings or when the address search doesn't explicitly link to a business profile.

### Strategy 3: Place Details Deep Enrichment
*   **Description**: Once a `place_id` is identified by the above strategies, pulls the full profile.
*   **API Endpoint**: `details/json`
*   **Logic**: Fetches `name, types, rating, user_ratings_total, business_status, website, formatted_phone_number`.
*   **Effectiveness**: **High**. Provides the key contact info (website/phone) and credibility metrics (rating) displayed in the dashboard and lead modals.

---

## ☀️ Solar Potential Enrichment Strategies

### Strategy 1: Building Insights (`findClosest`)
*   **Description**: Uses Google Solar API to get high-resolution building geometry and potential.
*   **API Endpoint**: `buildingInsights:findClosest`
*   **Data Points Collected**:
    *   **Max Panel Capacity**: Total panels the roof can accommodate.
    *   **Annual Energy Yield (kWh)**: Calculated based on local irradiance and roof shade.
    *   **Payback Period**: Financial viability check.
    *   **Carbon Offset**: Environmental impact metrics.

---

## 🎯 Targeted ICP (Ideal Customer Profile) Strategy
*   **Description**: Categorizes leads into specific industrial/commercial buckets to prioritize campaigns based on energy load and facility type.
*   **Buckets**:
    1.  **🏭 Tier 1: Manufacturing/Industrial**: Machining, assembly, steel, plastics, plants. (High kWh Load)
    2.  **📦 Tier 1: Warehousing/Logistics**: Distribution centers, storage, freight, supply. (Large Flat Roofs)
    3.  **❄️ Tier 1: Food/Beverage/Cold Load**: Breweries, cold storage, dairies, processing. (Constant High Load)
    4.  **🚗 Tier 2: Auto/Equipment**: Dealerships, fleet services, repair centers. (EV Angle)
    5.  **⛪ Tier 2: Nonprofits/Community**: Churches, youth centers, clubs. (Trust/Goodwill)
*   **Exclusions**: Small medical clinics, multi-tenant high-rises, and residential complexes are de-prioritized to maximize ROI.

---

## 🏗️ Building Qualification Strategies

### Strategy 1: Minimum Scale Filtering
*   **Description**: Automatic disqualification of buildings below a certain industrial/commercial threshold.
*   **Current Threshold**: **3,000 sq ft** minimum roof area (Reduced from 5k to catch priority ICPs).
*   **Exception**: High-priority ICPs (Manufacturing/Logistics) or verified landmarks are preserved regardless of size.

---

## 📈 Scoring Algorithm (The "Waterfall" Score)

Leads are scored on a scale of 0-100 following a weighted analytical model:

| Component | Max Points | Logic |
| :--- | :--- | :--- |
| **Solar Potential** | 40 pts | 250+ panels = Max. Incorporates proxy footprint math if API fails. |
| **ICP Relevance** | 25 pts | Tier 1 = +25, Tier 2 = +15, Exclusions = -30. |
| **Financial Viability** | 20 pts | +15 for viability, +5 bonus for <7yr payback. |
| **Building Type** | 10 pts | Industrial/Warehouse (10) > Commercial (8) > Retail (5). |
| **Business Data** | 10 pts | +7 for verified tenant, +3 for 4.0+ rating. |

### Configuration Metrics:
* **Proxy Conversion**: 17.5 sqft/panel @ 70% roof efficiency factor.
* **Baseline Score**: 12 pts for non-priority buildings in the system.

---

## 🛠️ The Search Query Toolbox

This section documents the specific queries that have been tested, categorized by their reliability and performance.

### 🗺️ OpenStreetMap (Overpass API) - Discovery Phase

#### ✅ WHAT WORKS (Reliable)
*   **Strategy: Bounding Box (Bbox) Search**
    *   **Logic**: Uses explicit coordinates `(south, west, north, east)` to define a search area. This avoids timeouts and geographical ambiguity.
    *   **Working Query Template**:
        ```overpass
        [out:json][timeout:90];
        (
          way["building"~"industrial|warehouse|factory|manufacturing|storage|cold_storage"]({{bbox}});
          way["amenity"~"place_of_worship"]({{bbox}});
          way["shop"~"car|car_repair"]({{bbox}});
        );
        out center body;
        ```
    *   **Why it works**: Extremely fast (usually < 2s), targets specific ICP types, and doesn't rely on the "Area" server which is often overloaded.

#### ⚠️ WHAT IS RISKY (Unreliable)
*   **Strategy: Named Area Search**
    *   **Logic**: `area[name="Rochester"]->.searchArea;`
    *   **Failure Mode**: Often causes **504 Gateway Timeouts** because the server has to resolve complex city boundaries.
    *   **Ambiguity**: Searching for "Rochester" without a state filter catches results in Minnesota and New York simultaneously.
    *   **Fix**: Added `["addr:state"="NY"]` filter, but Bbox remains the superior method for production.

---

### 🏢 Google Places API - Enrichment Phase

#### ✅ WHAT WORKS (The "Waterfall")
*   **Stage 1: Address + Location Bias**
    *   `findplacefromtext?input=[Address]&inputtype=textquery&locationbias=circle:100@[Lat,Lng]`
    *   **Best for**: Single-tenant industrial buildings.
*   **Stage 2: Landmark Keywords**
    *   Adding keywords like `Plaza`, `Tower`, or `Center` to the address.
    *   **Best for**: Multi-tenant office buildings and downtown commercial hubs.
*   **Stage 3: Proximity Fallback**
    *   `nearbysearch?location=[Lat,Lng]&radius=30&type=establishment`
    *   **Best for**: When the exact address yields no business profile.

#### ❌ WHAT FAILS (Deprecated)
*   **Strategy: Broad Keyword Searches**
    *   Searching for `industrial at [Address]` without a specific coordinate bias.
    *   **Result**: Often returns the city's "Industrial District" center point rather than the specific building.
*   **Strategy: High-Radius Nearby Search**
    *   Using a radius > 100m.
    *   **Result**: Too much "noise" (neighboring businesses) makes it impossible to know which business is actually inside the target footprint.
