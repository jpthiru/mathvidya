/**
 * Feedback Widget Component
 * Floating button that opens a feedback form modal
 */

import { useState } from 'react';
import { FiMessageSquare, FiX, FiSend, FiStar } from 'react-icons/fi';
import { feedbackAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';
import styles from './FeedbackWidget.module.css';

const FEEDBACK_TYPES = [
  { value: 'suggestion', label: 'Suggestion', emoji: '💡' },
  { value: 'bug', label: 'Bug Report', emoji: '🐛' },
  { value: 'compliment', label: 'Compliment', emoji: '❤️' },
  { value: 'question', label: 'Question', emoji: '❓' },
  { value: 'other', label: 'Other', emoji: '💬' },
];

const FeedbackWidget = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    rating: 0,
    type: 'suggestion',
    message: '',
    email: '',
  });
  const [hoverRating, setHoverRating] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.message.trim() || formData.message.trim().length < 10) {
      toast.error('Please enter at least 10 characters');
      return;
    }

    setSubmitting(true);
    try {
      await feedbackAPI.submitFeedback({
        rating: formData.rating || null,
        type: formData.type,
        message: formData.message.trim(),
        email: formData.email || null,
        page: window.location.pathname,
      });

      setSubmitted(true);
      toast.success('Thank you for your feedback!');

      // Reset after 2 seconds
      setTimeout(() => {
        setIsOpen(false);
        setSubmitted(false);
        setFormData({
          rating: 0,
          type: 'suggestion',
          message: '',
          email: '',
        });
      }, 2000);
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to submit feedback';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setSubmitted(false);
  };

  return (
    <>
      {/* Floating Button */}
      <button
        className={styles.floatingButton}
        onClick={() => setIsOpen(true)}
        aria-label="Give Feedback"
      >
        <FiMessageSquare size={24} />
        <span className={styles.buttonLabel}>Feedback</span>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className={styles.overlay} onClick={handleClose}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className={styles.header}>
              <h3>Share Your Feedback</h3>
              <button className={styles.closeBtn} onClick={handleClose}>
                <FiX size={20} />
              </button>
            </div>

            {submitted ? (
              /* Success State */
              <div className={styles.successState}>
                <div className={styles.successIcon}>✅</div>
                <h4>Thank You!</h4>
                <p>Your feedback helps us improve Mathvidya.</p>
              </div>
            ) : (
              /* Feedback Form */
              <form onSubmit={handleSubmit} className={styles.form}>
                {/* Rating */}
                <div className={styles.formGroup}>
                  <label>How would you rate your experience?</label>
                  <div className={styles.starRating}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        className={`${styles.star} ${
                          (hoverRating || formData.rating) >= star ? styles.active : ''
                        }`}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => setFormData({ ...formData, rating: star })}
                      >
                        <FiStar size={28} />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Feedback Type */}
                <div className={styles.formGroup}>
                  <label>What type of feedback?</label>
                  <div className={styles.typeButtons}>
                    {FEEDBACK_TYPES.map((type) => (
                      <button
                        key={type.value}
                        type="button"
                        className={`${styles.typeBtn} ${
                          formData.type === type.value ? styles.active : ''
                        }`}
                        onClick={() => setFormData({ ...formData, type: type.value })}
                      >
                        <span className={styles.typeEmoji}>{type.emoji}</span>
                        <span>{type.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Message */}
                <div className={styles.formGroup}>
                  <label>Your feedback *</label>
                  <textarea
                    className={styles.textarea}
                    placeholder="Tell us what you think... (minimum 10 characters)"
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    rows={4}
                    maxLength={2000}
                  />
                  <small className={styles.charCount}>
                    {formData.message.length}/2000 characters
                  </small>
                </div>

                {/* Email (if not logged in) */}
                {!user && (
                  <div className={styles.formGroup}>
                    <label>Email (optional, for follow-up)</label>
                    <input
                      type="email"
                      className={styles.input}
                      placeholder="your@email.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  className={styles.submitBtn}
                  disabled={submitting || formData.message.trim().length < 10}
                >
                  {submitting ? (
                    <>
                      <span className="spinner"></span>
                      Sending...
                    </>
                  ) : (
                    <>
                      <FiSend size={18} />
                      Submit Feedback
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackWidget;
