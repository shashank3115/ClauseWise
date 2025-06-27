import unittest
import sys
import os
from typing import Dict, Any

# This is a standard way to make sure the test file can find your backend modules.
# It adds the project's root directory to the Python path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils.law_loader import LawLoader
from backend.service.RegulatoryEngineService import RegulatoryEngineService

class TestRegulatoryEngine(unittest.TestCase):
    """
    Test suite for the RegulatoryEngineService and its interaction with the LawLoader.
    This suite verifies that the data loading, enrichment, and retrieval logic
    is working correctly with the actual law files and mappings.json structure.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment once for the entire test class.
        This is efficient as it loads the data only one time.
        """
        print("\n--- Setting up TestRegulatoryEngine ---")
        try:
            # Instantiate the core components, just like the main application would.
            cls.law_loader = LawLoader()
            cls.engine = RegulatoryEngineService(cls.law_loader)
            print("LawLoader and RegulatoryEngineService initialized successfully.")
        except FileNotFoundError as e:
            # This will cause all tests to be skipped if data files are not found.
            raise unittest.SkipTest(f"Required data files not found, skipping tests. Error: {e}")

    def test_01_gdpr_eu_enrichment(self):
        """
        Tests if the GDPR_EU law file correctly enriched the base data.
        """
        print("\nRunning test_01_gdpr_eu_enrichment...")
        gdpr_law = self.engine.get_law_details("GDPR_EU")
        
        # 1. Assert that the law was found
        self.assertIsNotNone(gdpr_law, "GDPR_EU law should be loaded and found.")
        
        # 2. Assert that it contains detailed data structure
        self.assertIn("law_id", gdpr_law, "GDPR_EU should have law_id field.")
        self.assertIn("metadata", gdpr_law, "GDPR_EU should have metadata section.")
        self.assertIn("applicability", gdpr_law, "GDPR_EU should have applicability section.")
        self.assertIn("key_provisions", gdpr_law, "GDPR_EU should have key_provisions section.")
        
        # 3. Check specific detailed provisions
        key_provisions = gdpr_law["key_provisions"]
        self.assertIn("Lawful_Basis_for_Processing", key_provisions, "Should contain Lawful_Basis_for_Processing provision.")
        self.assertIn("Data_Subject_Rights", key_provisions, "Should contain Data_Subject_Rights provision.")
        
        # 4. Verify structure of a specific provision
        lawful_basis = key_provisions["Lawful_Basis_for_Processing"]
        self.assertIn("section", lawful_basis, "Provision should have section reference.")
        self.assertIn("description", lawful_basis, "Provision should have description.")
        self.assertIn("requirements", lawful_basis, "Provision should have requirements list.")
        self.assertIn("ai_prompt_guidance", lawful_basis, "Provision should have AI prompt guidance.")
        
        print("  -> PASSED: GDPR_EU is fully enriched with detailed structure.")

    def test_02_pdpa_my_enrichment_and_fix(self):
        """
        Tests PDPA_MY law file enrichment and verifies a specific requirement.
        """
        print("\nRunning test_02_pdpa_my_enrichment_and_fix...")
        pdpa_law = self.engine.get_law_details("PDPA_MY")
        
        self.assertIsNotNone(pdpa_law, "PDPA_MY law should be loaded.")
        
        key_provisions = pdpa_law.get("key_provisions", {})
        self.assertIn("Notice_And_Choice_Principle", key_provisions)
        
        notice_provision = key_provisions["Notice_And_Choice_Principle"]
        self.assertIn("requirements", notice_provision)
        
        # --- THIS IS THE FIX: Added a period to match the JSON data exactly. ---
        expected_requirement = "Must describe the personal data being collected."
        
        # We can still strip the lists to be robust against any future whitespace errors.
        actual_requirements_cleaned = [req.strip() for req in notice_provision["requirements"]]
        
        self.assertIn(expected_requirement, actual_requirements_cleaned,
                      "The requirement string (with period) should be found in the cleaned list.")
        
        print("  -> PASSED: PDPA_MY 'Notice_And_Choice_Principle' requirement verified successfully.")

    def test_03_ccpa_us_enrichment(self):
        """
        Tests CCPA_US law file enrichment and US California-specific provisions.
        """
        print("\nRunning test_03_ccpa_us_enrichment...")
        ccpa_law = self.engine.get_law_details("CCPA_US")
        
        self.assertIsNotNone(ccpa_law, "CCPA_US law should be loaded.")
        
        # Check metadata
        metadata = ccpa_law["metadata"]
        self.assertIn("California Consumer Privacy Act", metadata["name"])
        self.assertEqual(metadata["jurisdiction"], "US")
        
        # Check CCPA-specific provisions
        key_provisions = ccpa_law["key_provisions"]
        self.assertIn("Consumer_Rights", key_provisions, "Should contain consumer rights provision.")
        
        # Verify California-specific consumer rights
        consumer_rights = key_provisions["Consumer_Rights"]
        requirements = consumer_rights["requirements"]
        self.assertTrue(any("Right to Know" in req for req in requirements), "Should include Right to Know.")
        self.assertTrue(any("Right to Delete" in req for req in requirements), "Should include Right to Delete.")
        self.assertTrue(any("Right to Opt-Out" in req for req in requirements), "Should include Right to Opt-Out.")
        
        print("  -> PASSED: CCPA_US is correctly enriched with California-specific provisions.")

    def test_04_employment_act_my_enrichment(self):
        """
        Tests EMPLOYMENT_ACT_MY law file enrichment.
        """
        print("\nRunning test_04_employment_act_my_enrichment...")
        employment_law = self.engine.get_law_details("EMPLOYMENT_ACT_MY")
        
        self.assertIsNotNone(employment_law, "EMPLOYMENT_ACT_MY law should be loaded.")
        
        # Check metadata
        metadata = employment_law["metadata"]
        self.assertIn("Employment Act 1955", metadata["name"])
        self.assertEqual(metadata["jurisdiction"], "MY")
        
        print("  -> PASSED: EMPLOYMENT_ACT_MY is correctly loaded.")

    def test_05_pdpa_sg_enrichment(self):
        """
        Tests PDPA_SG law file enrichment.
        """
        print("\nRunning test_05_pdpa_sg_enrichment...")
        pdpa_sg_law = self.engine.get_law_details("PDPA_SG")
        
        self.assertIsNotNone(pdpa_sg_law, "PDPA_SG law should be loaded.")
        
        # Check metadata
        metadata = pdpa_sg_law["metadata"]
        self.assertIn("Personal Data Protection Act", metadata["name"])
        self.assertEqual(metadata["jurisdiction"], "SG")
        
        print("  -> PASSED: PDPA_SG is correctly loaded.")

    def test_06_jurisdiction_mapping_correctness(self):
        """
        Verifies that jurisdiction mappings correctly return the detailed law files.
        """
        print("\nRunning test_06_jurisdiction_mapping_correctness...")
        
        # Test EU jurisdiction
        eu_laws = self.engine.get_laws_for_jurisdiction("EU")
        self.assertIn("GDPR_EU", eu_laws.keys(), "EU jurisdiction should map to GDPR_EU.")
        
        # Test MY jurisdiction
        my_laws = self.engine.get_laws_for_jurisdiction("MY")
        self.assertIn("PDPA_MY", my_laws.keys(), "MY jurisdiction should map to PDPA_MY.")
        self.assertIn("EMPLOYMENT_ACT_MY", my_laws.keys(), "MY jurisdiction should map to EMPLOYMENT_ACT_MY.")
        
        # Test US jurisdiction
        us_laws = self.engine.get_laws_for_jurisdiction("US")
        self.assertIn("CCPA_US", us_laws.keys(), "US jurisdiction should map to CCPA_US.")
        
        # Test SG jurisdiction
        sg_laws = self.engine.get_laws_for_jurisdiction("SG")
        self.assertIn("PDPA_SG", sg_laws.keys(), "SG jurisdiction should map to PDPA_SG.")
        
        print("  -> PASSED: All jurisdiction mappings return correct detailed laws.")

    def test_07_compliance_checklist_structure(self):
        """
        Tests that compliance checklists contain the correct structure for AI processing.
        """
        print("\nRunning test_07_compliance_checklist_structure...")
        
        # Test EU Data Processing Agreement
        eu_checklist = self.engine.get_compliance_checklist("EU", "Data Processing Agreement")
        self.assertIn("GDPR_EU", eu_checklist, "EU checklist should contain GDPR_EU.")
        
        gdpr_checklist_data = eu_checklist["GDPR_EU"]
        self.assertIn("metadata", gdpr_checklist_data, "Checklist should contain metadata.")
        self.assertIn("key_provisions", gdpr_checklist_data, "Checklist should contain key_provisions.")
        
        # Verify the provisions are detailed dictionaries, not simple strings
        key_provisions = gdpr_checklist_data["key_provisions"]
        self.assertIsInstance(key_provisions["Lawful_Basis_for_Processing"], dict, 
                              "Provision should be detailed dictionary for AI processing.")
        
        # Test Malaysian employment contract
        my_checklist = self.engine.get_compliance_checklist("MY", "Employment Contract")
        self.assertIn("PDPA_MY", my_checklist, "MY checklist should contain PDPA_MY.")
        self.assertIn("EMPLOYMENT_ACT_MY", my_checklist, "MY checklist should contain EMPLOYMENT_ACT_MY.")
        
        print("  -> PASSED: Compliance checklists have correct structure for AI processing.")

    def test_08_all_law_files_have_required_fields(self):
        """
        Verifies that all law files have the required fields for proper functioning.
        """
        print("\nRunning test_08_all_law_files_have_required_fields...")
        
        law_files = ["GDPR_EU", "PDPA_MY", "CCPA_US", "EMPLOYMENT_ACT_MY", "PDPA_SG"]
        
        for law_id in law_files:
            law_data = self.engine.get_law_details(law_id)
            self.assertIsNotNone(law_data, f"{law_id} should be loaded.")
            
            # Check required top-level fields
            self.assertIn("law_id", law_data, f"{law_id} should have law_id field.")
            self.assertIn("metadata", law_data, f"{law_id} should have metadata section.")
            
            # Check metadata fields
            metadata = law_data["metadata"]
            self.assertIn("name", metadata, f"{law_id} metadata should have name.")
            self.assertIn("jurisdiction", metadata, f"{law_id} metadata should have jurisdiction.")
            self.assertIn("type", metadata, f"{law_id} metadata should have type.")
            
            # Verify name is not None or empty
            law_name = metadata["name"]
            self.assertIsNotNone(law_name, f"{law_id} name should not be None.")
            self.assertIsInstance(law_name, str, f"{law_id} name should be a string.")
            self.assertTrue(len(law_name) > 0, f"{law_id} name should not be empty.")
            
            print(f"  -> Verified required fields for '{law_id}': '{law_name}'")
        
        print("  -> PASSED: All law files have required fields.")

    def test_09_ai_prompt_guidance_availability(self):
        """
        Tests that key provisions contain AI prompt guidance for contract generation.
        """
        print("\nRunning test_09_ai_prompt_guidance_availability...")
        
        # Check GDPR_EU provisions
        gdpr_law = self.engine.get_law_details("GDPR_EU")
        key_provisions = gdpr_law["key_provisions"]
        
        for provision_name, provision_data in key_provisions.items():
            if isinstance(provision_data, dict):
                self.assertIn("ai_prompt_guidance", provision_data, 
                              f"GDPR provision {provision_name} should have AI prompt guidance.")
                guidance = provision_data["ai_prompt_guidance"]
                self.assertIsInstance(guidance, str, "AI prompt guidance should be a string.")
                self.assertTrue(len(guidance) > 50, "AI prompt guidance should be substantial.")
        
        # Check PDPA_MY provisions
        pdpa_law = self.engine.get_law_details("PDPA_MY")
        key_provisions = pdpa_law["key_provisions"]
        
        consent_provision = key_provisions.get("General_And_Consent_Principle")
        if consent_provision:
            self.assertIn("ai_prompt_guidance", consent_provision, 
                          "PDPA consent provision should have AI prompt guidance.")
        
        print("  -> PASSED: Key provisions contain AI prompt guidance.")

    def test_10_contract_type_filtering(self):
        """
        Tests that compliance checklists correctly filter by contract type.
        """
        print("\nRunning test_10_contract_type_filtering...")
        
        # Test that employment-specific laws appear for employment contracts
        my_employment_checklist = self.engine.get_compliance_checklist("MY", "Employment Contract")
        self.assertIn("EMPLOYMENT_ACT_MY", my_employment_checklist, 
                      "Employment contracts should include Employment Act.")
        
        # Test that data protection laws appear for data processing agreements
        eu_data_checklist = self.engine.get_compliance_checklist("EU", "Data Processing Agreement")
        self.assertIn("GDPR_EU", eu_data_checklist, 
                      "Data processing agreements should include GDPR.")
        
        print("  -> PASSED: Contract type filtering works correctly.")


if __name__ == '__main__':
    unittest.main(verbosity=2)