import json
import random
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
from src.utils.ai_client import SolarIntelAI

class DiscoveryManager:
    """
    Manages the 'Daily Discovery' automation.
    Tracks which combinations of (Term + City) have been searched to ensure freshness.
    """
    
    def __init__(self):
        self.history_file = Path("data/raw/discovery_history.json")
        self.terms_file = Path("config/discovery_terms.json")
        self.history = self._load_history()
        self.terms = self._load_terms()
        self.cities = ["Rochester", "Buffalo", "Syracuse", "Albany", "Cheektowaga", "Tonawanda", "Henrietta", "Clay"]
        self.ai = SolarIntelAI() # Initialize AI layer

    def _load_history(self) -> dict:
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {"searches": [], "last_run": None}

    def _load_terms(self) -> List[str]:
        if self.terms_file.exists():
            with open(self.terms_file, 'r') as f:
                return json.load(f)
        return ["industrial", "warehouse", "church"]

    def save_history(self):
        self.history["last_run"] = datetime.now().isoformat()
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_next_search_queries(self, count: int = 3) -> List[Tuple[str, str]]:
        """
        Returns a list of (Query, City) tuples.
        Prioritizes AI generation, falls back to history-aware random selection.
        """
        queries = []
        
        # 1. Try AI Generation
        if self.ai.client:
            target_city = random.choice(self.cities)
            # Pass recently used terms to avoid repetition
            recent_terms = [H['term'] for H in self.history['searches'][-20:]]
            
            ai_terms = self.ai.generate_search_terms(target_city, count=count, existing_topics=recent_terms)
            
            for term in ai_terms:
                queries.append((term, target_city))
                # Add to history immediately so we track AI suggestions too
                self.history["searches"].append({
                    "key": f"AI_{term}_{target_city}",
                    "date": datetime.now().isoformat(),
                    "term": term,
                    "city": target_city
                })
                
            if queries:
                return queries

        # 2. Fallback to Permutation Strategy
        attempts = 0
        max_attempts = 50
        
        while len(queries) < count and attempts < max_attempts:
            term = random.choice(self.terms)
            city = random.choice(self.cities)
            key = f"{term}_{city}"
            
            # Check if searched in last 30 days
            already_searched = False
            for entry in self.history["searches"]:
                if entry["key"] == key:
                    date = datetime.fromisoformat(entry["date"])
                    if datetime.now() - date < timedelta(days=30):
                        already_searched = True
                        break
            
            if not already_searched:
                queries.append((f"{term} in {city} NY", city))
                # Record it
                self.history["searches"].append({
                    "key": key,
                    "date": datetime.now().isoformat(),
                    "term": term,
                    "city": city
                })
            
            attempts += 1
            
        return queries

    def add_custom_terms(self, new_terms: List[str]):
        """Allows AI or User to inject new search terms"""
        unique_new = [t for t in new_terms if t not in self.terms]
        self.terms.extend(unique_new)
        with open(self.terms_file, 'w') as f:
            json.dump(self.terms, f, indent=2)
