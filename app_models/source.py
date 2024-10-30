from bson import ObjectId
from datetime import datetime
import logging
from app_utils.config import config  # Update this import
from pymongo import MongoClient

# MongoDB connection using config
try:
    client = MongoClient(config['mongodb']['uri'])
    # Test the connection
    client.server_info()
    db = client[config['mongodb']['database']]
    sources_collection = db[config['mongodb']['collections']['sources']]
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

class Source:
    TYPES = ['camera', 'directory', 'video']

    def __init__(self, type, name, frame_rate=1, connection_details=None):
        if type not in self.TYPES:
            raise ValueError(f"Type must be one of {self.TYPES}")
        
        self.type = type
        self.name = name
        self.frame_rate = frame_rate
        self.connection_details = connection_details or {}
        
        # Validate connection details for camera type
        if type == 'camera':
            required_fields = ['address', 'user', 'password']
            if not all(field in self.connection_details for field in required_fields):
                raise ValueError("Camera type requires address, user, and password")

    @staticmethod
    def from_dict(data):
        return Source(
            type=data.get('type'),
            name=data.get('name'),
            frame_rate=data.get('frameRate', 1),
            connection_details=data.get('connectionDetails', {})
        )

    def to_dict(self):
        return {
            'type': self.type,
            'name': self.name,
            'frameRate': self.frame_rate,
            'connectionDetails': self.connection_details,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }

    @staticmethod
    def get_all():
        try:
            sources = list(sources_collection.find())
            logging.info(f"Retrieved {len(sources)} sources from MongoDB")
            return [{**s, '_id': str(s['_id'])} for s in sources]
        except Exception as e:
            logging.error(f"Error retrieving sources: {str(e)}")
            raise

    @staticmethod
    def get_by_id(source_id):
        try:
            source = sources_collection.find_one({'_id': ObjectId(source_id)})
            if source:
                source['_id'] = str(source['_id'])
                logging.info(f"Retrieved source {source_id}")
            else:
                logging.warning(f"Source {source_id} not found")
            return source
        except Exception as e:
            logging.error(f"Error retrieving source {source_id}: {str(e)}")
            raise

    def save(self):
        try:
            result = sources_collection.insert_one(self.to_dict())
            source_id = str(result.inserted_id)
            logging.info(f"Saved new source with ID: {source_id}")
            return source_id
        except Exception as e:
            logging.error(f"Error saving source: {str(e)}")
            raise

    @staticmethod
    def update(source_id, data):
        try:
            # Remove _id if it exists in the data
            if '_id' in data:
                del data['_id']
                
            data['updatedAt'] = datetime.utcnow()
            
            result = sources_collection.update_one(
                {'_id': ObjectId(source_id)},
                {'$set': data}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Source with id {source_id} not found")
                
            logging.info(f"Updated source {source_id}, matched: {result.matched_count}, modified: {result.modified_count}")
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating source {source_id}: {str(e)}")
            raise
        
    @staticmethod
    def delete(source_id):
        try:
            result = sources_collection.delete_one({'_id': ObjectId(source_id)})
            logging.info(f"Deleted source {source_id}, deleted count: {result.deleted_count}")
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting source {source_id}: {str(e)}")
            raise
