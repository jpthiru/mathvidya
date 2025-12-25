/**
 * Take Exam Page
 * MCQ exam interface with timer, question navigation, and submission
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { examsAPI } from '../../services/api';
import { MathText } from '../../components/common/MathRenderer';
import { FiClock, FiChevronLeft, FiChevronRight, FiCheck, FiAlertCircle, FiX } from 'react-icons/fi';
import toast from 'react-hot-toast';
import styles from './TakeExam.module.css';

const TakeExam = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [examData, setExamData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirmExit, setShowConfirmExit] = useState(false);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);

  // Load exam data from localStorage
  useEffect(() => {
    const storedExam = localStorage.getItem('current_exam');
    if (storedExam) {
      try {
        const exam = JSON.parse(storedExam);
        setExamData(exam);
        // Calculate remaining time
        const startTime = new Date(exam.start_time);
        const now = new Date();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        const totalSeconds = exam.duration_minutes * 60;
        const remaining = Math.max(0, totalSeconds - elapsedSeconds);
        setTimeRemaining(remaining);
      } catch (error) {
        console.error('Failed to parse exam data:', error);
        toast.error('Failed to load exam data');
        navigate('/student/dashboard');
      }
    } else {
      toast.error('No active exam found');
      navigate('/student/dashboard');
    }
  }, [navigate]);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const handleAutoSubmit = useCallback(async () => {
    toast.error('Time is up! Submitting your exam...');
    await handleSubmit(true);
  }, []);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerSelect = (questionId, option) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const handleNext = () => {
    if (examData && currentQuestionIndex < examData.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const handleQuestionJump = (index) => {
    setCurrentQuestionIndex(index);
  };

  const handleSubmit = async (isAutoSubmit = false) => {
    if (submitting) return;

    const answeredCount = Object.keys(answers).length;
    const totalQuestions = examData?.questions?.length || 0;

    if (!isAutoSubmit && answeredCount < totalQuestions) {
      setShowConfirmSubmit(true);
      return;
    }

    setSubmitting(true);
    setShowConfirmSubmit(false);

    try {
      // Format answers for API
      const formattedAnswers = Object.entries(answers).map(([questionId, selectedOption]) => ({
        question_id: questionId,
        selected_option: selectedOption,
      }));

      const result = await examsAPI.submitMCQ(examData.exam_instance_id, formattedAnswers);

      // Clear exam data from localStorage
      localStorage.removeItem('current_exam');

      // Show result
      toast.success(`Exam submitted! Score: ${result.correct_answers}/${result.total_mcq_questions} (${result.mcq_percentage}%)`);

      // Navigate back to dashboard
      navigate('/student/dashboard');
    } catch (error) {
      console.error('Failed to submit exam:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit exam');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExitExam = () => {
    setShowConfirmExit(true);
  };

  const confirmExit = () => {
    localStorage.removeItem('current_exam');
    toast.error('Exam abandoned. Your progress was not saved.');
    navigate('/student/dashboard');
  };

  if (!examData) {
    return (
      <div className={styles.loadingContainer}>
        <div className="spinner"></div>
        <p>Loading exam...</p>
      </div>
    );
  }

  const currentQuestion = examData.questions[currentQuestionIndex];
  const answeredCount = Object.keys(answers).length;
  const totalQuestions = examData.questions.length;
  const isTimeWarning = timeRemaining < 300; // Less than 5 minutes

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.examInfo}>
          <h1>MCQ Practice Exam</h1>
          <span className={styles.progress}>
            {answeredCount}/{totalQuestions} answered
          </span>
        </div>
        <div className={styles.headerActions}>
          <div className={`${styles.timer} ${isTimeWarning ? styles.timerWarning : ''}`}>
            <FiClock />
            <span>{formatTime(timeRemaining)}</span>
          </div>
          <button className={styles.exitBtn} onClick={handleExitExam}>
            <FiX /> Exit
          </button>
        </div>
      </div>

      <div className={styles.mainContent}>
        {/* Question Panel */}
        <div className={styles.questionPanel}>
          <div className={styles.questionHeader}>
            <span className={styles.questionNumber}>Question {currentQuestionIndex + 1}</span>
            <span className={styles.marks}>{currentQuestion.marks} mark</span>
          </div>

          <div className={styles.questionContent}>
            <div className={styles.questionText}>
              <MathText text={currentQuestion.question_text} />
            </div>

            {currentQuestion.question_image_url && (
              <div className={styles.questionImage}>
                <img src={currentQuestion.question_image_url} alt="Question diagram" />
              </div>
            )}

            <div className={styles.options}>
              {currentQuestion.options?.map((option, index) => {
                const optionLetter = String.fromCharCode(65 + index); // A, B, C, D
                const isSelected = answers[currentQuestion.question_id] === optionLetter;

                return (
                  <label
                    key={index}
                    className={`${styles.option} ${isSelected ? styles.selected : ''}`}
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.question_id}`}
                      checked={isSelected}
                      onChange={() => handleAnswerSelect(currentQuestion.question_id, optionLetter)}
                    />
                    <span className={styles.optionLetter}>{optionLetter}</span>
                    <span className={styles.optionText}>
                      <MathText text={option} />
                    </span>
                    {isSelected && <FiCheck className={styles.checkIcon} />}
                  </label>
                );
              })}
            </div>
          </div>

          <div className={styles.navigation}>
            <button
              className="btn btn-secondary"
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
            >
              <FiChevronLeft /> Previous
            </button>

            {currentQuestionIndex === totalQuestions - 1 ? (
              <button
                className="btn btn-primary"
                onClick={() => handleSubmit(false)}
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : 'Submit Exam'}
              </button>
            ) : (
              <button
                className="btn btn-primary"
                onClick={handleNext}
              >
                Next <FiChevronRight />
              </button>
            )}
          </div>
        </div>

        {/* Question Navigator */}
        <div className={styles.navigator}>
          <h3>Questions</h3>
          <div className={styles.questionGrid}>
            {examData.questions.map((q, index) => {
              const isAnswered = answers[q.question_id];
              const isCurrent = index === currentQuestionIndex;

              return (
                <button
                  key={q.question_id}
                  className={`${styles.navButton} ${isAnswered ? styles.answered : ''} ${isCurrent ? styles.current : ''}`}
                  onClick={() => handleQuestionJump(index)}
                >
                  {index + 1}
                </button>
              );
            })}
          </div>
          <div className={styles.legend}>
            <div className={styles.legendItem}>
              <span className={`${styles.legendDot} ${styles.answered}`}></span>
              Answered
            </div>
            <div className={styles.legendItem}>
              <span className={`${styles.legendDot} ${styles.unanswered}`}></span>
              Unanswered
            </div>
            <div className={styles.legendItem}>
              <span className={`${styles.legendDot} ${styles.current}`}></span>
              Current
            </div>
          </div>
          <button
            className={`btn btn-primary ${styles.submitBtn}`}
            onClick={() => handleSubmit(false)}
            disabled={submitting}
          >
            {submitting ? 'Submitting...' : 'Submit Exam'}
          </button>
        </div>
      </div>

      {/* Confirm Exit Modal */}
      {showConfirmExit && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <FiAlertCircle className={styles.modalIcon} />
            <h2>Exit Exam?</h2>
            <p>Are you sure you want to exit? Your answers will NOT be saved and you will need to start a new exam.</p>
            <div className={styles.modalActions}>
              <button className="btn btn-secondary" onClick={() => setShowConfirmExit(false)}>
                Continue Exam
              </button>
              <button className="btn btn-danger" onClick={confirmExit}>
                Exit Anyway
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Submit Modal */}
      {showConfirmSubmit && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <FiAlertCircle className={styles.modalIcon} />
            <h2>Submit Incomplete Exam?</h2>
            <p>
              You have answered {answeredCount} out of {totalQuestions} questions.
              Unanswered questions will be marked as incorrect.
            </p>
            <div className={styles.modalActions}>
              <button className="btn btn-secondary" onClick={() => setShowConfirmSubmit(false)}>
                Review Answers
              </button>
              <button className="btn btn-primary" onClick={() => handleSubmit(true)}>
                Submit Anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TakeExam;
