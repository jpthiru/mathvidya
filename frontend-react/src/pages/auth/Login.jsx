/**
 * Login Page
 * Multi-role authentication with validation
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { FiMail, FiLock, FiEye, FiEyeOff, FiUser, FiBook, FiShield } from 'react-icons/fi';
import styles from './Login.module.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    role: 'student',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const roles = [
    { id: 'student', label: 'Student', icon: FiUser, color: '#6366F1' },
    { id: 'teacher', label: 'Teacher', icon: FiBook, color: '#10B981' },
    { id: 'admin', label: 'Admin', icon: FiShield, color: '#EC4899' },
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    try {
      const data = await login(formData.email, formData.password);

      // Redirect based on actual user role from backend
      const redirectMap = {
        student: '/student/dashboard',
        teacher: '/teacher/questions',
        admin: '/admin/dashboard',
      };
      const userRole = data.user?.role || formData.role;
      navigate(redirectMap[userRole] || '/');
    } catch (error) {
      setErrors({ submit: error.response?.data?.detail || 'Login failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Left Side - Branding */}
      <div className={styles.brandingSide}>
        <div className={styles.brandingContent}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>📐</span>
            <h1>Mathvidya</h1>
          </div>
          <h2>Master CBSE Mathematics</h2>
          <p>Practice with real board exam patterns and get expert teacher evaluation within 24-48 hours.</p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <span>✓</span> Expert Teacher Evaluation
            </div>
            <div className={styles.feature}>
              <span>✓</span> Board Exam Aligned Practice
            </div>
            <div className={styles.feature}>
              <span>✓</span> Performance Analytics & Prediction
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className={styles.formSide}>
        <div className={styles.formContainer}>
          <h2>Welcome Back</h2>
          <p className="text-gray">Sign in to continue your learning journey</p>

          {/* Role Selector */}
          <div className={styles.roleSelector}>
            {roles.map((role) => {
              const Icon = role.icon;
              return (
                <button
                  key={role.id}
                  type="button"
                  className={`${styles.roleBtn} ${formData.role === role.id ? styles.active : ''}`}
                  onClick={() => setFormData({ ...formData, role: role.id })}
                  style={{
                    '--role-color': role.color,
                  }}
                >
                  <Icon size={20} />
                  <span>{role.label}</span>
                </button>
              );
            })}
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className={styles.form}>
            {errors.submit && (
              <div className={styles.errorAlert}>{errors.submit}</div>
            )}

            {/* Email Field */}
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className={styles.inputWrapper}>
                <FiMail className={styles.inputIcon} />
                <input
                  type="email"
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>

            {/* Password Field */}
            <div className="form-group">
              <label className="form-label">Password</label>
              <div className={styles.inputWrapper}>
                <FiLock className={styles.inputIcon} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <button
                  type="button"
                  className={styles.togglePassword}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {errors.password && <span className="form-error">{errors.password}</span>}
            </div>

            {/* Remember Me & Forgot Password */}
            <div className={styles.formOptions}>
              <label className={styles.checkbox}>
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <Link to="/forgot-password" className={styles.forgotLink}>
                Forgot Password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary btn-lg w-full"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Register Link */}
          <p className={styles.registerLink}>
            Don't have an account?{' '}
            <Link to="/register">Create one now</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
