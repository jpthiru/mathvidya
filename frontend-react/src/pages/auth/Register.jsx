/**
 * Registration Page
 * Student/Parent registration with terms acceptance
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { FiMail, FiLock, FiEye, FiEyeOff, FiUser, FiPhone, FiCheckSquare, FiSquare } from 'react-icons/fi';
import styles from './Register.module.css';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    studentClass: 'XII',
    parentName: '',
    parentEmail: '',
    parentPhone: '',
    acceptTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    // Student name
    if (!formData.name.trim()) {
      newErrors.name = 'Student name is required';
    }

    // Email
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    // Phone (Indian format)
    if (!formData.phone) {
      newErrors.phone = 'Phone number is required';
    } else if (!/^[6-9]\d{9}$/.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Please enter a valid 10-digit Indian mobile number';
    }

    // Password
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    // Confirm password
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Parent/Guardian info (mandatory for students who are minors)
    if (!formData.parentName.trim()) {
      newErrors.parentName = 'Parent/Guardian name is required';
    }

    if (!formData.parentEmail) {
      newErrors.parentEmail = 'Parent/Guardian email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.parentEmail)) {
      newErrors.parentEmail = 'Please enter a valid email';
    }

    if (!formData.parentPhone) {
      newErrors.parentPhone = 'Parent/Guardian phone is required';
    } else if (!/^[6-9]\d{9}$/.test(formData.parentPhone.replace(/\s/g, ''))) {
      newErrors.parentPhone = 'Please enter a valid 10-digit mobile number';
    }

    // Terms acceptance (mandatory)
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the Terms and Conditions to register';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    try {
      await register({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        student_class: formData.studentClass,
        parent_name: formData.parentName,
        parent_email: formData.parentEmail,
        parent_phone: formData.parentPhone,
        terms_accepted: formData.acceptTerms,
        terms_accepted_at: new Date().toISOString(),
      });
      navigate('/student/dashboard');
    } catch (error) {
      setErrors({ submit: error.response?.data?.detail || 'Registration failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
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
          <h2>Start Your Journey to Excellence</h2>
          <p>Join thousands of students achieving top scores in CBSE Mathematics with expert guidance.</p>

          <div className={styles.features}>
            <div className={styles.feature}>
              <span>✓</span> Board Exam Aligned Practice
            </div>
            <div className={styles.feature}>
              <span>✓</span> Expert Teacher Evaluation
            </div>
            <div className={styles.feature}>
              <span>✓</span> Performance Analytics
            </div>
            <div className={styles.feature}>
              <span>✓</span> Predicted Board Scores
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Registration Form */}
      <div className={styles.formSide}>
        <div className={styles.formContainer}>
          <h2>Create Account</h2>
          <p className="text-gray">Register as a student to get started</p>

          <form onSubmit={handleSubmit} className={styles.form}>
            {errors.submit && (
              <div className={styles.errorAlert}>{errors.submit}</div>
            )}

            {/* Student Information Section */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Student Information</h3>

              {/* Name */}
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <div className={styles.inputWrapper}>
                  <FiUser className={styles.inputIcon} />
                  <input
                    type="text"
                    className={`form-input ${errors.name ? 'error' : ''}`}
                    placeholder="Enter student's full name"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                  />
                </div>
                {errors.name && <span className="form-error">{errors.name}</span>}
              </div>

              {/* Email & Phone Row */}
              <div className={styles.row}>
                <div className="form-group">
                  <label className="form-label">Email *</label>
                  <div className={styles.inputWrapper}>
                    <FiMail className={styles.inputIcon} />
                    <input
                      type="email"
                      className={`form-input ${errors.email ? 'error' : ''}`}
                      placeholder="student@email.com"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                    />
                  </div>
                  {errors.email && <span className="form-error">{errors.email}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Phone *</label>
                  <div className={styles.inputWrapper}>
                    <FiPhone className={styles.inputIcon} />
                    <input
                      type="tel"
                      className={`form-input ${errors.phone ? 'error' : ''}`}
                      placeholder="9876543210"
                      value={formData.phone}
                      onChange={(e) => handleChange('phone', e.target.value)}
                    />
                  </div>
                  {errors.phone && <span className="form-error">{errors.phone}</span>}
                </div>
              </div>

              {/* Class Selection */}
              <div className="form-group">
                <label className="form-label">Class *</label>
                <div className={styles.classSelector}>
                  <button
                    type="button"
                    className={`${styles.classBtn} ${formData.studentClass === 'X' ? styles.active : ''}`}
                    onClick={() => handleChange('studentClass', 'X')}
                  >
                    Class X
                  </button>
                  <button
                    type="button"
                    className={`${styles.classBtn} ${formData.studentClass === 'XII' ? styles.active : ''}`}
                    onClick={() => handleChange('studentClass', 'XII')}
                  >
                    Class XII
                  </button>
                </div>
              </div>

              {/* Password Fields */}
              <div className={styles.row}>
                <div className="form-group">
                  <label className="form-label">Password *</label>
                  <div className={styles.inputWrapper}>
                    <FiLock className={styles.inputIcon} />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className={`form-input ${errors.password ? 'error' : ''}`}
                      placeholder="Min. 8 characters"
                      value={formData.password}
                      onChange={(e) => handleChange('password', e.target.value)}
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

                <div className="form-group">
                  <label className="form-label">Confirm Password *</label>
                  <div className={styles.inputWrapper}>
                    <FiLock className={styles.inputIcon} />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                      placeholder="Confirm password"
                      value={formData.confirmPassword}
                      onChange={(e) => handleChange('confirmPassword', e.target.value)}
                    />
                    <button
                      type="button"
                      className={styles.togglePassword}
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                    </button>
                  </div>
                  {errors.confirmPassword && <span className="form-error">{errors.confirmPassword}</span>}
                </div>
              </div>
            </div>

            {/* Parent/Guardian Information Section */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>Parent/Guardian Information</h3>
              <p className={styles.sectionNote}>Required for students under 18 years</p>

              {/* Parent Name */}
              <div className="form-group">
                <label className="form-label">Parent/Guardian Name *</label>
                <div className={styles.inputWrapper}>
                  <FiUser className={styles.inputIcon} />
                  <input
                    type="text"
                    className={`form-input ${errors.parentName ? 'error' : ''}`}
                    placeholder="Enter parent/guardian name"
                    value={formData.parentName}
                    onChange={(e) => handleChange('parentName', e.target.value)}
                  />
                </div>
                {errors.parentName && <span className="form-error">{errors.parentName}</span>}
              </div>

              {/* Parent Email & Phone */}
              <div className={styles.row}>
                <div className="form-group">
                  <label className="form-label">Parent Email *</label>
                  <div className={styles.inputWrapper}>
                    <FiMail className={styles.inputIcon} />
                    <input
                      type="email"
                      className={`form-input ${errors.parentEmail ? 'error' : ''}`}
                      placeholder="parent@email.com"
                      value={formData.parentEmail}
                      onChange={(e) => handleChange('parentEmail', e.target.value)}
                    />
                  </div>
                  {errors.parentEmail && <span className="form-error">{errors.parentEmail}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Parent Phone *</label>
                  <div className={styles.inputWrapper}>
                    <FiPhone className={styles.inputIcon} />
                    <input
                      type="tel"
                      className={`form-input ${errors.parentPhone ? 'error' : ''}`}
                      placeholder="9876543210"
                      value={formData.parentPhone}
                      onChange={(e) => handleChange('parentPhone', e.target.value)}
                    />
                  </div>
                  {errors.parentPhone && <span className="form-error">{errors.parentPhone}</span>}
                </div>
              </div>
            </div>

            {/* Terms Acceptance */}
            <div className={styles.termsSection}>
              <label
                className={`${styles.termsCheckbox} ${errors.acceptTerms ? styles.termsError : ''}`}
                onClick={() => handleChange('acceptTerms', !formData.acceptTerms)}
              >
                {formData.acceptTerms ? (
                  <FiCheckSquare className={styles.checkIcon} />
                ) : (
                  <FiSquare className={styles.checkIcon} />
                )}
                <span>
                  I agree to the{' '}
                  <Link to="/terms-and-conditions" target="_blank" onClick={(e) => e.stopPropagation()}>
                    Terms and Conditions
                  </Link>
                  {' '}and{' '}
                  <Link to="/privacy-policy" target="_blank" onClick={(e) => e.stopPropagation()}>
                    Privacy Policy
                  </Link>
                </span>
              </label>
              {errors.acceptTerms && <span className="form-error">{errors.acceptTerms}</span>}
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
                  Creating Account...
                </>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className={styles.loginLink}>
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>

          {/* Legal Links */}
          <div className={styles.legalLinks}>
            <Link to="/terms-and-conditions">Terms</Link>
            <span className={styles.separator}>•</span>
            <Link to="/privacy-policy">Privacy</Link>
            <span className={styles.separator}>•</span>
            <Link to="/refund-policy">Refunds</Link>
            <span className={styles.separator}>•</span>
            <Link to="/pricing">Pricing</Link>
            <span className={styles.separator}>•</span>
            <Link to="/contact-us">Contact</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
