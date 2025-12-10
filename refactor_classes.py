#!/usr/bin/env python3
"""
Script to extract individual classes from Django files into separate files.
Following ClassName+Layer naming convention.
"""

import ast
import os
import re
from pathlib import Path

def extract_classes_from_file(file_path, layer_name):
    """Extract individual classes from a Python file using AST."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []
    
    classes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get the start and end lines of the class
            start_line = node.lineno
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(content.split('\n'))
            
            # Extract class code
            lines = content.split('\n')
            class_lines = lines[start_line-1:end_line]
            class_code = '\n'.join(class_lines)
            
            # Remove comments
            class_code = remove_comments(class_code)
            
            # Get imports from the original file
            imports = extract_imports(content)
            
            classes.append({
                'name': node.name,
                'code': imports + '\n\n' + class_code,
                'start_line': start_line,
                'end_line': end_line
            })
    
    return classes

def extract_imports(content):
    """Extract import statements from the file."""
    lines = content.split('\n')
    imports = []
    
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith('import ') or 
            stripped.startswith('from ') or
            stripped.startswith('from .')):
            imports.append(line)
    
    return '\n'.join(imports)

def remove_comments(code):
    """Remove all comments from Python code."""
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove inline comments
        if '#' in line:
            # Keep the part before # if it's not in a string
            in_string = False
            quote_char = None
            cleaned_line = ''
            
            for i, char in enumerate(line):
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                
                if char == '#' and not in_string:
                    break
                cleaned_line += char
            
            line = cleaned_line.rstrip()
        
        # Skip empty lines or lines that are just whitespace
        if line.strip():
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def get_layer_suffix(layer_name):
    """Get the suffix for the layer name."""
    suffix_map = {
        'serializers': 'Serializers',
        'models': 'Models',
        'views': 'Views',
        'services': 'Service'
    }
    return suffix_map.get(layer_name, layer_name.capitalize())

def process_file(file_path, output_dir, layer_name):
    """Process a single file and extract classes."""
    print(f"Processing {file_path}...")
    
    classes = extract_classes_from_file(file_path, layer_name)
    layer_suffix = get_layer_suffix(layer_name)
    
    for class_info in classes:
        class_name = class_info['name']
        file_name = f"{class_name}{layer_suffix}.py"
        output_path = os.path.join(output_dir, file_name)
        
        # Write the class to its own file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(class_info['code'])
        
        print(f"  Created {output_path}")

def main():
    """Main function to process all files."""
    base_dir = Path('/home/jude/code/NoCode_Backend/apps/')
    
    # Define which files to process
    files_to_process = [
        # Foundation
        ('foundation/serializers/org_serializers.py', 'foundation/serializers/', 'serializers'),
        ('foundation/serializers/user_serializers.py', 'foundation/serializers/', 'serializers'),
        ('foundation/serializers/billing_serializers.py', 'foundation/serializers/', 'serializers'),
        ('foundation/views/auth_views.py', 'foundation/views/', 'views'),
        ('foundation/views/org_views.py', 'foundation/views/', 'views'),
        ('foundation/views/user_views.py', 'foundation/views/', 'views'),
        ('foundation/views/subscription_views.py', 'foundation/views/', 'views'),
        
        # Studio
        ('studio/serializers.py', 'studio/serializers/', 'serializers'),
        ('studio/user_friendly_serializers.py', 'studio/serializers/', 'serializers'),
        ('studio/views.py', 'studio/views/', 'views'),
        
        # Runtime
        ('runtime/serializers.py', 'runtime/serializers/', 'serializers'),
        ('runtime/views.py', 'runtime/views/', 'views'),
        
        # Automation
        ('automation/serializers.py', 'automation/serializers/', 'serializers'),
        ('automation/serializers/graph_serializers.py', 'automation/serializers/', 'serializers'),
        ('automation/views.py', 'automation/views/', 'views'),
        ('automation/views/graph_views.py', 'automation/views/', 'views'),
        
        # Insights
        ('insights/serializers.py', 'insights/serializers/', 'serializers'),
        ('insights/views.py', 'insights/views/', 'views'),
    ]
    
    for file_path, output_dir, layer_name in files_to_process:
        full_path = base_dir / file_path
        full_output_dir = base_dir / output_dir
        
        # Create output directory if it doesn't exist
        full_output_dir.mkdir(parents=True, exist_ok=True)
        
        if full_path.exists():
            process_file(full_path, full_output_dir, layer_name)
        else:
            print(f"Warning: {full_path} does not exist")
    
    print("\nRefactoring complete!")
    print("Next steps:")
    print("1. Update all __init__.py files to import from new locations")
    print("2. Test that all imports work correctly")
    print("3. Remove old files after verification")

if __name__ == '__main__':
    main()
