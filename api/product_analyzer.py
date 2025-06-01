import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def analyze_product(product_name: str) -> Dict:
    """
    Analyze a product and return its raw materials and their sources.
    
    Args:
        product_name (str): Name of the product to analyze
        
    Returns:
        Dict: Dictionary containing the analysis results
    """
    # Load the materials database
    materials_db = load_materials_database()
    
    # Create a more concise prompt
    prompt = f"""
    Analyze the product "{product_name}" and list ONLY the raw materials it contains.
    Focus on basic materials like metals, plastics, glass, etc.
    
    Format the response as a JSON object with this structure:
    {{
        "product": "{product_name}",
        "raw_materials": ["material1", "material2", ...]
    }}
    """
    
    try:
        # Call ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better analysis
            messages=[
                {"role": "system", "content": "You are a supply chain analysis expert. Your task is to identify raw materials in products."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent results
        )
        
        # Extract and parse the response
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        return {
            "error": f"Failed to analyze product: {str(e)}",
            "product": product_name,
            "raw_materials": []
        }

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
        print(f"\nAnalyzing {product}...")
        result = analyze_product(product)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 