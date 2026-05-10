#!/usr/bin/env python3
"""
Script to fix all pipeline files to inherit from SafePipeline instead of BasePipeline
"""

import os
import re

def fix_pipeline_file(file_path):
    """Fix a single pipeline file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file needs fixing
        if 'from core.base_pipeline import BasePipeline' not in content:
            return False
        
        # Replace import
        content = re.sub(
            r'from core\.base_pipeline import BasePipeline',
            'from core.base_pipeline import SafePipeline',
            content
        )
        
        # Replace class inheritance
        content = re.sub(
            r'class (\w+Pipeline)\(BasePipeline\):',
            r'class \1(SafePipeline):',
            content
        )
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all pipeline files"""
    pipelines_dir = "/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/pipelines"
    
    fixed_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk(pipelines_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total_count += 1
                if fix_pipeline_file(file_path):
                    fixed_count += 1
    
    print(f"\n🎯 Summary: Fixed {fixed_count}/{total_count} pipeline files")

if __name__ == "__main__":
    main()
