import cv2
import base64
import logging
import threading
import time
from threading import Lock
from app_models.source import Source

class StreamController:
    def __init__(self, socketio, model, labels, device):
        self.socketio = socketio
        self.model = model
        self.labels = labels
        self.device = device
        self.active_streams = {}
        self.captures = {}
        self.latest_frames = {}
        self.frame_locks = {}
        logging.info(f"StreamController initialized with model on {device}")

    def start_stream(self, source_id):
        try:
            logging.info(f"Starting stream for source {source_id}")
            
            if source_id not in self.frame_locks:
                logging.info("Creating new frame lock")
                self.frame_locks[source_id] = Lock()

            if source_id not in self.captures:
                logging.info("Setting up new capture")
                source = Source.get_by_id(source_id)
                if not source:
                    logging.error(f"Source not found: {source_id}")
                    return False

                logging.info(f"Source found: {source}")
                if source['type'] != 'camera':
                    logging.error("Only camera sources are supported")
                    return False

                rtsp_url = f"rtsp://{source['connectionDetails']['user']}:{source['connectionDetails']['password']}@{source['connectionDetails']['address']}/axis-media/media.amp"
                logging.info(f"Connecting to RTSP URL: {rtsp_url}")
                
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    logging.error("Failed to open RTSP stream")
                    return False
                
                logging.info("RTSP stream opened successfully")
                self.captures[source_id] = {
                    'capture': cap,
                    'frame_rate': source['frameRate']
                }

            if not self._is_grabber_running(source_id):
                logging.info("Starting frame grabber")
                self._start_frame_grabber(source_id)

            self.active_streams[source_id] = {
                'last_frame': 0,
                'frame_interval': 1.0 / self.captures[source_id]['frame_rate'],
                'processing': True
            }

            logging.info(f"Stream started successfully for source {source_id}")
            return True

        except Exception as e:
            logging.error(f"Error starting stream: {str(e)}")
            logging.exception("Full traceback:")
            return False

    def stop_stream(self, source_id):
        try:
            logging.info(f"Stopping stream for source {source_id}")
            if source_id in self.active_streams:
                self.active_streams[source_id]['processing'] = False
                if source_id in self.captures:
                    self.captures[source_id]['capture'].release()
                    del self.captures[source_id]
                if source_id in self.latest_frames:
                    del self.latest_frames[source_id]
                del self.active_streams[source_id]
                logging.info(f"Stream stopped for source {source_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error stopping stream: {str(e)}")
            logging.exception("Full traceback:")
            return False

    def _is_grabber_running(self, source_id):
        return source_id in self.active_streams and self.active_streams[source_id]['processing']

    def _start_frame_grabber(self, source_id):
        def grab_frames():
            while self._is_grabber_running(source_id):
                try:
                    cap = self.captures[source_id]['capture']
                    ret, frame = cap.read()
                    if ret:
                        with self.frame_locks[source_id]:
                            self.latest_frames[source_id] = frame
                    else:
                        logging.error(f"Failed to read frame from source {source_id}")
                        break
                except Exception as e:
                    logging.error(f"Error in frame grabber: {str(e)}")
                    break
            logging.info(f"Frame grabber stopped for source {source_id}")

        thread = threading.Thread(target=grab_frames)
        thread.daemon = True
        thread.start()
        logging.info(f"Frame grabber started for source {source_id}")

    def process_frame(self, source_id):
        if source_id not in self.active_streams or not self.active_streams[source_id]['processing']:
            return False

        now = time.time()
        stream = self.active_streams[source_id]

        if now - stream['last_frame'] >= stream['frame_interval']:
            with self.frame_locks[source_id]:
                if source_id in self.latest_frames:
                    frame = self.latest_frames[source_id].copy()
                    
                    if self.model is not None:
                        try:
                            results = self.model(frame)
                            
                            for det in results.xyxy[0]:
                                if len(det) >= 6:
                                    x1, y1, x2, y2, conf, cls_id = det[:6]
                                    x1, y1, x2, y2 = map(int, [x1.item(), y1.item(), x2.item(), y2.item()])
                                    conf = conf.item()
                                    cls_id = int(cls_id.item())
                                    
                                    if cls_id < len(self.labels):
                                        label = f"{self.labels[cls_id]} {conf:.2f}"
                                        self._draw_detection(frame, x1, y1, x2, y2, label)
                                        logging.debug(f"Detection: {label} at ({x1},{y1})-({x2},{y2})")
                        
                        except Exception as e:
                            logging.error(f"Error during inference: {str(e)}")
                            logging.exception("Full traceback:")
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = base64.b64encode(buffer).decode('utf-8')
                    stream['last_frame'] = now
                    return frame_data

        return None

    def _draw_detection(self, frame, x1, y1, x2, y2, label):
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Calculate text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Draw label background
        cv2.rectangle(frame, 
                     (x1, y1 - text_height - 10), 
                     (x1 + text_width + 10, y1),
                     (0, 0, 255),
                     -1)
        
        # Draw label text
        cv2.putText(frame, 
                   label,
                   (x1 + 5, y1 - 5),
                   font,
                   font_scale,
                   (255, 255, 255),
                   thickness)
