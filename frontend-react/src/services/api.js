/**
 * Mathvidya API Service
 * Centralized API client with authentication handling
 */

import axios from 'axios';

// Use relative URL for proxy in development, or explicit URL for production
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'Token:', token ? 'present' : 'missing');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== Authentication ====================

export const authAPI = {
  login: async (email, password) => {
    // Backend expects JSON body with email and password
    const response = await api.post('/auth/login', {
      email,
      password,
    });

    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }

    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// ==================== Questions ====================

export const questionsAPI = {
  // Search questions with filters and pagination
  getQuestions: async (params = {}) => {
    const { skip = 0, limit = 10, ...filters } = params;
    const page = Math.floor(skip / limit) + 1;

    // Map frontend field names to backend field names
    const filterBody = {};
    if (filters.question_type) filterBody.question_type = filters.question_type;
    if (filters.student_class) filterBody.class_level = filters.student_class;
    if (filters.unit) filterBody.unit = filters.unit;
    if (filters.difficulty) filterBody.difficulty = filters.difficulty;

    const response = await api.post('/questions/search', filterBody, {
      params: { page, page_size: limit },
    });
    return response.data;
  },

  getQuestion: async (questionId) => {
    const response = await api.get(`/questions/${questionId}`);
    return response.data;
  },

  createQuestion: async (questionData) => {
    // Map frontend field names to backend field names
    // Backend expects options as a List[str], not an object
    const payload = {
      question_type: questionData.question_type,
      class_level: questionData.student_class,
      unit: questionData.unit,
      topic: questionData.topic,
      difficulty: questionData.difficulty,
      marks: questionData.marks,
      question_text: questionData.question_text,
      question_image_url: questionData.image_url || null,
      options: questionData.question_type === 'MCQ' ? [
        questionData.option_a,
        questionData.option_b,
        questionData.option_c,
        questionData.option_d,
      ] : null,
      correct_option: questionData.question_type === 'MCQ' ? questionData.correct_answer : null,
      model_answer: questionData.explanation || null,
    };
    const response = await api.post('/questions', payload);
    return response.data;
  },

  updateQuestion: async (questionId, questionData) => {
    // Map frontend field names to backend field names
    // Backend expects options as a List[str], not an object
    const payload = {
      question_type: questionData.question_type,
      class_level: questionData.student_class,
      unit: questionData.unit,
      topic: questionData.topic,
      difficulty: questionData.difficulty,
      marks: questionData.marks,
      question_text: questionData.question_text,
      question_image_url: questionData.image_url || null,
      options: questionData.question_type === 'MCQ' ? [
        questionData.option_a,
        questionData.option_b,
        questionData.option_c,
        questionData.option_d,
      ] : null,
      correct_option: questionData.question_type === 'MCQ' ? questionData.correct_answer : null,
      model_answer: questionData.explanation || null,
    };
    const response = await api.put(`/questions/${questionId}`, payload);
    return response.data;
  },

  deleteQuestion: async (questionId) => {
    const response = await api.delete(`/questions/${questionId}`);
    return response.data;
  },

  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/questions/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/questions/stats/overview');
    return response.data;
  },

  checkDuplicate: async (questionText, classLevel = null, excludeQuestionId = null) => {
    const payload = {
      question_text: questionText,
    };
    if (classLevel) payload.class_level = classLevel;
    if (excludeQuestionId) payload.exclude_question_id = excludeQuestionId;

    const response = await api.post('/questions/check-duplicate', payload);
    return response.data;
  },
};

// ==================== Exams ====================

export const examsAPI = {
  getTemplates: async () => {
    const response = await api.get('/exams/templates');
    return response.data;
  },

  startExam: async (templateId, examType, selectedUnits = []) => {
    const response = await api.post('/exams/start', {
      template_id: templateId,
      exam_type: examType,
      selected_units: selectedUnits,
    });
    return response.data;
  },

  getExam: async (examId) => {
    const response = await api.get(`/exams/${examId}`);
    return response.data;
  },

  submitMCQAnswer: async (examId, questionNumber, selectedOption) => {
    const response = await api.post(`/exams/${examId}/mcq`, {
      question_number: questionNumber,
      selected_option: selectedOption,
    });
    return response.data;
  },

  submitMCQ: async (examInstanceId, answers) => {
    // answers is an array of { question_id, selected_option }
    const response = await api.post('/exams/submit-mcq', {
      exam_instance_id: examInstanceId,
      answers: answers,
    });
    return response.data;
  },

  submitExam: async (examId) => {
    const response = await api.post(`/exams/${examId}/submit`);
    return response.data;
  },
};

// ==================== Analytics ====================

export const analyticsAPI = {
  getStudentDashboard: async () => {
    const response = await api.get('/analytics/dashboard/student');
    return response.data;
  },

  getTeacherDashboard: async () => {
    const response = await api.get('/analytics/dashboard/teacher');
    return response.data;
  },

  getLeaderboard: async (studentClass = 'XII') => {
    const response = await api.get('/analytics/leaderboard', {
      params: { student_class: studentClass },
    });
    return response.data;
  },
};

// ==================== Evaluations ====================

export const evaluationsAPI = {
  getPending: async () => {
    const response = await api.get('/evaluations/pending');
    return response.data;
  },

  startEvaluation: async (evaluationId) => {
    const response = await api.post(`/evaluations/${evaluationId}/start`);
    return response.data;
  },

  submitMarks: async (evaluationId, marks) => {
    const response = await api.post(`/evaluations/${evaluationId}/marks`, marks);
    return response.data;
  },

  completeEvaluation: async (evaluationId) => {
    const response = await api.post(`/evaluations/${evaluationId}/complete`);
    return response.data;
  },
};

// ==================== Subscriptions ====================

export const subscriptionsAPI = {
  getPlans: async () => {
    const response = await api.get('/subscription-plans');
    return response.data;
  },

  getMySubscription: async () => {
    const response = await api.get('/subscriptions/my');
    return response.data;
  },

  checkExamEntitlement: async () => {
    const response = await api.get('/entitlements/check-exam');
    return response.data;
  },
};

export default api;
