/**
 * Mathvidya API Client
 * Handles all backend communication
 */

// Detect environment and set appropriate API base URL
// - localhost: Use port 8000 where uvicorn runs
// - Production (EC2): Use relative path (nginx proxies to backend)
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';

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
        // Handle FastAPI validation errors (array of objects)
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        if (error.detail) {
          if (Array.isArray(error.detail)) {
            // FastAPI validation errors: [{loc: [...], msg: "...", type: "..."}, ...]
            errorMessage = error.detail.map(e => {
              const field = e.loc ? e.loc.slice(1).join('.') : 'unknown';
              return `${field}: ${e.msg}`;
            }).join('; ');
          } else if (typeof error.detail === 'string') {
            errorMessage = error.detail;
          }
        }
        throw new Error(errorMessage);
      }

      // Handle 204 No Content (e.g., DELETE operations)
      if (response.status === 204) {
        return null;
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
    const data = await this.post('/auth/register', userData);
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

    const response = await fetch(`${this.baseURL}/auth/login`, {
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
    // Always clear token, even if API call fails (e.g., token already expired)
    try {
      await this.post('/auth/logout');
    } catch (error) {
      console.log('Logout API call failed (token may have expired), clearing local session');
    }
    this.clearToken();
  }

  async getMe() {
    return this.get('/auth/me');
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

  async startUnitExam(units, questionType) {
    return this.post('/exams/start-unit-practice', {
      selected_units: units,
      question_type: questionType,
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

  async getQuestions(filters = {}, page = 1, pageSize = 20) {
    // Backend uses POST /questions/search for listing with query params for pagination
    return this.post(`/questions/search?page=${page}&page_size=${pageSize}`, filters);
  }

  async getQuestion(questionId) {
    return this.get(`/questions/${questionId}`);
  }

  async getQuestionStats() {
    return this.get('/questions/stats/overview');
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

  async checkDuplicateQuestion(questionText, classLevel = null, excludeQuestionId = null) {
    const data = {
      question_text: questionText
    };
    if (classLevel) data.class_level = classLevel;
    if (excludeQuestionId) data.exclude_question_id = excludeQuestionId;
    return this.post('/questions/check-duplicate', data);
  }

  async verifyQuestion(questionId) {
    return this.post(`/questions/${questionId}/verify`, {});
  }

  async getUnverifiedStats() {
    return this.get('/questions/stats/unverified');
  }

  async getUnverifiedQuestions(filters = {}) {
    // Add is_verified: false filter for unverified questions
    return this.post('/questions/search', { ...filters, is_verified: false });
  }

  async uploadQuestionImage(questionId, fileName) {
    // Get presigned URL from backend
    const response = await this.post(`/questions/${questionId}/upload-image`, {
      file_name: fileName
    });
    return response;
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
    return this.get('/evaluations/my-pending');
  }

  async getTeacherWorkload() {
    return this.get('/evaluations/teacher/workload');
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
