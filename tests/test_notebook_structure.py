import os
import json
import pytest

def test_notebook_valid_json():
    notebook_path = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'train_yolov8n_colab.ipynb')
    with open(notebook_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "cells" in data
    assert "nbformat" in data
    assert len(data["cells"]) > 0
    
    has_markdown = any(cell["cell_type"] == "markdown" for cell in data["cells"])
    has_code = any(cell["cell_type"] == "code" for cell in data["cells"])
    
    assert has_markdown
    assert has_code
