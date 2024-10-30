// In static/js/models.js
document.addEventListener('DOMContentLoaded', function() {
    const modelInfo = document.getElementById('modelInfo');
    
    // Get model info
    fetch('/api/model')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                modelInfo.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                modelInfo.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Loaded Model</h5>
                            <p><strong>Device:</strong> ${data.device}</p>
                            <p><strong>Number of Classes:</strong> ${data.num_classes}</p>
                            <p><strong>Classes:</strong> ${Object.values(data.class_names).join(', ')}</p>
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modelInfo.innerHTML = `<div class="alert alert-danger">Error loading model info</div>`;
        });
});
