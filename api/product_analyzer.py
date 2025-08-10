import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def safe_json_loads(s: str):
    if not s or not isinstance(s, str):
        return []
    
    try:
        # Try direct JSON parsing first
        return json.loads(s)
    except json.JSONDecodeError:
        try:
            # Try to extract JSON from markdown or other text
            import re
            # Look for JSON arrays or objects
            json_match = re.search(r'\[.*\]|\{.*\}', s, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print(f"Could not extract JSON from: {s[:100]}...")
                return []
        except Exception as e:
            print(f"Error in safe_json_loads: {e}")
            return []

def load_materials_database() -> Dict:
    """Load the materials database from products.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "products.json")
    with open(json_path, "r") as f:
        return json.load(f)

def flatten_materials_db(materials_db: Dict, path: List[str] = None) -> List[Dict]:
    """
    Flatten the nested materials database into a list of materials with their full paths.
    This handles variable nesting depth in the JSON structure.
    """
    if path is None:
        path = []
    
    materials = []
    
    for key, value in materials_db.items():
        current_path = path + [key]
        
        if isinstance(value, dict):
            # If the dict has 'regions', it's a material
            if 'regions' in value:
                materials.append({
                    'name': key,
                    'path': current_path,
                    'regions': value['regions']
                })
            # Otherwise, it's a category or subcategory, so recurse
            else:
                materials.extend(flatten_materials_db(value, current_path))
    
    return materials

def print_material_structure(materials_db: Dict) -> None:
    """Helper function to print the structure of materials in the database"""
    materials = flatten_materials_db(materials_db)
    print("\nMaterials Database Structure:")
    print("=" * 50)
    for material in materials:
        print(f"Material: {material['name']}")
        print(f"  Path: {' > '.join(material['path'])}")
        print(f"  Sample Regions: {', '.join(material['regions'][:3])}...")
    print("=" * 50)

def analyze_product(product_name: str, location: Optional[str] = None) -> Dict:
    """
    Given a product and (optionally) a location, run the three-step GPT pipeline:
    1. Get likely locations
    2. Get materials
    3. Get material source locations (mapping)
    Return a combined result dictionary.
    """
    try:
        # Load data
        materials_db = load_materials_database()
        flattened = flatten_materials_db(materials_db)
        valid_materials = sorted({m['name'] for m in flattened})
        material_regions = {m['name']: m['regions'] for m in flattened}
        
        # Load valid locations from locations.json
        script_dir = os.path.dirname(os.path.abspath(__file__))
        locations_path = os.path.join(script_dir, "locations.json")
        with open(locations_path, "r") as f:
            locations_data = json.load(f)
        valid_locations = locations_data['countries'] + locations_data['us_cities'] + list(locations_data['city_to_country'].keys())

        # Step 1: Product + Location -> 3 likely locations
        try:
            locations = gpt_product_to_locations(product_name, location or "global")
            if not locations:
                locations = ["China", "Taiwan", "South Korea"]  # Fallback
        except Exception as e:
            print(f"Error in gpt_product_to_locations: {e}")
            locations = ["China", "Taiwan", "South Korea"]  # Fallback

        # Step 2: Product -> Materials
        try:
            materials = gpt_product_to_materials(product_name)
            if not materials:
                materials = ["aluminum", "copper", "silicon"]  # Fallback
        except Exception as e:
            print(f"Error in gpt_product_to_materials: {e}")
            materials = ["aluminum", "copper", "silicon"]  # Fallback

        # Step 3: Materials + Locations -> Material source locations
        try:
            material_locations = gpt_materials_and_locations_to_sources(materials, locations)
            if not material_locations:
                # Create a simple fallback mapping
                material_locations = {material: ["China"] for material in materials}
        except Exception as e:
            print(f"Error in gpt_materials_and_locations_to_sources: {e}")
            material_locations = {material: ["China"] for material in materials}

        return {
            "raw_materials": materials,
            "material_source_locations": material_locations,
            "risk_score": 0  # Will be calculated separately
        }
        
    except Exception as e:
        print(f"Critical error in analyze_product: {e}")
        # Return a safe fallback response
        return {
            "raw_materials": ["aluminum", "copper", "silicon"],
            "material_source_locations": {
                "aluminum": ["China"],
                "copper": ["China"], 
                "silicon": ["China"]
            },
            "risk_score": 0
        }

def gpt_product_to_locations(product_name: str, location: Optional[str], valid_locations: List[str]) -> List[str]:
    """
    Given a product and a location, return the 3 most likely locations (from valid_locations) where the product could have been manufactured or sourced.
    """
    system_prompt = (
        f"You are a supply chain analysis expert. "
        f"Only use locations from this list: {valid_locations}. "
        f"Do not invent new locations."
    )
    user_prompt = (
        f"Given the product '{product_name}' and the location '{location}', "
        f"return the 3 most likely locations where this product could have been manufactured or sourced, as a JSON array."
    )
    print("\n==== SYSTEM PROMPT (gpt_product_to_locations) ====")
    print(system_prompt)
    print("\n==== USER PROMPT (gpt_product_to_locations) ====")
    print(user_prompt)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return safe_json_loads(response.choices[0].message.content)

def gpt_product_to_materials(product_name: str, valid_materials: List[str]) -> List[str]:
    """
    Given a product, return the most relevant raw materials (from valid_materials).
    """
    system_prompt = (
        f"You are a supply chain analysis expert. "
        f"Only use materials from this list: {valid_materials}. "
        f"Do not invent new materials."
    )
    user_prompt = (
        f"Given the product '{product_name}', return the most relevant raw materials for this product as a JSON array."
    )
    print("\n==== SYSTEM PROMPT (gpt_product_to_materials) ====")
    print(system_prompt)
    print("\n==== USER PROMPT (gpt_product_to_materials) ====")
    print(user_prompt)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return safe_json_loads(response.choices[0].message.content)

def gpt_materials_and_locations_to_sources(materials: List[str], locations_of_interest: List[str], material_regions: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Given a list of materials and 3 locations of interest, return up to 3 likely source locations for each material as a mapping.
    """
    relevant_material_regions = {m: material_regions[m] for m in materials if m in material_regions}
    system_prompt = (
        f"You are a supply chain analysis expert. "
        f"Only use locations from this list: {locations_of_interest}. "
        f"Do not invent new locations."
    )
    user_prompt = (
        f"Given the materials {materials} and the regions where each is sourced: {json.dumps(relevant_material_regions)}, "
        f"return a JSON object mapping each material to an array of up to 3 likely source locations for that material. Example format: {{'material1': ['loc1', 'loc2', 'loc3'], ...}}. "
        f"Each value must be an array of strings. Respond ONLY with the JSON object, and do not include any explanation or extra text."
    )
    print("\n==== SYSTEM PROMPT (gpt_materials_and_locations_to_sources) ====")
    print(system_prompt)
    print("\n==== USER PROMPT (gpt_materials_and_locations_to_sources) ====")
    print(user_prompt)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return safe_json_loads(response.choices[0].message.content)

def main():
    """Example usage of the product analyzer"""
    # First test flatten_materials_db
    print("\nTesting flatten_materials_db:")
    print("=" * 50)
    materials_db = load_materials_database()
    flattened = flatten_materials_db(materials_db)
    print(f"Total materials found: {len(flattened)}")
    print("\nSample of materials (first 5):")
    for material in flattened[:5]:
        print(f"\nMaterial: {material['name']}")
        print(f"Path: {' > '.join(material['path'])}")
        print(f"Regions: {', '.join(material['regions'][:3])}...")
    print("=" * 50)
    
    # Then proceed with product analysis
    test_products = [
        "smartphone",
        "electric car",
        "cotton t-shirt",
        "laptop computer"
    ]
    
    for product in test_products:
        print(f"\nAnalyzing {product} (location: New York)...")
        result = analyze_product(product, location="New York")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 