// Menu toggle
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.querySelector('.sidebar');

// Toggle sidebar function
menuToggle.addEventListener('click', () => {
  sidebar.classList.toggle('open');

  // Update menu icon
  const menuIcon = menuToggle.querySelector('i');
  if (sidebar.classList.contains('open')) {
    menuIcon.classList.remove('fa-bars');
    menuIcon.classList.add('fa-times');
  } else {
    menuIcon.classList.remove('fa-times');
    menuIcon.classList.add('fa-bars');
  }
});

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
  if (!sidebar.contains(e.target) &&
      !menuToggle.contains(e.target) &&
      sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
    const menuIcon = menuToggle.querySelector('i');
    menuIcon.classList.remove('fa-times');
    menuIcon.classList.add('fa-bars');
  }
});

// Handle window resize
window.addEventListener('resize', () => {
  if (window.innerWidth > 900) {
    // For screens larger than 900px, ensure sidebar is in its normal state
    sidebar.classList.remove('open');
    const menuIcon = menuToggle.querySelector('i');
    menuIcon.classList.remove('fa-times');
    menuIcon.classList.add('fa-bars');
  }
});