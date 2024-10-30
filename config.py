import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # MongoDB settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'yolo_validation')
    
    # YOLOv5 settings
    DATASET_BASE_DIR = os.getenv('DATASET_BASE_DIR', '/home/fred/dataset')
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8765))
    
    # RTSP settings
    RTSP_BUFFER_SIZE = 1
    FRAME_WIDTH = 800
    FRAME_HEIGHT = 800

    # Model settings
    CONFIDENCE_THRESHOLD = 0.25
    IOU_THRESHOLD = 0.45
