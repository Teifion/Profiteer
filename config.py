import json
import sys
import random
import string

random.seed()

# This generates a list of characters we can use in a salt
# based on string.printable minus a few unwanted occupants
saltable = [c for c in string.printable if c not in ("\x0b", "\x0c", "\n", "\t", "\r", "\\")]

def save():
    """Saves the config to file"""
    
    key_list = list(config.keys())
    key_list.sort()
    
    with open(config_path, "w") as f:
        f.write("{")
        
        # We manually print it out so as to make it easier for a human
        # to edit the dictionary
        first_key = True
        for k in key_list:
            if not first_key:
                f.write(",")
            first_key = False
            
            if type(config[k]) == str:
                f.write('''\n\t{0:31} "{1}"'''.format('"%s":' % k, config[k]))
            elif type(config[k]) == bool:
                f.write('''\n\t{0:31} {1}'''.format('"%s":' % k, str(config[k]).lower()))
            else:
                f.write('''\n\t{0:31} {1}'''.format('"%s":' % k, config[k]))
        
        f.write("\n}")

# Load up the config
config_path = "{}/config.json".format(sys.path[0])
config = {}

def set(key, value):
    """Sets the value for the configuration dictionary"""
    config[key] = value

def check(key):
    """Checks that a value exists"""
    if key in config:
        return True
    return False

def init(key, value=""):
    """If the key is not present in the dictionary this places it there"""
    if key not in config:
        config[key] = value

def get(key, default=None):
    """Grabs an entry from the config"""
    
    if key in config:
        return config[key]
    
    else:
        if default != None:
            config[key] = default
            return default
        
        else:
            raise KeyError("{} is not present in the config dictionary".format(key))

def delete(key):
    if key in config:
        del(config[key])

def install():
    """Sets some default values in the config dictionary"""
    init("cache_path",      "{}/cache/".format(sys.path[0]))
    init("file_path",       "{}/".format(sys.path[0]))
    
    # Media used for the admin GUI
    init("media_path",      "media/")
    
    # Test database stuff
    init("test_db_host",        "localhost")
    init("test_db_name",        "test_datbase")
    init("test_db_password",    "password")
    init("test_db_username",    "username")
    
    # Run clear on terminal window at start of script
    init("clean_screen",    False)
    
    # Used as a salt for information, we generate it at install time
    init("passcode",        "".join(
        [random.choice(saltable) for i in range(32 + random.randint(0,4))]
    ))
    
    init("test_flag",       False)
    init("log_usage",       True)
    
    save()

try:
    with open(config_path) as f:
        config = dict(json.load(f))
except IOError as e:
    install()
except Exception as e:
    raise