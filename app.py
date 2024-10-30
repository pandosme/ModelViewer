from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import logging
import os
import sys
import torch
import argparse
from app_utils.config import config
from routes.source_routes import source_routes
from controllers.stream import StreamController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_model(model_path):
    try:
        logging.info(f"Loading model from {model_path}")
        model = torch.hub.load('ultralytics/yolov5', 
                             'custom', 
                             path=model_path, 
                             force_reload=True,
                             trust_repo=True)
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)
        model.eval()
        
        logging.info("Model loaded successfully")
        return model, device
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        logging.exception("Full traceback:")
        return None, None

def create_app(dataset_path, skip_model_load=False):
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    app.config['SECRET_KEY'] = config['flask']['secret_key']

    # Register source routes
    app.register_blueprint(source_routes, url_prefix='/api/sources')

    @app.route('/')
    def index():
        """Serve the main page"""
        return render_template('index.html')

    @app.route('/api/model/info')
    def get_model_info():
        """Get information about the loaded model"""
        if not hasattr(app, 'stream_controller') or app.stream_controller is None:
            return jsonify({'error': 'No model loaded'}), 404

        try:
            info = {
                'path': dataset_path,
                'device': str(app.stream_controller.device),
                'labels': app.stream_controller.labels,
                'status': 'loaded'
            }
            return jsonify(info)
        except Exception as e:
            logging.error(f"Error getting model info: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Socket.IO setup
    socketio = SocketIO(
        app,
        cors_allowed_origins=config['flask']['socket']['cors_allowed_origins'],
        async_mode=config['flask']['socket']['async_mode']
    )

    @socketio.on('connect')
    def handle_connect():
        logging.info('Socket.IO: Client connected')

    @socketio.on('startStream')
    def handle_start_stream(source_id):
        logging.info(f'Socket.IO: Starting stream for source: {source_id}')
        if hasattr(app, 'stream_controller') and app.stream_controller is not None:
            success = app.stream_controller.start_stream(source_id)
            logging.info(f'Stream start {"successful" if success else "failed"}')
        else:
            logging.error('No stream controller available')

    @socketio.on('stopStream')
    def handle_stop_stream(source_id):
        logging.info(f'Socket.IO: Stopping stream for source: {source_id}')
        if hasattr(app, 'stream_controller') and app.stream_controller is not None:
            success = app.stream_controller.stop_stream(source_id)
            logging.info(f'Stream stop {"successful" if success else "failed"}')
            
    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info('Socket.IO: Client disconnected')

    if not skip_model_load:
        # Verify dataset directory
        if not os.path.isdir(dataset_path):
            logging.error(f"Dataset directory not found: {dataset_path}")
            return None

        # Check for required files
        model_path = os.path.join(dataset_path, 'best.pt')
        if not os.path.exists(model_path):
            logging.error(f"Model file not found: {model_path}")
            return None

        # Load model
        model, device = load_model(model_path)
        if model is None:
            return None

        # Load labels
        labels_path = os.path.join(dataset_path, 'labels.txt')
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as f:
                labels = [line.strip() for line in f if line.strip()]
                logging.info(f"Loaded {len(labels)} labels from labels.txt")
        else:
            logging.error("Labels file not found")
            return None

        # Initialize StreamController
        app.stream_controller = StreamController(socketio, model, labels, device)
        logging.info("StreamController initialized successfully")

    return app, socketio

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start YOLO validation server')
    parser.add_argument('dataset_path', help='Path to dataset directory containing best.pt and labels')
    args = parser.parse_args()

    # Check if this is a reload
    is_reload = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    result = create_app(args.dataset_path, skip_model_load=is_reload)
    if result is None:
        logging.error("Failed to initialize application")
        exit(1)
    
    app, socketio = result

    try:
        logging.info("Starting Flask application...")
        socketio.run(
            app,
            host=config['flask']['host'],
            port=config['flask']['port'],
            debug=config['flask']['debug'],
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}")
