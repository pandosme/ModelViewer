from flask import Flask
import torch
import logging
import os
import sys  # Add sys import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)

# Print debug info
print(f"\nCurrent working directory: {os.getcwd()}")
print("\nPython path:")
for p in sys.path:
    print(f"  {p}")

def load_model(model_path):
    
    try:
        logging.info(f"Loading model from {model_path}")
        # Load YOLOv5 model using torch.hub
        model = torch.hub.load('ultralytics/yolov5', 
                             'custom', 
                             path=model_path, 
                             force_reload=True)
        
        # Move model to GPU if available
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        
        # Set model to evaluation mode
        model.eval()
        
        logging.info("Model loaded successfully")
        return model
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        logging.exception("Full traceback:")
        return None

@app.route('/')
def test_model():
    try:
        # Print torch version info
        logging.info(f"PyTorch version: {torch.__version__}")
        logging.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logging.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
        
        # Load model
        model_path = '/home/fred/dataset/who/best.pt'
        model = load_model(model_path)
        
        if model is None:
            return "Failed to load model"
        
        # Get model info
        info = {
            "Model loaded": True,
            "Model type": str(type(model)),
            "Device": next(model.parameters()).device,
            "Number of classes": len(model.names),
            "Class names": model.names
        }
        
        return "<br>".join([f"{k}: {v}" for k, v in info.items()])
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        logging.exception("Full traceback:")
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=True)
