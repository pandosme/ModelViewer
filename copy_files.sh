#!/bin/bash

# Source and destination directories
SRC_DIR="/home/fred/apps/run_dataset"
DEST_DIR="/home/fred/apps/m"

# Create static directories if they don't exist
mkdir -p "$DEST_DIR/static/css"
mkdir -p "$DEST_DIR/static/js"
mkdir -p "$DEST_DIR/templates"

# Copy static files (CSS and JavaScript)
cp "$SRC_DIR/public/css/styles.css" "$DEST_DIR/static/css/"
cp "$SRC_DIR/public/js/"* "$DEST_DIR/static/js/"

# Copy index.html to templates
cp "$SRC_DIR/public/index.html" "$DEST_DIR/templates/"

# Create requirements.txt with the versions from your conda environment
cat > "$DEST_DIR/requirements.txt" << EOF
Flask==3.0.3
Flask-SocketIO==0.23.1
opencv-python==4.10.0.84
python-dotenv==1.0.0
torch==2.4.0
torchvision==0.19.0
numpy==1.23.5
pymongo==3.12.0
ultralytics==8.2.82
EOF

echo "Files copied successfully!"
echo "Note: The JavaScript files may need modifications to work with Flask endpoints"
