/**
 * Mathvidya API Client
 * Handles all backend communication
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('auth_token');
  }

  // Set auth token
  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  // Clear auth token
  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  // Get headers
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      // Handle non-2xx responses
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      // Parse JSON response
      const data = await response.json();
      return data;

    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // HTTP methods
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // ==================== Authentication ====================

  async register(userData) {
    const data = await this.post('/register', userData);
    if (data.access_token) {
      this.setToken(data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  }

  async login(email, password) {
    // FastAPI OAuth2 expects form data
    const formData = new URLSearchParams();
    formData.append('username', email); // FastAPI OAuth2 uses 'username' field
    formData.append('password', password);

    const response = await fetch(`${this.baseURL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    if (data.access_token) {
      this.setToken(data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  }

  async logout() {
    await this.post('/logout');
    this.clearToken();
  }

  async getMe() {
    return this.get('/me');
  }

  // ==================== Exams ====================

  async getAvailableExams() {
    return this.get('/exams/templates');
  }

  async startExam(templateId, examType = 'unit_wise', units = []) {
    return this.post('/exams/start', {
      template_id: templateId,
      exam_type: examType,
      selected_units: units,
    });
  }

  async getExamInstance(examId) {
    return this.get(`/exams/${examId}`);
  }

  async submitMCQAnswer(examId, questionNumber, selectedOption) {
    return this.post(`/exams/${examId}/mcq`, {
      question_number: questionNumber,
      selected_option: selectedOption,
    });
  }

  async submitExam(examId) {
    return this.post(`/exams/${examId}/submit`, {});
  }

  // ==================== Questions ====================

  async getQuestions(filters = {}) {
    return this.get('/questions', filters);
  }

  async createQuestion(questionData) {
    return this.post('/questions', questionData);
  }

  async updateQuestion(questionId, questionData) {
    return this.put(`/questions/${questionId}`, questionData);
  }

  async deleteQuestion(questionId) {
    return this.delete(`/questions/${questionId}`);
  }

  async uploadQuestionImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/questions/upload-image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Image upload failed');
    }

    return response.json();
  }

  // ==================== Analytics ====================

  async getStudentDashboard() {
    return this.get('/analytics/dashboard/student');
  }

  async getLeaderboard(studentClass = 'XII') {
    return this.get('/analytics/leaderboard', { class: studentClass });
  }

  // ==================== Subscriptions ====================

  async getSubscriptionPlans() {
    return this.get('/subscription-plans');
  }

  async getMySubscription() {
    return this.get('/subscriptions/my');
  }

  async checkExamEntitlement() {
    return this.get('/entitlements/check-exam');
  }

  // ==================== Evaluations (Teacher) ====================

  async getPendingEvaluations() {
    return this.get('/evaluations/pending');
  }

  async startEvaluation(evaluationId) {
    return this.post(`/evaluations/${evaluationId}/start`, {});
  }

  async submitQuestionMarks(evaluationId, marks) {
    return this.post(`/evaluations/${evaluationId}/marks`, marks);
  }

  async completeEvaluation(evaluationId) {
    return this.post(`/evaluations/${evaluationId}/complete`, {});
  }
}

// Export singleton instance
const api = new ApiClient();
