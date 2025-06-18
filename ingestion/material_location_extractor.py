import logging

# Recursive function to create a material-location map from nested materials data
def create_material_location_map(materials_data):
    material_locations = {}
    
    def process_node(node, path=None):
        if path is None:
            path = []
        if isinstance(node, dict):
            if 'regions' in node:
                material_name = path[-1] if path else None
                if material_name:
                    material_locations[material_name] = node['regions']
            else:
                for key, value in node.items():
                    process_node(value, path + [key])
    if 'raw_materials' in materials_data:
        process_node(materials_data['raw_materials'])
    return material_locations

# Function to find material/location mentions in text
def find_material_location_mentions(text, material_locations):
    mentions = []
    text = text.lower()
    # Check each material
    for material, locations in material_locations.items():
        if material.lower() in text:
            for location in locations:
                if location.lower() in text:
                    mentions.append((material, location))
            mentions.append((material, None))
    # Check each location (for weather data or location-only mentions)
    all_locations = set()
    for locations in material_locations.values():
        all_locations.update(locations)
    for location in all_locations:
        if location.lower() in text:
            mentions.append((None, location))
    return mentions 