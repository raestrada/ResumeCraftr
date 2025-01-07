import json
import os
import re


def merge_json_files(target_file: str, source_file: str, output_path: str) -> None:
    """
    Merges two JSON files and writes the merged result into an output file.
    - Retains existing values in the target JSON.
    - Adds missing keys from the source JSON.
    - Saves the merged result to the specified output path.

    Args:
        target_file (str): Path to the primary JSON file.
        source_file (str): Path to the secondary JSON file.
        output_path (str): Path where the merged JSON will be saved.
    """

    # Load target JSON file (or create an empty dictionary if not found)
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    else:
        target_data = {}

    # Load source JSON file (or create an empty dictionary if not found)
    if os.path.exists(source_file):
        with open(source_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
    else:
        source_data = {}

    # Merge source_data into target_data without overwriting existing values
    for key, value in source_data.items():
        if key not in target_data:
            target_data[key] = value

    # Save the merged JSON into output_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(target_data, f, indent=4, ensure_ascii=False)

    print(f"Merged JSON successfully saved to: {output_path}")


def clean_json_response(response):
    """
    Extrae solo el JSON válido de la respuesta de OpenAI eliminando cualquier texto adicional.
    """
    try:
        match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)
        if match:
            return json.loads(match.group(0))  # Convierte el JSON a objeto Python
        return None  # Retorna None si no encuentra JSON válido
    except json.JSONDecodeError:
        return None  # Retorna None si la conversión a JSON falla
