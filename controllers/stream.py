import cv2
import base64
import logging
import threading
import time
import torch
import numpy as np
from collections import deque
from threading import Lock
from app_models.source import Source
from app_utils.config import config

class StreamController:
    def __init__(self, socketio, model, labels, device):
        self.socketio = socketio
        self.active_streams = {}
        self.captures = {}
        self.latest_frames = {}
        self.frame_locks = {}
        self.model = model
        self.labels = labels
        self.device = device
        logging.info(f"StreamController initialized with {len(labels)} labels")

    def process_frame(self, source_id):
        if source_id not in self.active_streams or not self.active_streams[source_id]['processing']:
            return False

        now = time.time()
        stream = self.active_streams[source_id]

        # Check if it's time for next frame
        if now - stream['last_frame'] >= stream['frame_interval']:
            # Get latest frame with lock
            with self.frame_locks[source_id]:
                if source_id in self.latest_frames:
                    frame = self.latest_frames[source_id].copy()
                    
                    # Apply model inference if model is loaded
                    if self.model is not None:
                        try:
                            # Prepare image for inference
                            img = frame.copy()
                            
                            # Run inference
                            results = self.model(img)
                            
                            # Process detections
                            for det in results.xyxy[0]:  # detections per image
                                if len(det) >= 6:  # check if detection has all required values
                                    x1, y1, x2, y2, conf, cls_id = det[:6]
                                    
                                    # Convert tensor values to integers
                                    x1, y1, x2, y2 = map(int, [x1.item(), y1.item(), x2.item(), y2.item()])
                                    conf = conf.item()
                                    cls_id = int(cls_id.item())
                                    
                                    # Get label name
                                    if cls_id < len(self.labels):
                                        label = f"{self.labels[cls_id]} {conf:.2f}"
                                        
                                        # Draw bounding box
                                        cv2.rectangle(frame, 
                                                    (x1, y1), 
                                                    (x2, y2), 
                                                    (0, 0, 255),  # BGR Red
                                                    2)  # thickness
                                        
                                        # Calculate text size
                                        font = cv2.FONT_HERSHEY_SIMPLEX
                                        font_scale = 0.5
                                        thickness = 2
                                        (text_width, text_height), baseline = cv2.getTextSize(
                                            label, font, font_scale, thickness)
                                        
                                        # Draw label background
                                        cv2.rectangle(frame, 
                                                    (x1, y1 - text_height - 10), 
                                                    (x1 + text_width + 10, y1),
                                                    (0, 0, 255),  # BGR Red
                                                    -1)  # filled
                                        
                                        # Draw label text
                                        cv2.putText(frame, 
                                                  label,
                                                  (x1 + 5, y1 - 5),
                                                  font,
                                                  font_scale,
                                                  (255, 255, 255),  # BGR White
                                                  thickness)
                                        
                                        logging.debug(f"Detection: {label} at ({x1},{y1})-({x2},{y2})")
                            
                        except Exception as e:
                            logging.error(f"Error during inference: {str(e)}")
                            logging.exception("Full traceback:")
                    
                    # Convert frame to JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = base64.b64encode(buffer).decode('utf-8')
                    
                    # Update last frame time
                    stream['last_frame'] = now
                    
                    return frame_data

        return None
        
        
    def start_stream(self, source_id):
        try:
            logging.info(f"Starting stream for source {source_id}")
            # Initialize lock if not exists
            if source_id not in self.frame_locks:
                self.frame_locks[source_id] = Lock()

            # Check if we already have a capture for this source
            if source_id not in self.captures:
                source = Source.get_by_id(source_id)
                if not source:
                    raise ValueError(f"Source not found: {source_id}")

                if source['type'] != 'camera':
                    raise ValueError("Only camera sources are supported")

                rtsp_url = f"rtsp://{source['connectionDetails']['user']}:{source['connectionDetails']['password']}@{source['connectionDetails']['address']}/axis-media/media.amp"
                
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not cap.isOpened():
                    raise ValueError("Failed to open RTSP stream")
                
                self.captures[source_id] = {
                    'capture': cap,
                    'frame_rate': source['frameRate']
                }

                # Start background frame grabber if not already running
                if not self._is_grabber_running(source_id):
                    self._start_frame_grabber(source_id)

            # Start frame processing
            self.active_streams[source_id] = {
                'last_frame': 0,
                'frame_interval': 1.0 / self.captures[source_id]['frame_rate'],
                'processing': True
            }

            return True

        except Exception as e:
            logging.error(f"Error starting stream: {str(e)}")
            return False

    def _is_grabber_running(self, source_id):
        return hasattr(self, f'grabber_thread_{source_id}') and getattr(self, f'grabber_thread_{source_id}').is_alive()

    def _start_frame_grabber(self, source_id):
        thread = threading.Thread(
            target=self._grab_frames,
            args=(source_id,),
            daemon=True,
            name=f'grabber_{source_id}'
        )
        setattr(self, f'grabber_thread_{source_id}', thread)
        thread.start()
        logging.info(f"Started frame grabber for source {source_id}")

    def _grab_frames(self, source_id):
        """Continuously grab frames in background"""
        cap = self.captures[source_id]['capture']
        
        while True:
            # Clear buffer
            for _ in range(5):
                cap.grab()
            
            # Read the latest frame
            ret, frame = cap.read()
            if ret:
                # Get original dimensions
                height, width = frame.shape[:2]
                
                # Calculate new dimensions maintaining aspect ratio
                target_width = config['rtsp']['frame']['width']
                target_height = int((target_width * height) / width)
                
                # Resize frame
                frame = cv2.resize(frame, 
                                (target_width, target_height),
                                interpolation=cv2.INTER_AREA)
                
                # Update latest frame with lock
                with self.frame_locks[source_id]:
                    self.latest_frames[source_id] = frame
            
            time.sleep(0.001)  # Prevent CPU overload

    def stop_stream(self, source_id):
        logging.info(f"Stopping stream for source {source_id}")        
        if source_id in self.active_streams:
            # Stop processing but keep the grabber running
            self.active_streams[source_id]['processing'] = False
            return True
        return False

    def cleanup_source(self, source_id):
        """Call this when changing sources"""
        self.stop_stream(source_id)
        if source_id in self.captures:
            self.captures[source_id]['capture'].release()
            del self.captures[source_id]
            if source_id in self.latest_frames:
                del self.latest_frames[source_id]
            if source_id in self.frame_locks:
                del self.frame_locks[source_id]
