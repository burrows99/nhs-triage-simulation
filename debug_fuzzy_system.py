#!/usr/bin/env python3
"""
Debug script to test Manchester Triage System fuzzy configuration
"""

import sys
sys.path.append('/Users/raunakburrows/dissertation')

from src.triage.manchester_triage_system.config.fuzzy_config import FuzzySystemConfigManager
from src.triage.manchester_triage_system.rules.fuzzy_rules_manager import FuzzyRulesManager
from skfuzzy import control as ctrl

def test_fuzzy_system_setup():
    """Test the fuzzy system configuration"""
    print("=== Testing Manchester Triage System Fuzzy Configuration ===")
    
    try:
        # Initialize managers
        fuzzy_manager = FuzzySystemConfigManager()
        rules_manager = FuzzyRulesManager()
        
        print("\n1. Creating input variables...")
        input_vars = fuzzy_manager.create_input_variables()
        print(f"   Created {len(input_vars)} input variables:")
        for i, var in enumerate(input_vars):
            print(f"   - {var.label}: {list(var.terms.keys())}")
            print(f"     Universe: {var.universe}")
            print(f"     Range: [{var.universe.min()}, {var.universe.max()}]")
        
        print("\n2. Creating output variable...")
        output_var = fuzzy_manager.create_output_variable()
        print(f"   Output variable: {output_var.label}")
        print(f"   Output terms: {list(output_var.terms.keys())}")
        print(f"   Output universe: {output_var.universe}")
        
        print("\n3. Creating fuzzy rules...")
        rules = rules_manager.create_rules(input_vars, output_var)
        print(f"   Created {len(rules)} rules")
        
        # Debug: Check individual rules
        print("\n3a. Examining rules...")
        for i, rule in enumerate(rules[:3]):  # Show first 3 rules
            print(f"   Rule {i+1}: {rule}")
            print(f"   Antecedent: {rule.antecedent}")
            print(f"   Consequent: {rule.consequent}")
        
        print("\n4. Creating control system...")
        try:
            control_system = ctrl.ControlSystem(rules)
            print("   Control system created successfully")
        except Exception as e:
            print(f"   ERROR creating control system: {e}")
            raise
        
        try:
            simulation = ctrl.ControlSystemSimulation(control_system)
            print("   Simulation created successfully")
        except Exception as e:
            print(f"   ERROR creating simulation: {e}")
            raise
        
        print("\n5. Testing simulation...")
        # Test the original failing case
        input_names = ['symptom1', 'symptom2', 'symptom3', 'symptom4', 'symptom5']
        test_values = [2.0, 5.0, 5.0, 2.0, 5.0]  # Original failing case
        
        print("   Testing with original failing case:")
        for i, value in enumerate(test_values):
            simulation.input[input_names[i]] = value
            print(f"   Set {input_names[i]} = {value}")
        
        # Check membership values for debugging
        print("\n5a. Checking membership values:")
        for i, var in enumerate(input_vars[:2]):  # Check first 2 variables
            value = test_values[i]
            print(f"   {var.label} = {value}:")
            for term_name in var.terms.keys():
                membership = var[term_name].membership_value
                print(f"     {term_name}: {membership}")
        
        print("\n6. Computing inference...")
        try:
            simulation.compute()
            print("   Computation completed")
        except Exception as e:
            print(f"   ERROR during computation: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n7. Results:")
        print(f"   Available outputs: {list(simulation.output.keys())}")
        print(f"   Simulation state: {hasattr(simulation, 'output')}")
        
        # Check if simulation has the output variable
        if hasattr(simulation, 'output'):
            print(f"   Output object type: {type(simulation.output)}")
            if hasattr(simulation.output, 'keys'):
                output_keys = list(simulation.output.keys())
                print(f"   Output keys: {output_keys}")
                for key in output_keys:
                    try:
                        value = simulation.output[key]
                        print(f"   {key}: {value}")
                    except Exception as e:
                        print(f"   {key}: ERROR - {e}")
            else:
                print("   Output object has no keys() method")
        else:
            print("   No output attribute found")
        
        # Try alternative access methods
        print("\n8. Alternative access attempts:")
        try:
            if 'triage_category' in simulation.output:
                result = simulation.output['triage_category']
                print(f"   Direct access to triage_category: {result}")
            else:
                print("   triage_category not found in outputs")
        except Exception as e:
            print(f"   Error accessing triage_category: {e}")
        
        # Check control system outputs
        print("\n9. Control system info:")
        print(f"   Control system outputs: {[str(output) for output in control_system.consequents]}")
        print(f"   Control system inputs: {[str(input_var) for input_var in control_system.antecedents]}")
        
        print("\n✅ SUCCESS: Fuzzy system working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fuzzy_system_setup()
    sys.exit(0 if success else 1)