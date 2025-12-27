/**
 * Pricing Page
 * Shows subscription plans with clear pricing details
 * Required for payment gateway compliance in India
 */

import { FiCheck, FiX } from 'react-icons/fi';
import styles from './Legal.module.css';

const Pricing = () => {
  const plans = [
    {
      name: 'Basic',
      price: '₹499',
      period: '/month',
      annualPrice: '₹4,999/year',
      annualSavings: 'Save ₹989',
      description: 'Perfect for getting started with board exam practice',
      features: [
        { text: '5 exams per month', included: true },
        { text: 'Full Board Exam practice', included: true },
        { text: 'MCQ with instant results', included: true },
        { text: 'VSA/SA with teacher evaluation', included: true },
        { text: '48-hour evaluation SLA', included: true },
        { text: '1 hour teacher interaction/month', included: true },
        { text: 'Performance analytics', included: true },
        { text: 'Unit-wise practice', included: false },
        { text: 'Leaderboard access', included: false },
        { text: 'Same-day evaluation', included: false },
      ],
      popular: false,
      buttonText: 'Start Basic',
    },
    {
      name: 'Premium MCQ',
      price: '₹699',
      period: '/month',
      annualPrice: '₹6,999/year',
      annualSavings: 'Save ₹1,389',
      description: 'Ideal for students focusing on MCQ mastery',
      features: [
        { text: '15 exams per month', included: true },
        { text: 'MCQ practice only', included: true },
        { text: 'Instant automated results', included: true },
        { text: 'Detailed explanations', included: true },
        { text: 'Performance analytics', included: true },
        { text: 'Unit-wise MCQ practice', included: true },
        { text: 'Topic-wise breakdown', included: true },
        { text: 'VSA/SA questions', included: false },
        { text: 'Teacher evaluation', included: false },
        { text: 'Leaderboard access', included: false },
      ],
      popular: false,
      buttonText: 'Start MCQ Plan',
    },
    {
      name: 'Premium',
      price: '₹1,499',
      period: '/month',
      annualPrice: null,
      description: 'Complete preparation with all practice modes',
      features: [
        { text: '50 exams per month', included: true },
        { text: 'Full Board Exam practice', included: true },
        { text: 'Unit-wise practice', included: true },
        { text: 'MCQ, VSA, SA questions', included: true },
        { text: '48-hour evaluation SLA', included: true },
        { text: '1 hour coaching/month', included: true },
        { text: 'Advanced analytics', included: true },
        { text: 'Board score prediction', included: true },
        { text: 'Leaderboard access', included: true },
        { text: 'Same-day evaluation', included: false },
      ],
      popular: true,
      buttonText: 'Start Premium',
    },
    {
      name: 'Centum',
      price: '₹2,499',
      period: '/month',
      annualPrice: '₹24,999/year',
      annualSavings: 'Save ₹4,989',
      description: 'For serious students aiming for 100% marks',
      features: [
        { text: '50 exams per month', included: true },
        { text: 'Full Board + Unit-wise practice', included: true },
        { text: 'All question types', included: true },
        { text: 'Same-day evaluation', included: true },
        { text: 'Direct teacher access', included: true },
        { text: 'Priority support', included: true },
        { text: 'Advanced analytics', included: true },
        { text: 'Board score prediction', included: true },
        { text: 'Leaderboard access', included: true },
        { text: 'Personalized study plan', included: true },
      ],
      popular: false,
      buttonText: 'Start Centum',
    },
  ];

  return (
    <div className={styles.legalPage}>
      <div className={styles.pricingContainer}>
        <div className={styles.pricingHeader}>
          <h1>Choose Your Plan</h1>
          <p>
            Flexible pricing for CBSE Class X and XII mathematics practice.
            All plans include access to our expert-curated question bank.
          </p>
        </div>

        <div className={styles.pricingGrid}>
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`${styles.pricingCard} ${plan.popular ? styles.popular : ''}`}
            >
              {plan.popular && <div className={styles.popularBadge}>Most Popular</div>}

              <h2>{plan.name}</h2>
              <p className={styles.planDescription}>{plan.description}</p>

              <div className={styles.priceSection}>
                <span className={styles.price}>{plan.price}</span>
                <span className={styles.period}>{plan.period}</span>
              </div>

              {plan.annualPrice && (
                <div className={styles.annualPrice}>
                  <span>Annual: {plan.annualPrice}</span>
                  {plan.annualSavings && (
                    <span className={styles.savings}>{plan.annualSavings}</span>
                  )}
                </div>
              )}

              <ul className={styles.featureList}>
                {plan.features.map((feature, index) => (
                  <li key={index} className={feature.included ? styles.included : styles.excluded}>
                    {feature.included ? (
                      <FiCheck className={styles.checkIcon} />
                    ) : (
                      <FiX className={styles.xIcon} />
                    )}
                    <span>{feature.text}</span>
                  </li>
                ))}
              </ul>

              <button className={`${styles.planButton} ${plan.popular ? styles.primaryButton : ''}`}>
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>

        {/* Additional Information */}
        <section className={styles.pricingInfo}>
          <h2>Important Information</h2>

          <div className={styles.infoGrid}>
            <div className={styles.infoCard}>
              <h3>What's included in all plans?</h3>
              <ul>
                <li>Access to CBSE-aligned question bank</li>
                <li>LaTeX-rendered mathematical equations</li>
                <li>Mobile-friendly platform</li>
                <li>Secure payment via Razorpay</li>
                <li>Email support</li>
              </ul>
            </div>

            <div className={styles.infoCard}>
              <h3>Payment Methods</h3>
              <ul>
                <li>Credit/Debit Cards (Visa, MasterCard, RuPay)</li>
                <li>Net Banking (all major banks)</li>
                <li>UPI (Google Pay, PhonePe, Paytm)</li>
                <li>Wallets (Paytm, Mobikwik)</li>
              </ul>
            </div>

            <div className={styles.infoCard}>
              <h3>Billing & Refunds</h3>
              <ul>
                <li>Auto-renewal can be turned off anytime</li>
                <li>7-day refund policy for new subscribers</li>
                <li>No hidden charges</li>
                <li>GST included in all prices</li>
              </ul>
            </div>

            <div className={styles.infoCard}>
              <h3>Need Help Choosing?</h3>
              <p>
                Not sure which plan is right for you? Contact our team and we'll
                help you find the perfect fit for your learning goals.
              </p>
              <p>
                <strong>Email:</strong> support@mathvidya.com<br />
                <strong>Phone:</strong> +91 98400 12345
              </p>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className={styles.pricingFaq}>
          <h2>Frequently Asked Questions</h2>

          <div className={styles.faqGrid}>
            <div className={styles.faqItem}>
              <h3>Can I switch plans later?</h3>
              <p>
                Yes! You can upgrade anytime and we'll prorate the difference.
                Downgrades take effect at the next billing cycle.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>What happens when my exam limit is reached?</h3>
              <p>
                You can purchase additional exam packs or upgrade your plan.
                Unused exams don't carry over to the next month.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>Is there a free trial?</h3>
              <p>
                We offer a 7-day money-back guarantee. Try any plan risk-free
                and get a full refund if you're not satisfied.
              </p>
            </div>
            <div className={styles.faqItem}>
              <h3>Can parents track progress?</h3>
              <p>
                Yes! Parent accounts have full visibility into their child's
                exam history, scores, and performance analytics.
              </p>
            </div>
          </div>
        </section>

        <div className={styles.footer}>
          <p className={styles.legalLinks}>
            By subscribing, you agree to our{' '}
            <a href="/terms-and-conditions">Terms and Conditions</a>,{' '}
            <a href="/privacy-policy">Privacy Policy</a>, and{' '}
            <a href="/refund-policy">Refund Policy</a>.
          </p>
          <a href="/login" className={styles.backLink}>&larr; Back to Login</a>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
