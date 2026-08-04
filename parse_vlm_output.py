import json

def parse_vlm_output(json_string):
    """Parse VLM JSON output into Python objects."""
    return json.loads(json_string)