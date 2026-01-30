#!/usr/bin/env python3
"""
JSON to Markdown Converter
Konvertiert JSON-Daten mit text und list Elementen in Markdown.
Sortiert nach page_idx und vertikaler Position (bbox[1]).
"""

import json
import sys
from pathlib import Path


def load_json(filepath):
    """Lädt JSON-Daten aus einer Datei."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def sort_elements(elements):
    """
    Sortiert Elemente nach Seite (page_idx) und vertikaler Position (bbox[1]).
    """
    return sorted(elements, key=lambda x: (
        x.get('page_idx', 0),
        x.get('bbox', [0, 0, 0, 0])[1]
    ))


def convert_to_markdown(data):
    """
    Konvertiert JSON-Daten in Markdown.
    
    Args:
        data: Liste von JSON-Objekten
        
    Returns:
        String mit Markdown-Inhalt
    """
    # Filtere nur 'text' und 'list' Elemente
    relevant_elements = [
        elem for elem in data 
        if elem.get('type') in ['text', 'list']
    ]
    
    # Sortiere nach Seite und Position
    sorted_elements = sort_elements(relevant_elements)
    
    markdown_lines = []
    current_page = None
    
    for elem in sorted_elements:
        page_idx = elem.get('page_idx', 0)
        elem_type = elem.get('type')
        
        # Neue Seite beginnt
        if page_idx != current_page:
            if current_page is not None:
                markdown_lines.append('\n---\n')  # Seitentrennlinie
            markdown_lines.append(f'## Seite {page_idx + 1}\n\n')
            current_page = page_idx
        
        # Text-Element verarbeiten
        if elem_type == 'text':
            text = elem.get('text', '').strip()
            text_level = elem.get('text_level', 0)
            
            if text:
                if text_level > 0:
                    # Überschrift (text_level 1 = ###, text_level 2 = ####, etc.)
                    heading_level = text_level + 2
                    markdown_lines.append(f'{"#" * heading_level} {text}\n\n')
                else:
                    # Normaler Text
                    markdown_lines.append(f'{text}\n\n')
        
        # List-Element verarbeiten
        elif elem_type == 'list':
            list_items = elem.get('list_items', [])
            sub_type = elem.get('sub_type', '')
            
            if list_items:
                for item in list_items:
                    item = item.strip()
                    if item:
                        # Alle Listen als Bullet-Listen
                        markdown_lines.append(f'- {item}\n')
                markdown_lines.append('\n')
    
    return ''.join(markdown_lines)


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Usage: python json_to_markdown.py <input.json> [output.md]")
        print("\nBeispiel:")
        print("  python json_to_markdown.py input.json output.md")
        print("  python json_to_markdown.py input.json  # gibt auf stdout aus")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Prüfe ob Input-Datei existiert
    if not Path(input_file).exists():
        print(f"Fehler: Datei '{input_file}' nicht gefunden!")
        sys.exit(1)
    
    try:
        # JSON laden
        print(f"Lade JSON aus '{input_file}'...")
        data = load_json(input_file)
        
        # Zu Markdown konvertieren
        print("Konvertiere zu Markdown...")
        markdown_content = convert_to_markdown(data)
        
        # Ausgabe
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"✓ Markdown erfolgreich gespeichert in '{output_file}'")
            print(f"  Anzahl Zeichen: {len(markdown_content):,}")
            print(f"  Anzahl Zeilen: {markdown_content.count(chr(10)):,}")
        else:
            print("\n" + "="*60)
            print(markdown_content)
            print("="*60)
    
    except json.JSONDecodeError as e:
        print(f"Fehler beim Parsen der JSON-Datei: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()