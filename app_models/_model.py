import os
import yaml
import logging
from app_utils.config import config as app_config

class Model:
    BASE_DIR = config['yolo']['dataset_base_dir']

    def __init__(self, name, directory, labels=None, config_file=None, weight_file=None):
        self.name = name
        self.directory = directory
        self.labels = labels or []
        self.config_file = config_file
        self.weight_file = weight_file

    @staticmethod
    def scan_models():
        """Scan the dataset directory for models"""
        models = []
        try:
            directories = os.listdir(Model.BASE_DIR)
            
            for dir_name in directories:
                dir_path = os.path.join(Model.BASE_DIR, dir_name)
                if os.path.isdir(dir_path):
                    # Check for required files
                    files = os.listdir(dir_path)
                    if all(f in files for f in ['best.pt', 'data.yaml', 'labels.txt']):
                        # Read labels
                        labels_path = os.path.join(dir_path, 'labels.txt')
                        with open(labels_path, 'r') as f:
                            labels = [line.strip() for line in f if line.strip()]
                        
                        models.append({
                            'name': dir_name,
                            'directory': dir_name,
                            'labels': labels,
                            'configFile': os.path.join(dir_path, 'data.yaml'),
                            'weightFile': os.path.join(dir_path, 'best.pt')
                        })
                        logging.info(f"Found model in directory: {dir_name}")
            
            return models
        except Exception as e:
            logging.error(f"Error scanning models: {str(e)}")
            raise
