import json
from pathlib import Path
from typing import Any, Dict, List, Optional

class LawLoader:
    def __init__(self, laws_directory: str = "backend/data/laws"):
        self.laws_directory = Path(laws_directory)
        self._law_cache: Dict[str, Dict[str, Any]] = {}

        if not self.laws_directory.is_dir():
            raise FileNotFoundError(
                f"The specified laws directory does not exist: {self.laws_directory.resolve()}"
            )

        self._load_all_laws_from_disk()

    def _load_all_laws_from_disk(self):
        print(f"--- LawLoader: Initializing and loading laws from '{self.laws_directory.resolve()}' ---")
        
        json_files = list(self.laws_directory.glob("*.json"))

        if not json_files:
            print("WARNING: No .json law files found in the directory.")
            return

        for law_file_path in json_files:
            # The law_id is the filename without the .json extension (e.g., "GDPR_EU")
            law_id = law_file_path.stem
            try:
                with open(law_file_path, 'r', encoding='utf-8') as f:
                    law_data = json.load(f)
                    # We can do a quick validation to ensure the file's ID matches its name
                    if law_data.get("law_id") != law_id:
                         print(f"WARNING: law_id '{law_data.get('law_id')}' in {law_file_path.name} does not match filename. Using filename '{law_id}' as the key.")
                    self._law_cache[law_id] = law_data
                    print(f"  [SUCCESS] Loaded '{law_file_path.name}'")
            except json.JSONDecodeError:
                print(f"  [ERROR] Failed to decode JSON from '{law_file_path.name}'. The file may be corrupted.")
            except Exception as e:
                print(f"  [ERROR] An unexpected error occurred while loading '{law_file_path.name}': {e}")
        
        print(f"--- LawLoader: Successfully loaded {len(self._law_cache)} laws. ---")

    def get_law_by_id(self, law_id: str) -> Optional[Dict[str, Any]]:
        return self._law_cache.get(law_id)

    def get_all_laws(self) -> List[Dict[str, Any]]:
        return list(self._law_cache.values())

    def get_laws_by_jurisdiction(self, jurisdiction_code: str) -> List[Dict[str, Any]]:
        return [
            law_data for law_data in self._law_cache.values()
            if law_data.get("metadata", {}).get("jurisdiction") == jurisdiction_code.upper()
        ]

# Test the LawLoader functionality
if __name__ == "__main__":
    try:
        # 1. Instantiate the loader
        law_loader = LawLoader()
        print("\n--- Testing LawLoader ---")

        # 2. Get the total number of laws loaded
        all_laws = law_loader.get_all_laws()
        print(f"\nTotal laws loaded: {len(all_laws)}")

        # 3. Test fetching a specific law by ID
        print("\nFetching GDPR_EU by ID...")
        gdpr_law = law_loader.get_law_by_id("GDPR_EU")
        if gdpr_law:
            print(f"  Successfully found: {gdpr_law['metadata']['name']}")
        else:
            print("  GDPR_EU not found.")
            
        # 4. Test fetching laws by jurisdiction
        print("\nFetching all laws for jurisdiction 'MY'...")
        my_laws = law_loader.get_laws_by_jurisdiction("MY")
        if my_laws:
            print(f"  Found {len(my_laws)} laws for MY:")
            for law in my_laws:
                print(f"    - {law['metadata']['name']}")
        else:
            print("  No laws found for MY.")

    except FileNotFoundError as e:
        print(f"\nERROR: Could not run test. {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during testing: {e}")