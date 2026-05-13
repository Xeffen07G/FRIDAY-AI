import os
import sys
import importlib.util
from pathlib import Path

def validate_imports(directory):
    """Recursively attempts to import all python files in the directory."""
    backend_path = os.path.abspath(directory)
    if backend_path not in sys.path:
        sys.path.append(backend_path)
    
    # Add parent to path to handle absolute imports like 'backend.core'
    parent_path = os.path.abspath(os.path.join(backend_path, ".."))
    if parent_path not in sys.path:
        sys.path.append(parent_path)

    results = []
    
    for path in Path(directory).rglob("*.py"):
        if "__init__" in path.name: continue
        if "scripts" in str(path): continue
        
        # Construct module name relative to current directory
        rel_path = path.relative_to(directory)
        module_name = ".".join(rel_path.with_suffix("").parts)
        
        try:
            # First try direct import
            importlib.import_module(module_name)
            results.append({"module": module_name, "status": "PASS", "error": None})
        except Exception as e:
            # Try absolute import (from backend)
            try:
                abs_module_name = "backend." + module_name
                importlib.import_module(abs_module_name)
                results.append({"module": abs_module_name, "status": "PASS", "error": None})
            except Exception as e2:
                results.append({"module": module_name, "status": "FAIL", "error": f"{str(e)} | {str(e2)}"})

    return results

if __name__ == "__main__":
    print("--- F.R.I.D.A.Y. Import Validation Audit ---")
    audit_results = validate_imports("backend")
    
    failed = [r for r in audit_results if r['status'] == "FAIL"]
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/IMPORT_VALIDATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Import Validation Report\n\n")
        f.write(f"**Total Modules Audited:** {len(audit_results)}\n")
        f.write(f"**Pass:** {len(audit_results) - len(failed)}\n")
        f.write(f"**Fail:** {len(failed)}\n\n")
        
        if failed:
            f.write("## Failed Imports\n")
            f.write("| Module | Error |\n| :--- | :--- |\n")
            for r in failed:
                f.write(f"| {r['module']} | {r['error']} |\n")
        else:
            f.write("## All imports validated successfully.\n")

    print(f"Audit complete. Results saved to docs/IMPORT_VALIDATION_REPORT.md")
    if failed:
        print(f"Warning: {len(failed)} imports failed validation.")
        # sys.exit(1) # Don't exit yet, let's see the failures
