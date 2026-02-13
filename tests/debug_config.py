
import sys
import os
sys.path.append(os.getcwd())

try:
    import config
    print(f"Direct import config: {config.__file__}")
    if hasattr(config, 'MONGO_URI'):
        print("Direct import has MONGO_URI")
    else:
        print("Direct import MISSING MONGO_URI")
except ImportError:
    print("Direct import config failed")

try:
    from src import config as src_config
    print(f"From src import config: {src_config.__file__}")
    if hasattr(src_config, 'MONGO_URI'):
        print("Src import has MONGO_URI")
    else:
        print("Src import MISSING MONGO_URI")
except ImportError:
    print("From src import config failed")
