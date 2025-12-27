/**
 * Teacher Question Management Page
 * CRUD operations for MCQ questions with LaTeX support
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { questionsAPI } from '../../services/api';
import { MathText, MathToolbar } from '../../components/common/MathRenderer';
import { FiPlus, FiEdit2, FiTrash2, FiFilter, FiX, FiUpload, FiChevronLeft, FiChevronRight, FiRefreshCw, FiAlertTriangle } from 'react-icons/fi';
import toast from 'react-hot-toast';
import styles from './Questions.module.css';

// Debounce helper
const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// CBSE Units for Class X and XII
const UNITS = {
  X: [
    'Number Systems',
    'Algebra',
    'Coordinate Geometry',
    'Geometry',
    'Trigonometry',
    'Mensuration',
    'Statistics & Probability',
  ],
  XII: [
    'Relations and Functions',
    'Inverse Trigonometric Functions',
    'Matrices',
    'Determinants',
    'Continuity and Differentiability',
    'Applications of Derivatives',
    'Integrals',
    'Applications of Integrals',
    'Differential Equations',
    'Vectors',
    'Three Dimensional Geometry',
    'Linear Programming',
    'Probability',
  ],
};

const ITEMS_PER_PAGE = 10;

const Questions = () => {
  console.log('Questions component rendering');

  // State for questions list
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // State for filters
  const [filters, setFilters] = useState({
    question_type: '',
    student_class: '',
    unit: '',
    difficulty: '',
  });

  // State for modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    question_type: 'MCQ',
    student_class: 'XII',
    unit: '',
    topic: '',
    difficulty: 'medium',
    marks: 1,
    question_text: '',
    image_url: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_answer: 'A',
    explanation: '',
  });

  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [imageUploading, setImageUploading] = useState(false);

  // Duplicate check state
  const [duplicateCheck, setDuplicateCheck] = useState({
    checking: false,
    isDuplicate: false,
    matchingQuestion: null,
    message: '',
  });

  const fileInputRef = useRef(null);
  const questionTextRef = useRef(null);

  // Load questions on mount and when dependencies change
  useEffect(() => {
    console.log('useEffect triggered - loading questions');
    loadQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, currentPage]);

  const loadQuestions = async () => {
    console.log('loadQuestions called');
    setLoading(true);
    try {
      // Remove empty filters and add pagination
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '')
      );
      const params = {
        ...activeFilters,
        skip: (currentPage - 1) * ITEMS_PER_PAGE,
        limit: ITEMS_PER_PAGE,
      };
      console.log('Calling questionsAPI.getQuestions with params:', params);
      const data = await questionsAPI.getQuestions(params);
      console.log('API response:', data);
      setQuestions(data.questions || data || []);
      setTotalCount(data.total || data.questions?.length || 0);
    } catch (error) {
      console.error('Failed to load questions:', error);
      toast.error('Failed to load questions');
      setQuestions([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  // Debounced duplicate check function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const checkForDuplicate = useCallback(
    debounce(async (questionText, classLevel, excludeId) => {
      // Only check if question text is at least 10 characters
      if (!questionText || questionText.trim().length < 10) {
        setDuplicateCheck({
          checking: false,
          isDuplicate: false,
          matchingQuestion: null,
          message: '',
        });
        return;
      }

      setDuplicateCheck(prev => ({ ...prev, checking: true }));

      try {
        const result = await questionsAPI.checkDuplicate(
          questionText,
          classLevel,
          excludeId
        );

        setDuplicateCheck({
          checking: false,
          isDuplicate: result.is_duplicate,
          matchingQuestion: result.matching_question,
          message: result.message,
        });
      } catch (error) {
        console.error('Duplicate check failed:', error);
        setDuplicateCheck({
          checking: false,
          isDuplicate: false,
          matchingQuestion: null,
          message: '',
        });
      }
    }, 500), // 500ms debounce
    []
  );

  // Check for duplicates when question text changes
  useEffect(() => {
    if (modalOpen && formData.question_text) {
      checkForDuplicate(
        formData.question_text,
        formData.student_class,
        editingQuestion?.question_id
      );
    }
  }, [formData.question_text, formData.student_class, modalOpen, editingQuestion, checkForDuplicate]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({
      question_type: '',
      student_class: '',
      unit: '',
      difficulty: '',
    });
    setCurrentPage(1);
  };

  // Open modal for new question
  const handleAddNew = () => {
    setEditingQuestion(null);
    setFormData({
      question_type: 'MCQ',
      student_class: 'XII',
      unit: '',
      topic: '',
      difficulty: 'medium',
      marks: 1,
      question_text: '',
      image_url: '',
      option_a: '',
      option_b: '',
      option_c: '',
      option_d: '',
      correct_answer: 'A',
      explanation: '',
    });
    setFormErrors({});
    setDuplicateCheck({
      checking: false,
      isDuplicate: false,
      matchingQuestion: null,
      message: '',
    });
    setModalOpen(true);
  };

  // Open modal for editing
  const handleEdit = (question) => {
    setEditingQuestion(question);
    // Map backend field names to frontend field names
    // Backend returns options as List[str], map to option_a/b/c/d
    const options = question.options || [];
    const isArray = Array.isArray(options);
    setFormData({
      question_type: question.question_type || 'MCQ',
      student_class: question.class_level || question.student_class || 'XII',
      unit: question.unit || '',
      topic: question.topic || '',
      difficulty: question.difficulty || 'medium',
      marks: question.marks || 1,
      question_text: question.question_text || '',
      image_url: question.question_image_url || question.image_url || '',
      option_a: isArray ? (options[0] || '') : (options.A || ''),
      option_b: isArray ? (options[1] || '') : (options.B || ''),
      option_c: isArray ? (options[2] || '') : (options.C || ''),
      option_d: isArray ? (options[3] || '') : (options.D || ''),
      correct_answer: question.correct_option || question.correct_answer || 'A',
      explanation: question.model_answer || question.explanation || '',
    });
    setFormErrors({});
    setDuplicateCheck({
      checking: false,
      isDuplicate: false,
      matchingQuestion: null,
      message: '',
    });
    setModalOpen(true);
  };

  // Delete question
  const handleDelete = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question?')) {
      return;
    }

    try {
      await questionsAPI.deleteQuestion(questionId);
      toast.success('Question deleted successfully');
      loadQuestions();
    } catch (error) {
      toast.error('Failed to delete question');
    }
  };

  // Handle image upload
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    setImageUploading(true);
    try {
      const data = await questionsAPI.uploadImage(file);
      setFormData({ ...formData, image_url: data.url });
      toast.success('Image uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload image');
    } finally {
      setImageUploading(false);
    }
  };

  // Insert math symbol at cursor
  const insertMathSymbol = (symbol) => {
    const textarea = questionTextRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = formData.question_text;

    const newText = text.substring(0, start) + `$${symbol}$` + text.substring(end);
    setFormData({ ...formData, question_text: newText });

    // Set cursor position after inserted symbol
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + symbol.length + 2, start + symbol.length + 2);
    }, 0);
  };

  // Validate form
  const validateForm = () => {
    const errors = {};

    if (!formData.unit) errors.unit = 'Unit is required';
    if (!formData.question_text.trim()) errors.question_text = 'Question text is required';

    if (formData.question_type === 'MCQ') {
      if (!formData.option_a.trim()) errors.option_a = 'Option A is required';
      if (!formData.option_b.trim()) errors.option_b = 'Option B is required';
      if (!formData.option_c.trim()) errors.option_c = 'Option C is required';
      if (!formData.option_d.trim()) errors.option_d = 'Option D is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit form
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Please fix the errors');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        marks: Number(formData.marks),
      };

      if (editingQuestion) {
        await questionsAPI.updateQuestion(editingQuestion.question_id, payload);
        toast.success('Question updated successfully');
      } else {
        await questionsAPI.createQuestion(payload);
        toast.success('Question created successfully');
      }

      setModalOpen(false);
      loadQuestions();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to save question';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Get available units based on selected class
  const availableUnits = UNITS[formData.student_class] || [];

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1>Question Bank</h1>
          <p className="text-gray">Manage MCQ questions with LaTeX math support</p>
        </div>
        <button className="btn btn-primary" onClick={handleAddNew}>
          <FiPlus /> Add New Question
        </button>
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        <div className={styles.filterIcon}>
          <FiFilter />
        </div>

        <select
          className="form-select"
          value={filters.question_type}
          onChange={(e) => handleFilterChange({ ...filters, question_type: e.target.value })}
        >
          <option value="">All Types</option>
          <option value="MCQ">MCQ</option>
          <option value="VSA">VSA</option>
          <option value="SA">SA</option>
        </select>

        <select
          className="form-select"
          value={filters.student_class}
          onChange={(e) => handleFilterChange({ ...filters, student_class: e.target.value, unit: '' })}
        >
          <option value="">All Classes</option>
          <option value="X">Class X</option>
          <option value="XII">Class XII</option>
        </select>

        <select
          className="form-select"
          value={filters.unit}
          onChange={(e) => handleFilterChange({ ...filters, unit: e.target.value })}
        >
          <option value="">All Units</option>
          {filters.student_class &&
            UNITS[filters.student_class]?.map((unit) => (
              <option key={unit} value={unit}>
                {unit}
              </option>
            ))}
        </select>

        <select
          className="form-select"
          value={filters.difficulty}
          onChange={(e) => handleFilterChange({ ...filters, difficulty: e.target.value })}
        >
          <option value="">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>

        <button
          className="btn btn-secondary btn-sm"
          onClick={clearFilters}
          title="Clear filters"
        >
          <FiRefreshCw /> Clear
        </button>

        <div className={styles.filterInfo}>
          <span className="text-sm text-gray">
            {totalCount} question{totalCount !== 1 ? 's' : ''} found
          </span>
        </div>
      </div>

      {/* Questions Table */}
      <div className={styles.tableContainer}>
        {loading ? (
          <div className={styles.loading}>
            <div className="spinner"></div>
            <p>Loading questions...</p>
          </div>
        ) : questions.length === 0 ? (
          <div className={styles.empty}>
            <p>No questions found. Add your first question!</p>
          </div>
        ) : (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Question</th>
                  <th>Type</th>
                  <th>Class</th>
                  <th>Unit</th>
                  <th>Difficulty</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((q, index) => (
                  <tr key={q.question_id}>
                    <td className="text-gray">
                      {(currentPage - 1) * ITEMS_PER_PAGE + index + 1}
                    </td>
                    <td className={styles.questionCell}>
                      <MathText text={q.question_text?.length > 80 ? q.question_text.substring(0, 80) + '...' : q.question_text || ''} />
                    </td>
                    <td>
                      <span className={`badge badge-${q.question_type === 'MCQ' ? 'primary' : 'gray'}`}>
                        {q.question_type}
                      </span>
                    </td>
                    <td>{q.class_level || q.student_class}</td>
                    <td className="text-sm">{q.unit}</td>
                    <td>
                      <span
                        className={`badge ${
                          q.difficulty === 'easy'
                            ? 'badge-success'
                            : q.difficulty === 'hard'
                            ? 'badge-error'
                            : 'badge-warning'
                        }`}
                      >
                        {q.difficulty}
                      </span>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleEdit(q)}
                          title="Edit"
                        >
                          <FiEdit2 />
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(q.question_id)}
                          title="Delete"
                        >
                          <FiTrash2 />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className={styles.pagination}>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  <FiChevronLeft /> Previous
                </button>

                <div className={styles.pageNumbers}>
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter(page => {
                      // Show first, last, current, and pages around current
                      return page === 1 ||
                        page === totalPages ||
                        Math.abs(page - currentPage) <= 1;
                    })
                    .map((page, idx, arr) => (
                      <span key={page}>
                        {idx > 0 && arr[idx - 1] !== page - 1 && (
                          <span className={styles.ellipsis}>...</span>
                        )}
                        <button
                          className={`${styles.pageBtn} ${currentPage === page ? styles.active : ''}`}
                          onClick={() => handlePageChange(page)}
                        >
                          {page}
                        </button>
                      </span>
                    ))}
                </div>

                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next <FiChevronRight />
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Add/Edit Modal */}
      {modalOpen && (
        <div className={styles.modalOverlay} onClick={() => setModalOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>{editingQuestion ? 'Edit Question' : 'Add New Question'}</h2>
              <button className={styles.closeBtn} onClick={() => setModalOpen(false)}>
                <FiX />
              </button>
            </div>

            <form onSubmit={handleSubmit} className={styles.modalBody}>
              {/* Row 1: Type, Class, Unit */}
              <div className={styles.formRow}>
                <div className="form-group">
                  <label className="form-label">Question Type</label>
                  <select
                    className="form-select"
                    value={formData.question_type}
                    onChange={(e) => setFormData({ ...formData, question_type: e.target.value })}
                  >
                    <option value="MCQ">MCQ (1 mark)</option>
                    <option value="VSA">VSA (2 marks)</option>
                    <option value="SA">SA (3 marks)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Class</label>
                  <select
                    className="form-select"
                    value={formData.student_class}
                    onChange={(e) => setFormData({ ...formData, student_class: e.target.value, unit: '' })}
                  >
                    <option value="X">Class X</option>
                    <option value="XII">Class XII</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Unit *</label>
                  <select
                    className={`form-select ${formErrors.unit ? 'error' : ''}`}
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  >
                    <option value="">Select Unit</option>
                    {availableUnits.map((unit) => (
                      <option key={unit} value={unit}>
                        {unit}
                      </option>
                    ))}
                  </select>
                  {formErrors.unit && <span className="form-error">{formErrors.unit}</span>}
                </div>
              </div>

              {/* Row 2: Topic, Difficulty, Marks */}
              <div className={styles.formRow}>
                <div className="form-group">
                  <label className="form-label">Topic (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., Quadratic Equations"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Difficulty</label>
                  <select
                    className="form-select"
                    value={formData.difficulty}
                    onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Marks</label>
                  <input
                    type="number"
                    className="form-input"
                    min="1"
                    max="10"
                    value={formData.marks}
                    onChange={(e) => setFormData({ ...formData, marks: e.target.value })}
                  />
                </div>
              </div>

              {/* Question Text with Math Toolbar */}
              <div className="form-group">
                <label className="form-label">Question Text * (Use $ for inline math, $$ for block math)</label>
                <MathToolbar onInsert={insertMathSymbol} />
                <textarea
                  ref={questionTextRef}
                  className={`form-textarea ${formErrors.question_text ? 'error' : ''} ${duplicateCheck.isDuplicate ? 'warning' : ''}`}
                  rows={4}
                  placeholder="Enter your question. Use $x^2$ for inline math or $$\frac{a}{b}$$ for block math."
                  value={formData.question_text}
                  onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
                />
                {formErrors.question_text && (
                  <span className="form-error">{formErrors.question_text}</span>
                )}

                {/* Duplicate Check Status */}
                {duplicateCheck.checking && (
                  <div className={styles.duplicateChecking}>
                    <span className="spinner-small"></span>
                    <span className="text-gray">Checking for duplicates...</span>
                  </div>
                )}

                {duplicateCheck.isDuplicate && duplicateCheck.matchingQuestion && (
                  <div className={styles.duplicateWarning}>
                    <FiAlertTriangle className={styles.warningIcon} />
                    <div className={styles.duplicateContent}>
                      <strong>Potential duplicate found!</strong>
                      <p className="text-sm">
                        A similar question exists in {duplicateCheck.matchingQuestion.unit} ({duplicateCheck.matchingQuestion.class_level}):
                      </p>
                      <div className={styles.matchingQuestion}>
                        <MathText text={duplicateCheck.matchingQuestion.question_text} />
                      </div>
                      <p className="text-sm text-gray">
                        You can still save this question if it&apos;s intentionally different.
                      </p>
                    </div>
                  </div>
                )}

                {!duplicateCheck.checking && !duplicateCheck.isDuplicate && formData.question_text.length >= 10 && (
                  <div className={styles.duplicateOk}>
                    <span className="text-success">✓ No duplicate found</span>
                  </div>
                )}

                {/* Live Preview */}
                {formData.question_text && (
                  <div className={styles.preview}>
                    <small className="text-gray">Preview:</small>
                    <div className={styles.previewContent}>
                      <MathText text={formData.question_text} />
                    </div>
                  </div>
                )}
              </div>

              {/* Image Upload */}
              <div className="form-group">
                <label className="form-label">Question Image (Optional)</label>
                <div className={styles.imageUpload}>
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept="image/*"
                    onChange={handleImageUpload}
                    hidden
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={imageUploading}
                  >
                    {imageUploading ? (
                      <span className="spinner"></span>
                    ) : (
                      <>
                        <FiUpload /> Upload Image
                      </>
                    )}
                  </button>

                  {formData.image_url && (
                    <div className={styles.imagePreview}>
                      <img src={formData.image_url} alt="Question" />
                      <button
                        type="button"
                        className={styles.removeImage}
                        onClick={() => setFormData({ ...formData, image_url: '' })}
                      >
                        <FiX />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* MCQ Options */}
              {formData.question_type === 'MCQ' && (
                <div className={styles.optionsSection}>
                  <label className="form-label">Answer Options *</label>
                  <p className="text-sm text-gray mb-2">
                    Use $ for math notation. Example: $x^2 + 1$
                  </p>

                  {['A', 'B', 'C', 'D'].map((letter) => (
                    <div key={letter} className={styles.optionRow}>
                      <label className={styles.optionRadio}>
                        <input
                          type="radio"
                          name="correct_answer"
                          value={letter}
                          checked={formData.correct_answer === letter}
                          onChange={(e) =>
                            setFormData({ ...formData, correct_answer: e.target.value })
                          }
                        />
                        <span
                          className={`${styles.optionBadge} ${
                            formData.correct_answer === letter ? styles.correct : ''
                          }`}
                        >
                          {letter}
                        </span>
                      </label>
                      <div className={styles.optionInput}>
                        <input
                          type="text"
                          className={`form-input ${
                            formErrors[`option_${letter.toLowerCase()}`] ? 'error' : ''
                          }`}
                          placeholder={`Option ${letter} (e.g., $\\frac{1}{2}$ or plain text)`}
                          value={formData[`option_${letter.toLowerCase()}`]}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              [`option_${letter.toLowerCase()}`]: e.target.value,
                            })
                          }
                        />
                        {formData[`option_${letter.toLowerCase()}`] && (
                          <small className="text-gray">
                            <MathText text={formData[`option_${letter.toLowerCase()}`]} />
                          </small>
                        )}
                      </div>
                    </div>
                  ))}
                  <small className="text-success">
                    ✓ Select the radio button next to the correct answer
                  </small>
                </div>
              )}

              {/* Explanation */}
              <div className="form-group">
                <label className="form-label">Solution / Explanation (Optional)</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Enter the solution or explanation. Math notation is supported."
                  value={formData.explanation}
                  onChange={(e) => setFormData({ ...formData, explanation: e.target.value })}
                />
                {formData.explanation && (
                  <div className={styles.preview}>
                    <small className="text-gray">Preview:</small>
                    <div className={styles.previewContent}>
                      <MathText text={formData.explanation} />
                    </div>
                  </div>
                )}
              </div>

              {/* Submit Buttons */}
              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? (
                    <>
                      <span className="spinner"></span>
                      Saving...
                    </>
                  ) : editingQuestion ? (
                    'Update Question'
                  ) : (
                    'Create Question'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Questions;
