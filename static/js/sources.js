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

    // Add source form handler
    if (addSourceForm) {
        addSourceForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = {
                name: document.getElementById('sourceName').value,
                type: sourceType.value,
                frameRate: parseInt(document.getElementById('frameRate').value)
            };

            if (sourceType.value === 'camera') {
                formData.connectionDetails = {
                    address: document.getElementById('cameraAddress').value,
                    user: document.getElementById('cameraUser').value,
                    password: document.getElementById('cameraPassword').value
                };
            }

            fetch('/api/sources', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(result => {
                console.log('Source added:', result);
                loadSources();  // Reload sources list
                addSourceForm.reset();
            })
            .catch(error => {
                console.error('Error adding source:', error);
            });
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
                <div class="source-actions">
                    <button onclick="editSource('${source._id}')" class="btn btn-primary btn-sm">Edit</button>
                    <button onclick="deleteSource('${source._id}')" class="btn btn-danger btn-sm">Delete</button>
                </div>
            `;
            
            sourcesList.appendChild(sourceElement);
        });
    }
});

// Global functions for edit and delete
function editSource(sourceId) {
    console.log('Editing source:', sourceId);
    fetch(`/api/sources/${sourceId}`)
        .then(response => response.json())
        .then(source => {
            // Populate edit form
            document.getElementById('editSourceId').value = source._id;
            document.getElementById('editSourceName').value = source.name;
            document.getElementById('editFrameRate').value = source.frameRate;
            
            if (source.type === 'camera') {
                document.getElementById('editCameraAddress').value = source.connectionDetails.address;
                document.getElementById('editCameraUser').value = source.connectionDetails.user;
                document.getElementById('editCameraPassword').value = source.connectionDetails.password;
            }
            
            // Show edit modal
            const editModal = new bootstrap.Modal(document.getElementById('editSourceModal'));
            editModal.show();
        })
        .catch(error => {
            console.error('Error loading source:', error);
        });
}

function deleteSource(sourceId) {
    if (confirm('Are you sure you want to delete this source?')) {
        fetch(`/api/sources/${sourceId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            console.log('Source deleted:', result);
            // Reload sources list
            document.querySelector('#sourcesList').dispatchEvent(new Event('loadSources'));
        })
        .catch(error => {
            console.error('Error deleting source:', error);
        });
    }
}

function updateSource() {
    const sourceId = document.getElementById('editSourceId').value;
    const formData = {
        name: document.getElementById('editSourceName').value,
        frameRate: parseInt(document.getElementById('editFrameRate').value),
        connectionDetails: {
            address: document.getElementById('editCameraAddress').value,
            user: document.getElementById('editCameraUser').value,
            password: document.getElementById('editCameraPassword').value
        }
    };

    fetch(`/api/sources/${sourceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(result => {
        console.log('Source updated:', result);
        // Close modal
        const editModal = bootstrap.Modal.getInstance(document.getElementById('editSourceModal'));
        editModal.hide();
        // Reload sources list
        document.querySelector('#sourcesList').dispatchEvent(new Event('loadSources'));
    })
    .catch(error => {
        console.error('Error updating source:', error);
    });
}
