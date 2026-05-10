#!/usr/bin/env python3
"""
Script to standardize all pipelines to use unified BypassResponse contract
"""

import os
import re
import sys
from pathlib import Path

def standardize_pipeline_file(file_path):
    """Standardize a single pipeline file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Replace print() statements with tracer.info()
        print_pattern = r'print\((.*?)\)'
        content = re.sub(print_pattern, r'self.tracer.info(\1)', content)
        
        # 2. Replace error field with error_reason in BypassResponse
        content = content.replace('error=', 'error_reason=')
        
        # 3. Replace response_time with latency in success cases
        # Keep response_time for backward compatibility but add latency
        bpass_pattern = r'(BypassResponse\(\s*success=.*?response_time=)([^,\)]+)([,\)]))'
        def add_latency(match):
            start = match.group(1)
            time_val = match.group(2)
            end = match.group(3)
            # Add latency field before response_time
            return f"{start}latency={time_val}, response_time={time_val}{end}"
        content = re.sub(bpass_pattern, add_latency, content, flags=re.DOTALL)
        
        # 4. Fix error cases to include latency
        error_pattern = r'(BypassResponse\(\s*success=False,\s*error_reason=.*?response_time=)([^,\)]+)([,\)]))'
        def fix_error_latency(match):
            start = match.group(1)
            time_val = match.group(2)
            end = match.group(3)
            return f"{start}latency={time_val}, response_time={time_val}{end}"
        content = re.sub(error_pattern, fix_error_latency, content, flags=re.DOTALL)
        
        # 5. Add _mark_initialized(True) to initialize methods
        init_pattern = r'(def initialize\(self, config: Dict\[str, Any\]\) -> bool:.*?return True)'
        def add_mark_initialized(match):
            init_method = match.group(1)
            # Find the last return True and add _mark_initialized before it
            if 'self._mark_initialized(True)' not in init_method:
                init_method = init_method.replace('return True', 'self._mark_initialized(True)\n        return True')
            return init_method
        content = re.sub(init_pattern, add_mark_initialized, content, flags=re.DOTALL)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Standardized: {file_path}")
            return True
        else:
            print(f"⚪ No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")
        return False

def main():
    """Main function to standardize all pipeline files"""
    pipelines_dir = Path("/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/pipelines")
    
    # Find all Python files in pipelines directory
    pipeline_files = list(pipelines_dir.rglob("*.py"))
    
    # Skip __init__.py files
    pipeline_files = [f for f in pipeline_files if f.name != "__init__.py"]
    
    print(f"Found {len(pipeline_files)} pipeline files to standardize...")
    
    standardized_count = 0
    for file_path in pipeline_files:
        if standardize_pipeline_file(file_path):
            standardized_count += 1
    
    print(f"\n✅ Standardized {standardized_count} pipeline files")
    print(f"⚪ {len(pipeline_files) - standardized_count} files already compliant")

if __name__ == "__main__":
    main()
