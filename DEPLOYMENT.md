
# Solar Leads Dashboard - Deployment & Migration Guide

Use this guide to run the dashboard on a different computer while keeping your discovered leads.

## 1. Prerequisites

On the new computer, ensure you have:
*   **Node.js** (v18 or higher)
*   **Python** (v3.10 or higher)
*   **Git**

## 2. Clone the Repository

```bash
git clone <your-repo-url>
cd solar-leads-finder
```

## 3. Environment Setup

### Backend (Python)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

*Note: If `requirements.txt` is missing, run `pip install openai pandas requests python-dotenv loguru`.*

### Frontend (Next.js)
```bash
cd frontend
npm install
cd ..
```

### API Keys
Create a `.env` file in the root directory (copy `.env.example` if it exists) and add your keys:
```bash
GOOGLE_MAPS_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

## 4. ⚠️ CRITICAL: Migrating Data

Your collected leads are stored in local CSV/JSON files that are **ignored by Git** to protect your data. You must manually transfer them.

**Copy these files from your old computer to the new one:**

| Source File | Destination on New PC | Description |
| :--- | :--- | :--- |
| `data/raw/enriched_buildings.csv` | `data/raw/enriched_buildings.csv` | **Main Database**: Contains all your leads and scores. |
| `data/raw/discovery_history.json` | `data/raw/discovery_history.json` | **AI Memory**: Prevents re-searching the same things. |

*If you skip this step, the dashboard will open empty!*

## 5. Running the Application

Open two terminal tabs.

**Terminal 1 (Frontend Dashboard):**
```bash
cd frontend
npm run dev
```

**Terminal 2 (Discovery Engine - Optional testing):**
```bash
# Only needed if you want to manually trigger discovery from CLI
source venv/bin/activate
python src/discovery/run_discovery.py
```

Open your browser to `http://localhost:3000`. You should see all your leads!
