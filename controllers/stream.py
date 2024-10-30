import cv2
import base64
import logging
import threading
import time
from threading import Lock
from app_models.source import Source

class StreamController:
    def __init__(self, socketio, model, labels, device):
        # Keep existing initialization
        self.socketio = socketio
        self.model = model
        self.labels = labels
        self.device = device
        self.streams = {}  # Store all stream-related data
        self.locks = {}    # Thread synchronization locks
        logging.info(f"StreamController initialized with model on {device}")

    def start_stream(self, source_id, frame_rate=10):  # Add frame_rate parameter
        """Start streaming from a camera source"""
        try:
            logging.info(f"Starting stream for source {source_id} at {frame_rate} FPS")
            
            # Get source configuration
            source = Source.get_by_id(source_id)
            if not source or source['type'] != 'camera':
                logging.error(f"Invalid source: {source_id}")
                return False

            # Setup RTSP connection
            rtsp_url = f"rtsp://{source['connectionDetails']['user']}:{source['connectionDetails']['password']}@{source['connectionDetails']['address']}/axis-media/media.amp"
            logging.info(f"Connecting to RTSP URL: {rtsp_url}")
            
            capture = cv2.VideoCapture(rtsp_url)
            if not capture.isOpened():
                logging.error("Failed to open RTSP stream")
                return False
            
            # Initialize stream data with client-specified frame rate
            self.locks[source_id] = Lock()
            self.streams[source_id] = {
                'capture': capture,
                'frame_rate': frame_rate,  # Use client-specified frame rate
                'latest_frame': None,
                'running': True,
                'last_processed': 0
            }

            # Start capture thread
            self._start_capture_thread(source_id)
            # Start processing thread
            self._start_processing_thread(source_id)

            logging.info(f"Stream started successfully for source {source_id}")
            return True

        except Exception as e:
            logging.error(f"Error starting stream: {str(e)}")
            logging.exception("Full traceback:")
            return False

    def cleanup(self):
        """Stop all active streams and clean up resources"""
        logging.info("Cleaning up all streams")
        try:
            # Get list of active streams first to avoid modification during iteration
            active_streams = list(self.active_streams.keys())
            for source_id in active_streams:
                self.stop_stream(source_id)
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
        
    def stop_stream(self, source_id):
        try:
            logging.info(f"Stopping stream for source {source_id}")
            if source_id in self.active_streams:
                # First set processing to false to stop the threads
                self.active_streams[source_id]['processing'] = False
                
                # Give threads time to stop
                time.sleep(0.5)
                
                # Clean up resources in order
                if source_id in self.captures:
                    try:
                        self.captures[source_id]['capture'].release()
                    except Exception as e:
                        logging.error(f"Error releasing capture: {str(e)}")
                    del self.captures[source_id]
                    
                if source_id in self.latest_frames:
                    del self.latest_frames[source_id]
                    
                if source_id in self.frame_locks:
                    del self.frame_locks[source_id]
                    
                if source_id in self.active_streams:
                    del self.active_streams[source_id]
                    
                logging.info(f"Stream stopped and resources cleaned up for source {source_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error stopping stream: {str(e)}")
            logging.exception("Full traceback:")
            return False
        
    def _start_capture_thread(self, source_id):
        """Thread for continuous frame capture from camera"""
        def capture_frames():
            while self.streams[source_id]['running']:
                try:
                    ret, frame = self.streams[source_id]['capture'].read()
                    if ret:
                        with self.locks[source_id]:
                            self.streams[source_id]['latest_frame'] = frame
                    else:
                        logging.error(f"Failed to read frame from source {source_id}")
                        break
                except Exception as e:
                    logging.error(f"Error capturing frame: {str(e)}")
                    break
            logging.info(f"Capture thread stopped for source {source_id}")

        thread = threading.Thread(target=capture_frames)
        thread.daemon = True
        thread.start()
        logging.info(f"Capture thread started for source {source_id}")

    def _start_processing_thread(self, source_id):
        """Thread for processing frames and sending to client"""
        def process_frames():
            while self.streams[source_id]['running']:
                try:
                    now = time.time()
                    frame_interval = 1.0 / self.streams[source_id]['frame_rate']
                    
                    # Check if it's time to process a new frame
                    if now - self.streams[source_id]['last_processed'] >= frame_interval:
                        with self.locks[source_id]:
                            if self.streams[source_id]['latest_frame'] is not None:
                                frame = self.streams[source_id]['latest_frame'].copy()
                                
                                # Run inference
                                if self.model is not None:
                                    results = self.model(frame)
                                    
                                    # Draw detections
                                    for det in results.xyxy[0]:
                                        if len(det) >= 6:
                                            x1, y1, x2, y2, conf, cls_id = map(float, det[:6])
                                            if cls_id < len(self.labels):
                                                label = f"{self.labels[int(cls_id)]} {conf:.2f}"
                                                self._draw_detection(frame, int(x1), int(y1), int(x2), int(y2), label)
                                
                                # Encode and send frame
                                _, buffer = cv2.imencode('.jpg', frame)
                                frame_data = base64.b64encode(buffer).decode('utf-8')
                                self.socketio.emit('frame', frame_data)
                                self.streams[source_id]['last_processed'] = now
                
                    time.sleep(0.001)  # Small delay to prevent CPU overload
                    
                except Exception as e:
                    logging.error(f"Error processing frame: {str(e)}")
                    break
                    
            logging.info(f"Processing thread stopped for source {source_id}")

        thread = threading.Thread(target=process_frames)
        thread.daemon = True
        thread.start()
        logging.info(f"Processing thread started for source {source_id}")

    def _draw_detection(self, frame, x1, y1, x2, y2, label):
        """Draw bounding box and label on frame"""
        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Draw label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, thickness)
        
        cv2.rectangle(frame, 
                     (x1, y1 - text_height - 10), 
                     (x1 + text_width + 10, y1),
                     (0, 0, 255),
                     -1)
        
        cv2.putText(frame, 
                   label,
                   (x1 + 5, y1 - 5),
                   font,
                   font_scale,
                   (255, 255, 255),
                   thickness)
