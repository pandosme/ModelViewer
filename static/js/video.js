let socket;

document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const videoSource = document.getElementById('sourceSelect');
    const frameRate = document.getElementById('frameRate');
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
				console.log('Received sources:', sources);  // Debug log
				const videoSource = document.getElementById('sourceSelect');
				if (!videoSource) {
					console.error('sourceSelect element not found');
					return;
				}
				videoSource.innerHTML = '<option value="">Select a source</option>';
				sources.forEach(source => {
					if (source.type === 'camera') {
						const option = document.createElement('option');
						option.value = source._id;
						option.textContent = source.name;
						videoSource.appendChild(option);
						console.log('Added source:', source.name);  // Debug log
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
        const fps = parseInt(frameRate.value);
        if (!sourceId) {
            console.error('No source selected');
            return;
        }
        console.log('Starting stream:', { sourceId, fps });
        socket.emit('startStream', { sourceId, fps });
        currentStream = sourceId;
        startButton.style.display = 'none';
        stopButton.style.display = 'block';
        setControlsEnabled(false);
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
