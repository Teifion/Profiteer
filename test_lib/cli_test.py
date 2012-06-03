import types
import unittest
from profiteer import cli

class CLITester(unittest.TestCase):
    test_targets = []
    
    maxDiff = None
    
    def test_cli_funcs_exist(self):
        self.test_targets.append(cli.main)
        
        # Check we've got the right number of items
        for k, v in cli.func_dict.items():
            f, info, a, k = v
            
            self.assertIn(type(f), (types.FunctionType, types.LambdaType))
            self.assertEqual(type(info), str)
            self.assertIn(type(a), (list, tuple, set))
            self.assertEqual(type(k), dict)
        
        # Check we've got certain elements in there
        self.assertIn("default", cli.func_dict)
