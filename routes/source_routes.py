from flask import Blueprint, request, jsonify
from app_models.source import Source
import logging

source_routes = Blueprint('source_routes', __name__)

@source_routes.route('/', methods=['GET'])  # Changed from '/api/sources'
def get_sources():
    try:
        sources = Source.get_all()
        logging.info(f"Retrieved {len(sources)} sources")
        return jsonify(sources)
    except Exception as e:
        logging.error(f"Error getting sources: {str(e)}")
        return jsonify({'error': str(e)}), 500

@source_routes.route('/<source_id>', methods=['PUT'])  # Changed from '/api/sources/<source_id>'
def update_source(source_id):
    try:
        data = request.json
        logging.info(f"Updating source {source_id} with data: {data}")
        
        existing_source = Source.get_by_id(source_id)
        if not existing_source:
            logging.error(f"Source {source_id} not found")
            return jsonify({'error': 'Source not found'}), 404

        Source.update(source_id, data)
        
        logging.info(f"Successfully updated source {source_id}")
        return jsonify({'message': 'Source updated successfully'})
    except Exception as e:
        logging.error(f"Error updating source {source_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@source_routes.route('/test', methods=['GET'])  # Changed from '/api/sources/test'
def test_mongodb():
    try:
        sources = Source.get_all()
        return jsonify({
            'status': 'success',
            'message': 'MongoDB connection successful',
            'sources_count': len(sources),
            'sources': sources
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'MongoDB error: {str(e)}'
        }), 500
