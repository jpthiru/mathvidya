/**
 * Refund and Cancellation Policy Page
 * Required for payment gateway compliance in India
 */

import styles from './Legal.module.css';

const RefundPolicy = () => {
  return (
    <div className={styles.legalPage}>
      <div className={styles.container}>
        <h1>Refund and Cancellation Policy</h1>
        <p className={styles.lastUpdated}>Last Updated: December 2024</p>

        <section className={styles.section}>
          <h2>1. Overview</h2>
          <p>
            This Refund and Cancellation Policy outlines the terms under which MathVidya
            processes refunds and cancellations for subscription plans purchased on our platform.
          </p>
          <p>
            We strive to ensure customer satisfaction while maintaining fair policies for our
            educational services.
          </p>
        </section>

        <section className={styles.section}>
          <h2>2. Subscription Plans</h2>
          <p>MathVidya offers the following subscription plans:</p>
          <table className={styles.pricingTable}>
            <thead>
              <tr>
                <th>Plan</th>
                <th>Billing Cycle</th>
                <th>Features</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Basic</strong></td>
                <td>Monthly / Annual</td>
                <td>5 exams/month, Board Exam practice, 48-hour evaluation</td>
              </tr>
              <tr>
                <td><strong>Premium MCQ</strong></td>
                <td>Monthly / Annual</td>
                <td>15 exams/month, MCQ only, Instant results</td>
              </tr>
              <tr>
                <td><strong>Premium</strong></td>
                <td>Monthly</td>
                <td>50 exams/month, Full practice modes, 48-hour evaluation, Leaderboard access</td>
              </tr>
              <tr>
                <td><strong>Centum</strong></td>
                <td>Annual</td>
                <td>50 exams/month, Same-day evaluation, Direct teacher access, Leaderboard access</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className={styles.section}>
          <h2>3. Cancellation Policy</h2>

          <h3>3.1 Monthly Subscriptions</h3>
          <ul>
            <li>You may cancel your monthly subscription at any time.</li>
            <li>Cancellation takes effect at the end of the current billing period.</li>
            <li>You will continue to have access until the end of the paid period.</li>
            <li>No partial refunds for unused days within the current month.</li>
          </ul>

          <h3>3.2 Annual Subscriptions</h3>
          <ul>
            <li>Annual subscriptions can be cancelled within 7 days of purchase for a full refund (subject to Section 4).</li>
            <li>After 7 days, no refund is available for annual subscriptions.</li>
            <li>Access continues until the end of the annual period.</li>
          </ul>

          <h3>3.3 How to Cancel</h3>
          <p>To cancel your subscription:</p>
          <ol>
            <li>Log in to your MathVidya account</li>
            <li>Go to Settings &gt; Subscription</li>
            <li>Click "Cancel Subscription"</li>
            <li>Confirm your cancellation</li>
          </ol>
          <p>
            Alternatively, email us at support@mathvidya.com with your registered email address.
          </p>
        </section>

        <section className={styles.section}>
          <h2>4. Refund Policy</h2>

          <h3>4.1 Eligible Refunds</h3>
          <p>Refunds are processed in the following cases:</p>
          <ul>
            <li>
              <strong>7-Day Cooling Period:</strong> Full refund if you cancel within 7 days of
              purchase AND have not used more than 2 exams.
            </li>
            <li>
              <strong>Technical Issues:</strong> If our platform has significant technical problems
              that prevent you from using the service for more than 7 consecutive days.
            </li>
            <li>
              <strong>Duplicate Payment:</strong> Full refund if you were charged multiple times
              for the same subscription.
            </li>
            <li>
              <strong>Failed Payment Recovery:</strong> If payment was deducted but subscription
              was not activated.
            </li>
          </ul>

          <h3>4.2 Non-Refundable Cases</h3>
          <p>Refunds are NOT available in the following cases:</p>
          <ul>
            <li>After the 7-day cooling period has passed</li>
            <li>If more than 2 exams have been attempted</li>
            <li>For monthly subscriptions after partial use</li>
            <li>If the account has been suspended due to policy violations</li>
            <li>If the user simply changed their mind after using the service</li>
            <li>For promotional or discounted subscriptions (unless stated otherwise)</li>
          </ul>

          <h3>4.3 Partial Refunds</h3>
          <p>
            Partial refunds may be considered on a case-by-case basis for:
          </p>
          <ul>
            <li>Medical emergencies (with valid documentation)</li>
            <li>Extended platform outages caused by us</li>
            <li>Other exceptional circumstances at our discretion</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>5. Refund Process</h2>

          <h3>5.1 How to Request a Refund</h3>
          <ol>
            <li>
              Email us at <strong>refunds@mathvidya.com</strong> with:
              <ul>
                <li>Your registered email address</li>
                <li>Order ID / Transaction ID</li>
                <li>Reason for refund request</li>
                <li>Any supporting documentation (if applicable)</li>
              </ul>
            </li>
            <li>Our team will review your request within 3 business days.</li>
            <li>You will receive an email with the decision and next steps.</li>
          </ol>

          <h3>5.2 Refund Timeline</h3>
          <table className={styles.timelineTable}>
            <thead>
              <tr>
                <th>Payment Method</th>
                <th>Refund Timeline</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Credit Card</td>
                <td>5-7 business days</td>
              </tr>
              <tr>
                <td>Debit Card</td>
                <td>5-7 business days</td>
              </tr>
              <tr>
                <td>Net Banking</td>
                <td>5-7 business days</td>
              </tr>
              <tr>
                <td>UPI</td>
                <td>3-5 business days</td>
              </tr>
              <tr>
                <td>Wallet</td>
                <td>1-3 business days</td>
              </tr>
            </tbody>
          </table>
          <p>
            <em>Note: Actual timeline may vary depending on your bank or payment provider.</em>
          </p>

          <h3>5.3 Refund Amount</h3>
          <p>
            Refunds are processed for the amount paid, minus any applicable:
          </p>
          <ul>
            <li>Payment gateway fees (typically 2-3%)</li>
            <li>Taxes already remitted to the government</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>6. Plan Upgrades and Downgrades</h2>

          <h3>6.1 Upgrades</h3>
          <ul>
            <li>You can upgrade your plan at any time.</li>
            <li>You will be charged the prorated difference for the remaining period.</li>
            <li>New features are available immediately upon upgrade.</li>
          </ul>

          <h3>6.2 Downgrades</h3>
          <ul>
            <li>Downgrades take effect at the next billing cycle.</li>
            <li>No refund is provided for the current period.</li>
            <li>Unused exam quota from the current month does not carry forward.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>7. Free Trial</h2>
          <p>
            If we offer a free trial period:
          </p>
          <ul>
            <li>No payment is required during the trial.</li>
            <li>You will be notified before the trial ends.</li>
            <li>You must cancel before the trial ends to avoid being charged.</li>
            <li>Charges after a trial period are non-refundable.</li>
          </ul>
        </section>

        <section className={styles.section}>
          <h2>8. Disputes</h2>
          <p>
            If you believe a charge is incorrect or if you have a dispute:
          </p>
          <ol>
            <li>Contact us first at support@mathvidya.com.</li>
            <li>We will investigate and respond within 7 business days.</li>
            <li>If unresolved, you may escalate to your payment provider.</li>
          </ol>
          <p>
            Please do not initiate a chargeback without contacting us first, as this may result
            in immediate account suspension.
          </p>
        </section>

        <section className={styles.section}>
          <h2>9. Changes to This Policy</h2>
          <p>
            We may update this Refund and Cancellation Policy from time to time. Changes will be
            posted on this page with an updated "Last Updated" date.
          </p>
          <p>
            Existing subscriptions will be governed by the policy in effect at the time of purchase.
          </p>
        </section>

        <section className={styles.section}>
          <h2>10. Contact Us</h2>
          <p>
            For refund requests or questions about this policy:
          </p>
          <div className={styles.contactInfo}>
            <p><strong>MathVidya Support</strong></p>
            <p>Email: refunds@mathvidya.com</p>
            <p>Phone: +91 98400 12345</p>
            <p>Hours: Monday - Saturday, 9:00 AM - 6:00 PM IST</p>
          </div>
        </section>

        <div className={styles.footer}>
          <a href="/login" className={styles.backLink}>&larr; Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default RefundPolicy;
