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

## 🏗️ Building Qualification Strategies

### Strategy 1: Minimum Scale Filtering
*   **Description**: Automatic disqualification of buildings below a certain industrial/commercial threshold.
*   **Current Threshold**: **5,000 sq ft** minimum roof area.
*   **Logic**: Uses Solar API `maxArrayAreaMeters2` if available (precise), falling back to estimated footprint from ingestion.
*   **Outcome**: Buildings below 5,000 sq ft are marked `ineligible` and filtered from the dashboard to focus on high-value commercial installs.

---

## 📈 Scoring Algorithm (Current Version)

Leads are scored on a scale of 0-100 based on the following weights:
1.  **Solar Capacity (0-40pts)**: Based on total panel count (100+ panels = max points).
2.  **Financial Viability (0-20pts)**: Bonus for quick payback (<7 years).
3.  **Building Type (0-15pts)**: Industrial and Warehouse prioritized.
4.  **Business Presence (0-10pts)**: Verified tenant/company identified.
5.  **Sunshine Hours (0-10pts)**: Regional irradiance metrics.
6.  **Environmental Impact (0-5pts)**: Carbon offset potential.
