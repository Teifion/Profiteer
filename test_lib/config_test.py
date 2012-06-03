import unittest
from profiteer import config

class ConfigTester(unittest.TestCase):
    test_targets = [
        config.install,
        
        config.check,
        config.delete,
        config.get,
        config.init,
        config.save,
        config.set,
    ]
    
    maxDiff = None
    
    def test_inistall(self):
        config.install()
        
        keys = ("cache_path","file_path","media_path","clean_screen","passcode","test_flag","log_usage")
        
        for k in keys:
            self.assertIn(k, config.config)
    
    def test_config(self):
        config.set("test_flag", False)
        config.save()
        
        # Get a hash of the file
        with open(config.config_path) as f:
            file_hash = hash(f.read())
        
        # Get a value
        r = config.get("test_flag")
        not_r = not r
        
        # Innit should not override the existing value
        config.init("test_flag", not_r)
        self.assertNotEqual(not_r, config.get("test_flag"))
        
        config.set("test_flag", not_r)
        
        # Ensure everything is still as it was
        with open(config.config_path) as f:
            self.assertEqual(file_hash, hash(f.read()))
        
        # Now try to save it
        config.save()
        
        with open(config.config_path) as f:
            self.assertNotEqual(file_hash, hash(f.read()))
        
        # Now try to set a new property
        config.delete("test_flag2")
        self.assertEqual(config.check("test_flag2"), False)
        
        # Lets set it and then delete it, just to be sure
        config.set("test_flag2", False)
        self.assertEqual(config.check("test_flag2"), True)
        
        # Now save it, it should have a diffrent hash
        config.save()
        with open(config.config_path) as f:
            self.assertNotEqual(file_hash, hash(f.read()))
        
        # Delete the check
        config.delete("test_flag2")
        
        # Check it's all back to how it started
        config.set("test_flag", False)
        config.save()
        with open(config.config_path) as f:
            self.assertEqual(file_hash, hash(f.read()))
