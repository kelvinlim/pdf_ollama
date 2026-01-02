import yaml
from typing import List, Optional, Type, Any
from pydantic import BaseModel, Field, create_model

def map_yaml_type_to_python(type_str: str) -> Type:
    type_map = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "list[string]": List[str],
        "list[integer]": List[int]
    }
    return type_map.get(type_str.lower().strip(), str)

def generate_model_from_yaml(yaml_path: str) -> Type[BaseModel]:
    with open(yaml_path, 'r') as f:
        schema_defs = yaml.safe_load(f)

    model_fields = {}
    for item in schema_defs:
        field_name = item['item_name']
        description = item.get('question', '')
        
        # Add hint if present
        if item.get('hint'):
            description += f" (Hint: {item['hint']})"
        
        # Add examples if present
        examples = item.get('examples')
        if examples:
            example_str = " | ".join([f"Input: {ex.get('input')} -> Output: {ex.get('output')}" for ex in examples if isinstance(ex, dict)])
            if example_str:
                description += f" [Examples: {example_str}]"
        
        py_type = map_yaml_type_to_python(item.get('output_type', 'string'))
        
        # Handle required vs optional
        if item.get('is_required', False):
            model_fields[field_name] = (py_type, Field(..., description=description))
        else:
            model_fields[field_name] = (Optional[py_type], Field(default=None, description=description))

    return create_model('AcademicPaperExtraction', **model_fields)
