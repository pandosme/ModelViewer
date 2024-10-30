document.addEventListener('DOMContentLoaded', function() {
    const addSourceForm = document.getElementById('addSourceForm');
    const sourcesList = document.getElementById('sourcesList');
    const sourceType = document.getElementById('sourceType');
    const cameraFields = document.getElementById('cameraFields');

    // Initialize camera fields visibility
    initializeCameraFields();
    
    // Load initial sources
    loadSources();

    // Source type change handler
    if (sourceType) {
        sourceType.addEventListener('change', function() {
            initializeCameraFields();
        });
    }

    function initializeCameraFields() {
        if (sourceType && cameraFields) {
            cameraFields.style.display = sourceType.value === 'camera' ? 'block' : 'none';
            console.log('Camera fields visibility:', sourceType.value === 'camera');
        }
    }

    function loadSources() {
        console.log('Loading sources...');
        fetch('/api/sources')
            .then(response => response.json())
            .then(sources => {
                console.log('Loaded sources:', sources);
                displaySources(sources);
            })
            .catch(error => {
                console.error('Error loading sources:', error);
            });
    }

    function displaySources(sources) {
        if (!sourcesList) return;
        
        sourcesList.innerHTML = '';
        sources.forEach(source => {
            const sourceElement = document.createElement('div');
            sourceElement.className = 'source-item';
            
            let connectionDetails = '';
            if (source.type === 'camera') {
                connectionDetails = `
                    <p><strong>Address:</strong> ${source.connectionDetails.address}</p>
                    <p><strong>User:</strong> ${source.connectionDetails.user}</p>
                `;
            }
            
            sourceElement.innerHTML = `
                <div class="source-info">
                    <h3>${source.name}</h3>
                    <p><strong>Type:</strong> ${source.type}</p>
                    ${connectionDetails}
                    <p><strong>Frame Rate:</strong> ${source.frameRate}</p>
                </div>
            `;
            
            sourcesList.appendChild(sourceElement);
        });
    }
});
