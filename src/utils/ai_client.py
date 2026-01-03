
import os
import json
import random
from typing import List
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class SolarIntelAI:
    """
    AI Intelligence Layer for Solar Discovery.
    Uses OpenAI to generate creative, niche search strategies.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. AI features will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    def generate_search_terms(self, city: str, count: int = 3, existing_topics: List[str] = []) -> List[str]:
        """Generate specific search terms for a given city"""
        if not self.client:
            return []

        # Context for the AI
        prompt = f"""
        You are a commercial solar sales strategist targeting {city}, NY.
        
        Generate {count} highly specific, distinct business categories or search terms to find buildings 
        with large roofs and high energy usage (Tier 1 ICPs).
        
        Target Categories:
        - Manufacturing/Industrial (e.g., "Plastic fabrication", "Steel service center")
        - Logistics/Warehousing (e.g., "Cold chain logistics", "Distribution warehouse")
        - Specialized (e.g., "Auto auction", "Data center", "Mega church")
        
        Avoid generic terms like "Industrial park" if possible, go for specific tenant types.
        Do NOT include these terms: {', '.join(existing_topics[:10])}
        
        Return ONLY a JSON list of strings. Example: ["Injection molding in {city}", "Refrigerated warehouse {city}"]
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # Or gpt-3.5-turbo 
                messages=[
                    {"role": "system", "content": "You are a helpful solar data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content
            # Clean formatting if AI returns markdown code block
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return []
            
    def qualify_lead(self, business_name: str, types: List[str]) -> dict:
        """Estimate likelihood of being a good solar lead"""
        if not self.client:
            return {"score": 0, "reason": "No AI Key"}
            
        prompt = f"""
        Rate the commercial solar potential of '{business_name}' (Types: {types}) on a scale of 1-10.
        Consider roof size likelihood and energy usage.
        Return JSON: {{"score": int, "reason": "short string"}}
        """
        # ... Implementation for later ...
        return {"score": 0, "reason": "Not implemented"}
