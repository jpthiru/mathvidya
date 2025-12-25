/**
 * Mathvidya - Main Utilities
 * Global helper functions and utilities
 */

// ==================== Toast Notifications ====================
class Toast {
  static show(message, type = 'info', duration = 3000) {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Add icon
    const icon = document.createElement('i');
    icon.className = this.getIcon(type);
    toast.prepend(icon);

    // Add to DOM
    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  static getIcon(type) {
    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-exclamation-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle',
    };
    return icons[type] || icons.info;
  }

  static success(message) {
    this.show(message, 'success');
  }

  static error(message) {
    this.show(message, 'error');
  }

  static warning(message) {
    this.show(message, 'warning');
  }

  static info(message) {
    this.show(message, 'info');
  }
}

// Toast styles (will be added to CSS)
const toastStyles = `
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  min-width: 300px;
  padding: 1rem 1.5rem;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
  z-index: var(--z-tooltip);
  transform: translateX(400px);
  transition: transform var(--transition-base);
}

.toast.show {
  transform: translateX(0);
}

.toast i {
  font-size: 1.25rem;
}

.toast-success {
  border-left: 4px solid var(--color-accent);
  color: var(--color-accent);
}

.toast-error {
  border-left: 4px solid var(--color-error);
  color: var(--color-error);
}

.toast-warning {
  border-left: 4px solid var(--color-warning);
  color: var(--color-warning);
}

.toast-info {
  border-left: 4px solid var(--color-info);
  color: var(--color-info);
}
`;

// Inject toast styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// ==================== Modal ====================
class Modal {
  static show(content, options = {}) {
    const {
      title = '',
      size = 'md', // sm, md, lg
      showClose = true,
      onConfirm = null,
      onCancel = null,
      confirmText = 'Confirm',
      cancelText = 'Cancel',
    } = options;

    // Create modal HTML
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal modal-${size}">
        <div class="modal-header">
          <h3>${title}</h3>
          ${showClose ? '<button class="modal-close" aria-label="Close">&times;</button>' : ''}
        </div>
        <div class="modal-body">
          ${content}
        </div>
        ${onConfirm || onCancel ? `
          <div class="modal-footer">
            ${onCancel ? `<button class="btn btn-secondary modal-cancel">${cancelText}</button>` : ''}
            ${onConfirm ? `<button class="btn btn-primary modal-confirm">${confirmText}</button>` : ''}
          </div>
        ` : ''}
      </div>
    `;

    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('show'), 10);

    // Event listeners
    if (showClose) {
      modal.querySelector('.modal-close').addEventListener('click', () => this.close(modal));
    }

    if (onCancel) {
      modal.querySelector('.modal-cancel').addEventListener('click', () => {
        onCancel();
        this.close(modal);
      });
    }

    if (onConfirm) {
      modal.querySelector('.modal-confirm').addEventListener('click', () => {
        onConfirm();
        this.close(modal);
      });
    }

    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) this.close(modal);
    });

    return modal;
  }

  static close(modal) {
    modal.classList.remove('show');
    setTimeout(() => modal.remove(), 300);
  }

  static confirm(message, onConfirm) {
    return this.show(message, {
      title: 'Confirm Action',
      onConfirm,
      onCancel: () => {},
      confirmText: 'Yes',
      cancelText: 'No',
    });
  }
}

// Modal styles
const modalStyles = `
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.modal-overlay.show {
  opacity: 1;
}

.modal {
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-height: 90vh;
  overflow-y: auto;
  transform: scale(0.9);
  transition: transform var(--transition-base);
}

.modal-overlay.show .modal {
  transform: scale(1);
}

.modal-sm { max-width: 400px; }
.modal-md { max-width: 600px; }
.modal-lg { max-width: 800px; }

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-gray-200);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-gray-500);
  transition: color var(--transition-fast);
}

.modal-close:hover {
  color: var(--color-gray-800);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--color-gray-200);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
`;

const modalStyleSheet = document.createElement('style');
modalStyleSheet.textContent = modalStyles;
document.head.appendChild(modalStyleSheet);

// ==================== Form Validation ====================
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function validatePassword(password) {
  return password.length >= 8;
}

function validateRequired(value) {
  return value && value.trim().length > 0;
}

// ==================== Formatting Utilities ====================
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatScore(score, total) {
  return `${score}/${total} (${((score / total) * 100).toFixed(1)}%)`;
}

// ==================== Loading States ====================
function showLoading(button) {
  button.disabled = true;
  button.dataset.originalText = button.innerHTML;
  button.innerHTML = '<span class="spinner"></span> Loading...';
}

function hideLoading(button) {
  button.disabled = false;
  button.innerHTML = button.dataset.originalText || button.innerHTML;
}

// ==================== Scroll Animations ====================
function observeElements(selector, className = 'animate-slideUp') {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add(className);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll(selector).forEach((el) => observer.observe(el));
}

// ==================== Debounce ====================
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ==================== Local Storage Helpers ====================
function getUser() {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

function getToken() {
  return localStorage.getItem('auth_token');
}

function isAuthenticated() {
  return !!getToken();
}

function getUserRole() {
  const user = getUser();
  return user ? user.role : null;
}

// ==================== Export to Global ====================
window.Toast = Toast;
window.Modal = Modal;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
window.validateRequired = validateRequired;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.formatScore = formatScore;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.observeElements = observeElements;
window.debounce = debounce;
window.getUser = getUser;
window.getToken = getToken;
window.isAuthenticated = isAuthenticated;
window.getUserRole = getUserRole;
