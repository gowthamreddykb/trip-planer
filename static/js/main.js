/**
 * Trip Planner Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 6 seconds
  setTimeout(function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    });
  }, 6000);

  // Fallback for broken images
  document.querySelectorAll('img').forEach(function (img) {
    img.addEventListener('error', function () {
      if (!this.dataset.hasFallback) {
        this.dataset.hasFallback = 'true';
        this.src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80';
      }
    });
  });

  // Client-side Trip Form validation
  const tripForm = document.getElementById('tripForm');
  if (tripForm) {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    tripForm.addEventListener('submit', function (e) {
      if (startDateInput && endDateInput) {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);
        if (end < start) {
          e.preventDefault();
          alert('End date cannot be earlier than start date.');
          endDateInput.focus();
        }
      }
    });
  }
});
