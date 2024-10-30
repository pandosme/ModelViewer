let socket;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO connection
    socket = io();
    console.log('Socket.IO initialized');

    const videoSource = document.getElementById('sourceSelect');
    const startButton = document.getElementById('startStream');
    const stopButton = document.getElementById('stopStream');
    const videoFrame = document.getElementById('video');
    let currentStream = null;

    // Function to load sources into dropdown
    function loadVideoSources() {
        console.log('Loading video sources...');
        fetch('/api/sources')
            .then(response => response.json())
            .then(sources => {
                console.log('Received sources:', sources);
                videoSource.innerHTML = '<option value="">Select a source</option>';
                sources.forEach(source => {
                    if (source.type === 'camera') { // Only add camera sources
                        const option = document.createElement('option');
                        option.value = source._id;
                        option.textContent = source.name;
                        videoSource.appendChild(option);
                    }
                });
            })
            .catch(error => {
                console.error('Error loading video sources:', error);
            });
    }

    // Load sources when page loads
    loadVideoSources();

    startButton.addEventListener('click', function() {
        const sourceId = videoSource.value;
        if (!sourceId) {
            console.error('No source selected');
            return;
        }
        console.log('Starting stream for source:', sourceId);
        socket.emit('startStream', sourceId);  // Send just the ID
        currentStream = sourceId;
        startButton.style.display = 'none';
        stopButton.style.display = 'block';
    });

    stopButton.addEventListener('click', function() {
        if (currentStream) {
            console.log('Stopping stream for source:', currentStream);
            socket.emit('stopStream', currentStream);  // Send just the ID
            currentStream = null;
            startButton.style.display = 'block';
            stopButton.style.display = 'none';
            videoFrame.src = '';
        }
    });

    socket.on('frame', function(frameData) {
        if (currentStream && videoFrame) {
            videoFrame.src = 'data:image/jpeg;base64,' + frameData;
        }
    });

    // Socket event handlers for connection status
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        if (currentStream) {
            currentStream = null;
            startButton.style.display = 'block';
            stopButton.style.display = 'none';
            videoFrame.src = '';
        }
    });
});
