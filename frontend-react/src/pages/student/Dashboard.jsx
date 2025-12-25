/**
 * Student Dashboard Page
 * Overview of student's exam performance and quick exam start
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { analyticsAPI, examsAPI } from '../../services/api';
import { MathText } from '../../components/common/MathRenderer';
import { FiPlay, FiFileText, FiTrendingUp, FiAward, FiClock, FiCheckCircle } from 'react-icons/fi';
import toast from 'react-hot-toast';
import styles from './Dashboard.module.css';

// CBSE Units
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

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [examTab, setExamTab] = useState('unit'); // 'unit' or 'board'
  const [selectedUnits, setSelectedUnits] = useState([]);
  const [startingExam, setStartingExam] = useState(false);

  const studentClass = user?.student_class || 'XII';
  const availableUnits = UNITS[studentClass] || UNITS.XII;

  useEffect(() => {
    loadDashboard();
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await examsAPI.getTemplates();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadDashboard = async () => {
    try {
      const data = await analyticsAPI.getStudentDashboard();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      // Use mock data for demo
      setDashboardData({
        exams_taken_this_month: 3,
        monthly_limit: 50,
        average_score: 78.5,
        class_rank: 12,
        recent_exams: [],
        board_prediction: {
          predicted_percentage: 85,
          confidence_level: 'medium',
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUnitToggle = (unit) => {
    setSelectedUnits((prev) =>
      prev.includes(unit) ? prev.filter((u) => u !== unit) : [...prev, unit]
    );
  };

  const handleStartExam = async (examType) => {
    if (examType === 'unit' && selectedUnits.length === 0) {
      toast.error('Please select at least one unit');
      return;
    }

    // Find the appropriate template for the exam type
    // unit_wise uses section_mcq template, board uses board_exam template
    const targetExamType = examType === 'unit' ? 'section_mcq' : 'board_exam';
    const template = templates.find((t) => t.exam_type === targetExamType);

    if (!template) {
      toast.error('No exam template available. Please contact support.');
      return;
    }

    setStartingExam(true);
    try {
      const data = await examsAPI.startExam(
        template.template_id,
        targetExamType,
        selectedUnits
      );

      // Store exam data for the exam interface
      localStorage.setItem('current_exam', JSON.stringify(data));
      toast.success('Exam started! Good luck!');
      navigate('/student/take-exam');
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to start exam';
      toast.error(message);
    } finally {
      setStartingExam(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      evaluated: { label: 'Evaluated', class: 'badge-success' },
      pending_evaluation: { label: 'Pending', class: 'badge-warning' },
      in_progress: { label: 'In Progress', class: 'badge-primary' },
      submitted_mcq: { label: 'MCQ Submitted', class: 'badge-success' },
      submitted: { label: 'Submitted', class: 'badge-success' },
      under_evaluation: { label: 'Under Review', class: 'badge-warning' },
    };
    const s = statusMap[status] || { label: status, class: 'badge-gray' };
    return <span className={`badge ${s.class}`}>{s.label}</span>;
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Welcome Section */}
      <div className={styles.welcome}>
        <div>
          <h1>Welcome back, {user?.first_name}! 👋</h1>
          <p className="text-gray">Keep practicing to ace your board exams</p>
        </div>
        <div className={styles.classTag}>Class {studentClass}</div>
      </div>

      {/* Stats Cards */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ background: 'var(--color-primary)' }}>
            <FiFileText size={24} />
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>
              {dashboardData?.total_exams || 0}
            </span>
            <span className={styles.statLabel}>Total Exams</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ background: 'var(--color-accent)' }}>
            <FiTrendingUp size={24} />
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>
              {dashboardData?.overall_percentage?.toFixed(1) || '0.0'}%
            </span>
            <span className={styles.statLabel}>Average Score</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ background: 'var(--color-secondary)' }}>
            <FiAward size={24} />
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>
              #{dashboardData?.overall_rank || '-'}
            </span>
            <span className={styles.statLabel}>Class Rank</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon} style={{ background: 'var(--color-warning)' }}>
            <FiCheckCircle size={24} />
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>
              {dashboardData?.exams_completed || 0}
            </span>
            <span className={styles.statLabel}>Completed</span>
          </div>
        </div>
      </div>

      {/* Start Exam Section */}
      <div className={styles.examSection}>
        <h2>Start New Exam</h2>

        {/* Exam Type Tabs */}
        <div className={styles.examTabs}>
          <button
            className={`${styles.examTab} ${examTab === 'unit' ? styles.active : ''}`}
            onClick={() => setExamTab('unit')}
          >
            <FiPlay /> Unit-Wise Practice
          </button>
          <button
            className={`${styles.examTab} ${examTab === 'board' ? styles.active : ''}`}
            onClick={() => setExamTab('board')}
          >
            <FiFileText /> Full Board Exam
          </button>
        </div>

        {/* Unit Selection */}
        {examTab === 'unit' && (
          <div className={styles.unitSelection}>
            <p className="text-gray mb-3">
              Select the units you want to practice ({selectedUnits.length} selected)
            </p>
            <div className={styles.unitGrid}>
              {availableUnits.map((unit, index) => (
                <label
                  key={unit}
                  className={`${styles.unitCard} ${
                    selectedUnits.includes(unit) ? styles.selected : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedUnits.includes(unit)}
                    onChange={() => handleUnitToggle(unit)}
                  />
                  <span className={styles.unitNumber}>{index + 1}</span>
                  <span className={styles.unitName}>{unit}</span>
                  <FiCheckCircle className={styles.unitCheck} />
                </label>
              ))}
            </div>
            <button
              className="btn btn-primary btn-lg mt-4"
              onClick={() => handleStartExam('unit')}
              disabled={startingExam || selectedUnits.length === 0}
            >
              {startingExam ? (
                <>
                  <span className="spinner"></span> Starting...
                </>
              ) : (
                <>
                  <FiPlay /> Start Unit-Wise Exam
                </>
              )}
            </button>
          </div>
        )}

        {/* Board Exam Option */}
        {examTab === 'board' && (
          <div className={styles.boardExamCard}>
            <div className={styles.boardExamInfo}>
              <h3>CBSE Class {studentClass} Board Exam Pattern</h3>
              <div className={styles.boardExamDetails}>
                <div className={styles.detailItem}>
                  <FiClock />
                  <span>3 Hours</span>
                </div>
                <div className={styles.detailItem}>
                  <FiFileText />
                  <span>80 Marks</span>
                </div>
                <div className={styles.detailItem}>
                  <FiCheckCircle />
                  <span>38 Questions</span>
                </div>
              </div>
              <p className="text-gray">
                Full CBSE board exam pattern with MCQ, VSA, and SA questions from all units.
              </p>
            </div>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => handleStartExam('board')}
              disabled={startingExam}
            >
              {startingExam ? (
                <>
                  <span className="spinner"></span> Starting...
                </>
              ) : (
                <>
                  <FiPlay /> Start Board Exam
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Recent Exams */}
      <div className={styles.recentExams}>
        <h2>Recent Exams</h2>
        {dashboardData?.recent_exams?.length > 0 ? (
          <div className={styles.tableContainer}>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.recent_exams.map((exam) => (
                  <tr key={exam.exam_instance_id}>
                    <td>{formatDate(exam.started_at)}</td>
                    <td>
                      <span className="badge badge-gray">{exam.exam_type}</span>
                    </td>
                    <td>
                      {exam.mcq_score !== null || exam.total_score !== null
                        ? `${exam.total_score || exam.mcq_score || 0}/${exam.total_marks}`
                        : '-'}
                    </td>
                    <td>{getStatusBadge(exam.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={styles.emptyState}>
            <FiFileText size={48} />
            <p>No exams taken yet. Start your first exam!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
