import json
import os
from pathlib import Path

def merge():
    base_file = Path('data/raw/upstate_ny_buildings.json')
    disco_file = Path('data/raw/discovered_icp_leads.json')
    # The dashboard actually looks at data/raw/enriched_buildings.json usually 
    # but let's update everything to be safe.
    output_file = Path('data/raw/enriched_buildings.json')

    if not base_file.exists() or not disco_file.exists():
        print(f"Missing files for merge: {base_file.exists()}, {disco_file.exists()}")
        return

    with open(base_file, 'r') as f:
        base_leads = json.load(f)
    
    with open(disco_file, 'r') as f:
        disco_leads = json.load(f)

    # Use address as de-duplication key
    seen_addresses = {l['address'].lower() for l in base_leads if 'address' in l}
    
    merged = list(base_leads)
    new_count = 0
    for l in disco_leads:
        addr = l.get('address', '').lower()
        if addr and addr not in seen_addresses:
            merged.append(l)
            seen_addresses.add(addr)
            new_count += 1
    
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    # Also save as CSV for easy viewing
    import pandas as pd
    pd.DataFrame(merged).to_csv('data/raw/enriched_buildings.csv', index=False)
    
    print(f"Merged {new_count} new discovered leads into {output_file}")
    print(f"Total leads: {len(merged)}")

if __name__ == '__main__':
    merge()
