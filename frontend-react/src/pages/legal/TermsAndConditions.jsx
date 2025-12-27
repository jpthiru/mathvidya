/**
 * Terms and Conditions Page
 * Required for payment gateway compliance in India
 */

import styles from './Legal.module.css';

const TermsAndConditions = () => {
  return (
    <div className={styles.legalPage}>
      <div className={styles.container}>
        <h1>Terms and Conditions</h1>
        <p className={styles.lastUpdated}>Last Updated: December 2024</p>

        <section className={styles.section}>
          <h2>1. Introduction</h2>
          <p>
            Welcome to MathVidya ("we," "our," or "us"). These Terms and Conditions govern your
            access to and use of the MathVidya website (www.mathvidya.com) and our online
            mathematics practice platform for CBSE students.
          </p>
          <p>
            By accessing or using our services, you agree to be bound by these Terms and Conditions.
            If you do not agree to these terms, please do not use our services.
          </p>
        </section>

        <section className={styles.section}>
          <h2>2. Definitions</h2>
          <ul>
            <li><strong>"Platform"</strong> refers to the MathVidya website and all related services.</li>
            <li><strong>"User"</strong> refers to any person who accesses or uses the Platform, including Students, Parents, and Teachers.</li>
            <li><strong>"Student"</strong> refers to a registered user who takes practice exams on the Platform.</li>
            <li><strong>"Parent/Guardian"</strong> refers to the parent or legal guardian of a Student.</li>
            <li><strong>"Subscription"</strong> refers to a paid plan that grants access to specific features and services.</li>
            <li><strong>"Content"</strong> refers to all questions, answers, explanations, and educational materials on the Platform.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>3. Eligibility</h2>
          <p>
            Our services are designed for CBSE students of Classes X and XII in India. By registering:
          </p>
          <ul>
            <li>Students under 18 years of age must have consent from a parent or legal guardian.</li>
            <li>Parent/Guardian registration is mandatory for all student accounts.</li>
            <li>You confirm that all information provided during registration is accurate and complete.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>4. Account Registration</h2>
          <p>To use our services, you must:</p>
          <ul>
            <li>Create an account with valid email address and phone number.</li>
            <li>Provide accurate personal information including name, class, and contact details.</li>
            <li>Keep your login credentials confidential and secure.</li>
            <li>Notify us immediately of any unauthorized use of your account.</li>
          </ul>
          <p>
            You are responsible for all activities that occur under your account. We reserve the right
            to suspend or terminate accounts that violate these terms.
          </p>
        </section>

        <section className={styles.section}>
          <h2>5. Services Provided</h2>
          <p>MathVidya provides:</p>
          <ul>
            <li>Online mathematics practice exams aligned with CBSE board examination patterns.</li>
            <li>Multiple Choice Questions (MCQ) with automated evaluation.</li>
            <li>Very Short Answer (VSA) and Short Answer (SA) questions with expert teacher evaluation.</li>
            <li>Personalized performance analytics and board exam score predictions.</li>
            <li>Unit-wise and full board examination practice modes.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>6. Subscription Plans and Payments</h2>
          <p>
            We offer various subscription plans with different features. By purchasing a subscription:
          </p>
          <ul>
            <li>You agree to pay the specified fees for your chosen plan.</li>
            <li>Payments are processed securely through our payment gateway partner (Razorpay).</li>
            <li>Subscription fees are non-refundable except as specified in our Refund Policy.</li>
            <li>We reserve the right to modify pricing with prior notice to users.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>7. Evaluation and SLA</h2>
          <p>For teacher-evaluated questions (VSA/SA):</p>
          <ul>
            <li><strong>Centum Plan:</strong> Same working day evaluation.</li>
            <li><strong>Other Plans:</strong> Within 48 working hours.</li>
            <li>Working days exclude Sundays and declared public holidays.</li>
          </ul>
          <p>
            While we strive to meet these timelines, occasional delays may occur due to unforeseen
            circumstances. Such delays do not constitute grounds for refund.
          </p>
        </section>

        <section className={styles.section}>
          <h2>8. User Conduct</h2>
          <p>You agree NOT to:</p>
          <ul>
            <li>Share your account credentials with others.</li>
            <li>Attempt to access other users' accounts or data.</li>
            <li>Copy, distribute, or reproduce our content without permission.</li>
            <li>Use automated tools to access or scrape our platform.</li>
            <li>Upload inappropriate, offensive, or illegal content.</li>
            <li>Interfere with the proper functioning of the platform.</li>
            <li>Engage in any activity that violates applicable laws.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>9. Intellectual Property</h2>
          <p>
            All content on the Platform, including questions, solutions, explanations, graphics,
            logos, and software, is the property of MathVidya or its licensors and is protected
            by Indian copyright laws.
          </p>
          <p>
            You may not reproduce, distribute, modify, or create derivative works from our content
            without our express written permission.
          </p>
        </section>

        <section className={styles.section}>
          <h2>10. Privacy</h2>
          <p>
            Your privacy is important to us. Please review our <a href="/privacy-policy">Privacy Policy</a> to
            understand how we collect, use, and protect your personal information.
          </p>
        </section>

        <section className={styles.section}>
          <h2>11. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law:
          </p>
          <ul>
            <li>MathVidya is not liable for any indirect, incidental, or consequential damages.</li>
            <li>Our total liability shall not exceed the amount paid by you in the last 12 months.</li>
            <li>We do not guarantee specific exam results or board examination scores.</li>
            <li>We are not responsible for technical issues beyond our control.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>12. Disclaimer</h2>
          <p>
            Our services are provided "as is" without warranties of any kind. While we strive to
            provide accurate and helpful content:
          </p>
          <ul>
            <li>We do not guarantee that our content is error-free.</li>
            <li>Score predictions are estimates based on historical data and are not guaranteed.</li>
            <li>Our platform supplements, but does not replace, classroom education.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>13. Termination</h2>
          <p>
            We may suspend or terminate your account if you violate these terms. Upon termination:
          </p>
          <ul>
            <li>Your access to the platform will be revoked.</li>
            <li>No refund will be provided for unused subscription period.</li>
            <li>We may retain your data as required by law.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>14. Changes to Terms</h2>
          <p>
            We may modify these Terms and Conditions at any time. Changes will be effective upon
            posting on this page with an updated "Last Updated" date. Continued use of our services
            after changes constitutes acceptance of the modified terms.
          </p>
        </section>

        <section className={styles.section}>
          <h2>15. Governing Law and Jurisdiction</h2>
          <p>
            These Terms are governed by the laws of India. Any disputes shall be subject to the
            exclusive jurisdiction of the courts in Chennai, Tamil Nadu, India.
          </p>
        </section>

        <section className={styles.section}>
          <h2>16. Contact Us</h2>
          <p>
            If you have any questions about these Terms and Conditions, please contact us:
          </p>
          <div className={styles.contactInfo}>
            <p><strong>MathVidya</strong></p>
            <p>Email: support@mathvidya.com</p>
            <p>Phone: +91 98400 12345</p>
            <p>Address: Chennai, Tamil Nadu, India</p>
          </div>
        </section>

        <div className={styles.footer}>
          <a href="/login" className={styles.backLink}>&larr; Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default TermsAndConditions;
