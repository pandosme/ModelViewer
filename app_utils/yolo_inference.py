import torch
import cv2
import numpy as np
from app_utils.config import config as app_config

class YOLOInference:
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                  path=model_path, 
                                  device=self.device)
        self.model.conf = config['yolo']['confidence_threshold']
        self.model.iou = config['yolo']['iou_threshold']
        
    def process_frame(self, frame):
        # Run inference
        results = self.model(frame)
        
        # Get detections
        detections = results.xyxy[0].cpu().numpy()
        
        # Draw detections
        annotated_frame = frame.copy()
        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            
            # Draw red box with constant line thickness
            line_thickness = 3
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), line_thickness)
            
            # Prepare label text
            label = f"{results.names[int(cls)]} {conf:.2f}"
            
            # Calculate text size and background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            font_thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # Draw red background for text
            cv2.rectangle(annotated_frame, 
                         (x1, y1 - text_height - 10), 
                         (x1 + text_width + 10, y1),
                         (0, 0, 255), 
                         -1)  # Filled rectangle
            
            # Draw white text
            cv2.putText(annotated_frame, 
                       label, 
                       (x1 + 5, y1 - 5),
                       font,
                       font_scale,
                       (255, 255, 255),
                       font_thickness)
        
        return annotated_frame
