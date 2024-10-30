from flask import Blueprint, jsonify, current_app
import logging

model_routes = Blueprint('model_routes', __name__)

@model_routes.route('/api/model', methods=['GET'])
def get_model_info():
    """Get information about the loaded model"""
    try:
        stream_controller = current_app.stream_controller
        if stream_controller.model is None:
            return jsonify({'error': 'No model loaded'}), 404

        info = {
            'device': str(stream_controller.device),
            'num_classes': len(stream_controller.model.names),
            'class_names': stream_controller.model.names
        }
        return jsonify(info)
    except Exception as e:
        logging.error(f"Error getting model info: {str(e)}")
        return jsonify({'error': str(e)}), 500
