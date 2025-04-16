// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Toggle sidebar on mobile devices
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.toggle('show');
            }
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const sidebar = document.querySelector('.sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        
        if (sidebar && sidebar.classList.contains('show') && 
            !sidebar.contains(event.target) && 
            !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    });
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Handle form validation styling
    const forms = document.querySelectorAll('.needs-validation');
    
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Utility function to set invalid state on a form element
    window.setInvalid = function(element, message) {
        if (!element) return;
        
        element.classList.add('is-invalid');
        
        // Find or create feedback element
        let feedback = element.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.classList.add('invalid-feedback');
            element.parentNode.insertBefore(feedback, element.nextSibling);
        }
        
        feedback.innerText = message;
    };
    
    // Utility function to clear validation state
    window.clearValidation = function(element) {
        if (!element) return;
        
        element.classList.remove('is-invalid');
        element.classList.remove('is-valid');
        
        // Remove feedback elements
        const feedback = element.nextElementSibling;
        if (feedback && (feedback.classList.contains('invalid-feedback') || feedback.classList.contains('valid-feedback'))) {
            feedback.remove();
        }
    };
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }
});