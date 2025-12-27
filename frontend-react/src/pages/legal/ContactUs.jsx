/**
 * Contact Us Page
 * Required for payment gateway compliance in India
 */

import { useState } from 'react';
import { FiMail, FiPhone, FiMapPin, FiClock, FiSend } from 'react-icons/fi';
import styles from './Legal.module.css';

const ContactUs = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // In production, this would send to backend
    console.log('Contact form submitted:', formData);
    setSubmitted(true);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className={styles.legalPage}>
      <div className={styles.container}>
        <h1>Contact Us</h1>
        <p className={styles.subtitle}>
          We're here to help! Reach out to us with any questions, feedback, or support requests.
        </p>

        <div className={styles.contactGrid}>
          {/* Contact Information */}
          <div className={styles.contactInfoSection}>
            <h2>Get in Touch</h2>

            <div className={styles.contactCard}>
              <div className={styles.contactIcon}>
                <FiMail />
              </div>
              <div>
                <h3>Email</h3>
                <p><a href="mailto:support@mathvidya.com">support@mathvidya.com</a></p>
                <p className={styles.contactNote}>General inquiries and support</p>
              </div>
            </div>

            <div className={styles.contactCard}>
              <div className={styles.contactIcon}>
                <FiPhone />
              </div>
              <div>
                <h3>Phone</h3>
                <p><a href="tel:+919840012345">+91 98400 12345</a></p>
                <p className={styles.contactNote}>Mon - Sat, 9:00 AM - 6:00 PM IST</p>
              </div>
            </div>

            <div className={styles.contactCard}>
              <div className={styles.contactIcon}>
                <FiMapPin />
              </div>
              <div>
                <h3>Address</h3>
                <p>
                  MathVidya Education Pvt. Ltd.<br />
                  123, Anna Salai, Teynampet<br />
                  Chennai - 600018<br />
                  Tamil Nadu, India
                </p>
              </div>
            </div>

            <div className={styles.contactCard}>
              <div className={styles.contactIcon}>
                <FiClock />
              </div>
              <div>
                <h3>Business Hours</h3>
                <p>Monday - Saturday: 9:00 AM - 6:00 PM IST</p>
                <p>Sunday: Closed</p>
                <p className={styles.contactNote}>Response within 24 hours on business days</p>
              </div>
            </div>

            <div className={styles.departmentEmails}>
              <h3>Department Emails</h3>
              <ul>
                <li><strong>General Support:</strong> <a href="mailto:support@mathvidya.com">support@mathvidya.com</a></li>
                <li><strong>Billing & Refunds:</strong> <a href="mailto:billing@mathvidya.com">billing@mathvidya.com</a></li>
                <li><strong>Privacy Concerns:</strong> <a href="mailto:privacy@mathvidya.com">privacy@mathvidya.com</a></li>
                <li><strong>Grievances:</strong> <a href="mailto:grievance@mathvidya.com">grievance@mathvidya.com</a></li>
                <li><strong>Partnerships:</strong> <a href="mailto:partners@mathvidya.com">partners@mathvidya.com</a></li>
              </ul>
            </div>
          </div>

          {/* Contact Form */}
          <div className={styles.contactFormSection}>
            <h2>Send us a Message</h2>

            {submitted ? (
              <div className={styles.successMessage}>
                <div className={styles.successIcon}>✓</div>
                <h3>Thank you for contacting us!</h3>
                <p>
                  We've received your message and will get back to you within 24 hours
                  on business days.
                </p>
                <button
                  className={styles.resetButton}
                  onClick={() => {
                    setSubmitted(false);
                    setFormData({ name: '', email: '', phone: '', subject: '', message: '' });
                  }}
                >
                  Send Another Message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className={styles.contactForm}>
                <div className={styles.formRow}>
                  <div className="form-group">
                    <label className="form-label">Your Name *</label>
                    <input
                      type="text"
                      name="name"
                      className="form-input"
                      value={formData.name}
                      onChange={handleChange}
                      required
                      placeholder="Enter your full name"
                    />
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className="form-group">
                    <label className="form-label">Email Address *</label>
                    <input
                      type="email"
                      name="email"
                      className="form-input"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      placeholder="your.email@example.com"
                    />
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className="form-group">
                    <label className="form-label">Phone Number</label>
                    <input
                      type="tel"
                      name="phone"
                      className="form-input"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+91 98400 12345"
                    />
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className="form-group">
                    <label className="form-label">Subject *</label>
                    <select
                      name="subject"
                      className="form-select"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Select a topic</option>
                      <option value="general">General Inquiry</option>
                      <option value="technical">Technical Support</option>
                      <option value="billing">Billing & Payments</option>
                      <option value="refund">Refund Request</option>
                      <option value="feedback">Feedback & Suggestions</option>
                      <option value="complaint">Complaint</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className="form-group">
                    <label className="form-label">Message *</label>
                    <textarea
                      name="message"
                      className="form-textarea"
                      rows={5}
                      value={formData.message}
                      onChange={handleChange}
                      required
                      placeholder="Please describe your inquiry in detail..."
                    />
                  </div>
                </div>

                <button type="submit" className={styles.submitButton}>
                  <FiSend /> Send Message
                </button>
              </form>
            )}
          </div>
        </div>

        {/* FAQ Section */}
        <section className={styles.faqSection}>
          <h2>Frequently Asked Questions</h2>
          <div className={styles.faqGrid}>
            <div className={styles.faqItem}>
              <h3>How do I reset my password?</h3>
              <p>
                Click on "Forgot Password" on the login page and enter your registered email.
                You'll receive a password reset link within a few minutes.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>How long does evaluation take?</h3>
              <p>
                For Centum plan: Same working day. For other plans: Within 48 working hours.
                Working days exclude Sundays and public holidays.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>Can I upgrade my subscription?</h3>
              <p>
                Yes! You can upgrade anytime from your account settings. You'll be charged
                the prorated difference for the remaining period.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>How do I request a refund?</h3>
              <p>
                Email us at refunds@mathvidya.com within 7 days of purchase with your
                order details. See our Refund Policy for full terms.
              </p>
            </div>
          </div>
        </section>

        <div className={styles.footer}>
          <a href="/login" className={styles.backLink}>&larr; Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default ContactUs;
