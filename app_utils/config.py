import yaml
import os
from pathlib import Path
import logging

def setup_logging(config):
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format=config['logging']['format'],
        datefmt=config['logging']['date_format']
    )

def load_config():
    try:
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables if they exist
        if os.getenv('MONGODB_URI'):
            config['mongodb']['uri'] = os.getenv('MONGODB_URI')
        if os.getenv('DATASET_BASE_DIR'):
            config['yolo']['dataset_base_dir'] = os.getenv('DATASET_BASE_DIR')
        if os.getenv('FLASK_SECRET_KEY'):
            config['flask']['secret_key'] = os.getenv('FLASK_SECRET_KEY')
        if os.getenv('FLASK_DEBUG'):
            config['flask']['debug'] = os.getenv('FLASK_DEBUG').lower() == 'true'
        
        # Setup logging
        setup_logging(config)
        
        return config
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        raise

# Create a global config object
config = load_config()
