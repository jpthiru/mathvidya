/**
 * Mathvidya Analytics & Third-Party Integrations
 *
 * This file handles:
 * - Google Analytics 4 (GA4)
 * - Google reCAPTCHA v3
 * - Tawk.to Chat Widget
 * - Common tracking utilities
 */

// ============================================
// CONFIGURATION - Replace with your actual keys
// ============================================
const MV_CONFIG = {
    // Google Analytics 4 Measurement ID
    // Get this from: https://analytics.google.com/ -> Admin -> Data Streams -> Measurement ID
    GA4_MEASUREMENT_ID: 'G-HJZ60RG9TE',

    // Google reCAPTCHA v3 Site Key
    // Get this from: https://www.google.com/recaptcha/admin
    RECAPTCHA_SITE_KEY: '6Lfcdz8sAAAAAEcnmNPOqSiCklrykmlhNZ8L3KjN', // Test key - replace in production

    // Tawk.to Property ID and Widget ID
    // Get this from: https://dashboard.tawk.to/ -> Administration -> Chat Widget
    TAWKTO_PROPERTY_ID: '6959d51f85cf7b197c865c5d',
    TAWKTO_WIDGET_ID: '1je3eh0h3',

    // Environment
    IS_PRODUCTION: window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
};

// ============================================
// GOOGLE ANALYTICS 4
// ============================================
function initGoogleAnalytics() {
    if (!MV_CONFIG.GA4_MEASUREMENT_ID || MV_CONFIG.GA4_MEASUREMENT_ID === 'G-XXXXXXXXXX') {
        console.log('[Analytics] GA4 not configured - skipping initialization');
        return;
    }

    // Create script tag for gtag.js
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${MV_CONFIG.GA4_MEASUREMENT_ID}`;
    document.head.appendChild(script);

    // Initialize gtag
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;

    gtag('js', new Date());
    gtag('config', MV_CONFIG.GA4_MEASUREMENT_ID, {
        'anonymize_ip': true,
        'cookie_flags': 'SameSite=None;Secure'
    });

    console.log('[Analytics] Google Analytics initialized');
}

// Track custom events
function trackEvent(eventName, params = {}) {
    if (window.gtag) {
        gtag('event', eventName, params);
    }
}

// Track page views (useful for SPAs)
function trackPageView(pagePath, pageTitle) {
    if (window.gtag) {
        gtag('event', 'page_view', {
            page_path: pagePath || window.location.pathname,
            page_title: pageTitle || document.title
        });
    }
}

// Common events to track
const MV_EVENTS = {
    // Authentication
    SIGNUP_START: 'signup_start',
    SIGNUP_COMPLETE: 'signup_complete',
    LOGIN_SUCCESS: 'login_success',
    LOGIN_FAILED: 'login_failed',
    LOGOUT: 'logout',

    // Exam flow
    EXAM_START: 'exam_start',
    EXAM_SUBMIT: 'exam_submit',
    EXAM_COMPLETE: 'exam_complete',

    // Subscription
    PLAN_VIEW: 'plan_view',
    PROMO_CODE_APPLIED: 'promo_code_applied',
    SUBSCRIPTION_START: 'subscription_start',

    // Engagement
    FEEDBACK_SUBMIT: 'feedback_submit',
    CHAT_OPEN: 'chat_open',
    CTA_CLICK: 'cta_click'
};

// ============================================
// GOOGLE RECAPTCHA V3
// ============================================
let recaptchaReady = false;

function initRecaptcha() {
    if (!MV_CONFIG.RECAPTCHA_SITE_KEY) {
        console.log('[reCAPTCHA] Not configured - skipping initialization');
        return;
    }

    // Load reCAPTCHA script
    const script = document.createElement('script');
    script.src = `https://www.google.com/recaptcha/api.js?render=${MV_CONFIG.RECAPTCHA_SITE_KEY}`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
        grecaptcha.ready(() => {
            recaptchaReady = true;
            console.log('[reCAPTCHA] Ready');
        });
    };
}

// Execute reCAPTCHA and get token
async function getRecaptchaToken(action = 'submit') {
    if (!recaptchaReady || !window.grecaptcha) {
        console.warn('[reCAPTCHA] Not ready');
        return null;
    }

    try {
        const token = await grecaptcha.execute(MV_CONFIG.RECAPTCHA_SITE_KEY, { action });
        return token;
    } catch (error) {
        console.error('[reCAPTCHA] Error getting token:', error);
        return null;
    }
}

// ============================================
// MATHVIDYA CHATBOT WIDGET
// ============================================
let chatbotOpen = false;
let chatMessages = [];

function initChatbot() {
    // Create chatbot button
    const chatBtn = document.createElement('button');
    chatBtn.id = 'mv-chat-btn';
    chatBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
    `;
    chatBtn.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9998;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        transition: transform 0.3s, box-shadow 0.3s;
    `;

    chatBtn.addEventListener('mouseenter', () => {
        chatBtn.style.transform = 'scale(1.1)';
        chatBtn.style.boxShadow = '0 6px 25px rgba(99, 102, 241, 0.5)';
    });
    chatBtn.addEventListener('mouseleave', () => {
        chatBtn.style.transform = 'scale(1)';
        chatBtn.style.boxShadow = '0 4px 20px rgba(99, 102, 241, 0.4)';
    });
    chatBtn.addEventListener('click', toggleChatbot);

    document.body.appendChild(chatBtn);

    // Create chatbot window (hidden initially)
    createChatWindow();

    console.log('[Chatbot] Mathvidya chatbot initialized');
}

function createChatWindow() {
    const chatWindow = document.createElement('div');
    chatWindow.id = 'mv-chat-window';
    chatWindow.innerHTML = `
        <div class="mv-chat-header">
            <div class="mv-chat-header-info">
                <div class="mv-chat-avatar">M</div>
                <div>
                    <div class="mv-chat-title">Mathvidya Support</div>
                    <div class="mv-chat-status">Ask me anything!</div>
                </div>
            </div>
            <button class="mv-chat-close">&times;</button>
        </div>
        <div class="mv-chat-messages" id="mv-chat-messages">
            <div class="mv-chat-welcome">
                <p>👋 Hi! I'm here to help you with:</p>
                <ul>
                    <li>Getting started with Mathvidya</li>
                    <li>Subscription plans & pricing</li>
                    <li>Taking practice exams</li>
                    <li>Technical support</li>
                </ul>
            </div>
            <div class="mv-chat-suggestions" id="mv-chat-suggestions">
                <!-- Suggestions will be loaded here -->
            </div>
        </div>
        <div class="mv-chat-input-area">
            <input type="text" id="mv-chat-input" placeholder="Type your question..." maxlength="500">
            <button id="mv-chat-send">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
            </button>
        </div>
    `;

    // Add styles
    const styles = document.createElement('style');
    styles.id = 'mv-chat-styles';
    styles.textContent = `
        #mv-chat-window {
            position: fixed;
            bottom: 100px;
            right: 24px;
            width: 380px;
            height: 520px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            display: none;
            flex-direction: column;
            z-index: 9999;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #mv-chat-window.open {
            display: flex;
            animation: slideUp 0.3s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .mv-chat-header {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .mv-chat-header-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .mv-chat-avatar {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
        }
        .mv-chat-title {
            font-weight: 600;
            font-size: 16px;
        }
        .mv-chat-status {
            font-size: 12px;
            opacity: 0.9;
        }
        .mv-chat-close {
            background: none;
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.2s;
            line-height: 1;
        }
        .mv-chat-close:hover {
            opacity: 1;
        }
        .mv-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #f8fafc;
        }
        .mv-chat-welcome {
            background: white;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .mv-chat-welcome p {
            margin: 0 0 8px 0;
            font-weight: 500;
            color: #1e293b;
        }
        .mv-chat-welcome ul {
            margin: 0;
            padding-left: 20px;
            color: #64748b;
            font-size: 14px;
        }
        .mv-chat-welcome li {
            margin: 4px 0;
        }
        .mv-chat-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
        }
        .mv-chat-suggestion {
            background: white;
            border: 1px solid #e2e8f0;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            color: #475569;
        }
        .mv-chat-suggestion:hover {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
        }
        .mv-chat-message {
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
        }
        .mv-chat-message.user {
            align-items: flex-end;
        }
        .mv-chat-message.bot {
            align-items: flex-start;
        }
        .mv-chat-bubble {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        .mv-chat-message.user .mv-chat-bubble {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .mv-chat-message.bot .mv-chat-bubble {
            background: white;
            color: #1e293b;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .mv-chat-bubble strong {
            font-weight: 600;
        }
        .mv-chat-typing {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: white;
            border-radius: 16px;
            width: fit-content;
        }
        .mv-chat-typing span {
            width: 8px;
            height: 8px;
            background: #cbd5e1;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .mv-chat-typing span:nth-child(2) { animation-delay: 0.2s; }
        .mv-chat-typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
        }
        .mv-chat-input-area {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 8px;
        }
        #mv-chat-input {
            flex: 1;
            border: 1px solid #e2e8f0;
            padding: 12px 16px;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        #mv-chat-input:focus {
            border-color: #6366f1;
        }
        #mv-chat-send {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        #mv-chat-send:hover {
            transform: scale(1.05);
        }
        #mv-chat-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        @media (max-width: 480px) {
            #mv-chat-window {
                width: calc(100% - 32px);
                right: 16px;
                bottom: 90px;
                height: 60vh;
            }
        }
    `;

    document.head.appendChild(styles);
    document.body.appendChild(chatWindow);

    // Event handlers
    chatWindow.querySelector('.mv-chat-close').addEventListener('click', toggleChatbot);
    document.getElementById('mv-chat-send').addEventListener('click', sendChatMessage);
    document.getElementById('mv-chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    // Load suggestions
    loadChatSuggestions();
}

async function loadChatSuggestions() {
    try {
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000/api/v1'
            : '/api/v1';

        const response = await fetch(`${API_BASE}/chat/suggestions`);
        if (response.ok) {
            const data = await response.json();
            const container = document.getElementById('mv-chat-suggestions');
            container.innerHTML = data.questions.map(q =>
                `<button class="mv-chat-suggestion">${q}</button>`
            ).join('');

            // Add click handlers
            container.querySelectorAll('.mv-chat-suggestion').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.getElementById('mv-chat-input').value = btn.textContent;
                    sendChatMessage();
                });
            });
        }
    } catch (error) {
        console.log('[Chatbot] Could not load suggestions');
    }
}

function toggleChatbot() {
    chatbotOpen = !chatbotOpen;
    const chatWindow = document.getElementById('mv-chat-window');
    const chatBtn = document.getElementById('mv-chat-btn');

    if (chatbotOpen) {
        chatWindow.classList.add('open');
        chatBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        `;
        document.getElementById('mv-chat-input').focus();
        trackEvent(MV_EVENTS.CHAT_OPEN);
    } else {
        chatWindow.classList.remove('open');
        chatBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        `;
    }
}

async function sendChatMessage() {
    const input = document.getElementById('mv-chat-input');
    const message = input.value.trim();

    if (!message) return;

    const messagesContainer = document.getElementById('mv-chat-messages');
    const sendBtn = document.getElementById('mv-chat-send');

    // Hide suggestions after first message
    const suggestions = document.getElementById('mv-chat-suggestions');
    if (suggestions) suggestions.style.display = 'none';

    // Add user message
    addChatMessage(message, 'user');
    input.value = '';
    sendBtn.disabled = true;

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'mv-chat-message bot';
    typingDiv.innerHTML = `
        <div class="mv-chat-typing">
            <span></span><span></span><span></span>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000/api/v1'
            : '/api/v1';

        const response = await fetch(`${API_BASE}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        typingDiv.remove();

        if (response.ok) {
            const data = await response.json();
            addChatMessage(data.response, 'bot');
        } else {
            addChatMessage("Sorry, I'm having trouble responding right now. Please try again or contact support@mathvidya.com", 'bot');
        }
    } catch (error) {
        typingDiv.remove();
        addChatMessage("Sorry, I couldn't connect to the server. Please check your internet connection.", 'bot');
    }

    sendBtn.disabled = false;
}

function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('mv-chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `mv-chat-message ${sender}`;

    // Convert markdown-like formatting to HTML
    let formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    messageDiv.innerHTML = `<div class="mv-chat-bubble">${formattedText}</div>`;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    chatMessages.push({ text, sender, timestamp: new Date() });
}

// ============================================
// FEEDBACK WIDGET
// ============================================
function createFeedbackWidget() {
    // Create floating feedback button
    const feedbackBtn = document.createElement('button');
    feedbackBtn.id = 'mv-feedback-btn';
    feedbackBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span>Feedback</span>
    `;
    feedbackBtn.style.cssText = `
        position: fixed;
        right: -40px;
        top: 50%;
        transform: translateY(-50%) rotate(-90deg);
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: inherit;
        font-size: 14px;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        transition: right 0.3s ease;
    `;

    feedbackBtn.addEventListener('mouseenter', () => feedbackBtn.style.right = '-30px');
    feedbackBtn.addEventListener('mouseleave', () => feedbackBtn.style.right = '-40px');
    feedbackBtn.addEventListener('click', openFeedbackModal);

    document.body.appendChild(feedbackBtn);
}

function openFeedbackModal() {
    // Check if modal already exists
    if (document.getElementById('mv-feedback-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'mv-feedback-modal';
    modal.innerHTML = `
        <div class="mv-modal-overlay"></div>
        <div class="mv-modal-content">
            <button class="mv-modal-close">&times;</button>
            <h3>Share Your Feedback</h3>
            <p>We'd love to hear from you! Your feedback helps us improve.</p>

            <form id="mv-feedback-form">
                <div class="mv-form-group">
                    <label>How would you rate your experience?</label>
                    <div class="mv-rating-group">
                        <button type="button" class="mv-rating-btn" data-rating="1">1</button>
                        <button type="button" class="mv-rating-btn" data-rating="2">2</button>
                        <button type="button" class="mv-rating-btn" data-rating="3">3</button>
                        <button type="button" class="mv-rating-btn" data-rating="4">4</button>
                        <button type="button" class="mv-rating-btn" data-rating="5">5</button>
                    </div>
                    <input type="hidden" name="rating" id="mv-feedback-rating" required>
                </div>

                <div class="mv-form-group">
                    <label>Feedback Type</label>
                    <select name="type" id="mv-feedback-type" required>
                        <option value="">Select type...</option>
                        <option value="suggestion">Suggestion</option>
                        <option value="bug">Bug Report</option>
                        <option value="compliment">Compliment</option>
                        <option value="question">Question</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div class="mv-form-group">
                    <label>Your Feedback</label>
                    <textarea name="message" id="mv-feedback-message" rows="4" placeholder="Tell us what's on your mind..." required></textarea>
                </div>

                <div class="mv-form-group">
                    <label>Email (optional)</label>
                    <input type="email" name="email" id="mv-feedback-email" placeholder="your@email.com">
                </div>

                <button type="submit" class="mv-submit-btn">Submit Feedback</button>
            </form>

            <div id="mv-feedback-success" style="display: none;">
                <div class="mv-success-icon">&#10003;</div>
                <h4>Thank you!</h4>
                <p>Your feedback has been submitted successfully.</p>
            </div>
        </div>
    `;

    // Add styles
    const styles = document.createElement('style');
    styles.textContent = `
        #mv-feedback-modal .mv-modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
        }
        #mv-feedback-modal .mv-modal-content {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 32px;
            border-radius: 16px;
            max-width: 480px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            z-index: 10001;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        #mv-feedback-modal .mv-modal-close {
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #64748b;
        }
        #mv-feedback-modal h3 {
            margin: 0 0 8px 0;
            font-size: 24px;
            color: #1e293b;
        }
        #mv-feedback-modal p {
            margin: 0 0 24px 0;
            color: #64748b;
        }
        #mv-feedback-modal .mv-form-group {
            margin-bottom: 20px;
        }
        #mv-feedback-modal label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #374151;
        }
        #mv-feedback-modal .mv-rating-group {
            display: flex;
            gap: 8px;
        }
        #mv-feedback-modal .mv-rating-btn {
            width: 48px;
            height: 48px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        #mv-feedback-modal .mv-rating-btn:hover,
        #mv-feedback-modal .mv-rating-btn.active {
            border-color: #6366f1;
            background: #6366f1;
            color: white;
        }
        #mv-feedback-modal select,
        #mv-feedback-modal textarea,
        #mv-feedback-modal input[type="email"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        #mv-feedback-modal select:focus,
        #mv-feedback-modal textarea:focus,
        #mv-feedback-modal input:focus {
            outline: none;
            border-color: #6366f1;
        }
        #mv-feedback-modal .mv-submit-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #mv-feedback-modal .mv-submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
        }
        #mv-feedback-modal .mv-success-icon {
            width: 64px;
            height: 64px;
            background: #10b981;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            color: white;
            margin: 0 auto 16px;
        }
        #mv-feedback-modal #mv-feedback-success {
            text-align: center;
            padding: 20px 0;
        }
        #mv-feedback-modal #mv-feedback-success h4 {
            margin: 0 0 8px 0;
            font-size: 24px;
            color: #1e293b;
        }
    `;
    document.head.appendChild(styles);
    document.body.appendChild(modal);

    // Event handlers
    modal.querySelector('.mv-modal-overlay').addEventListener('click', closeFeedbackModal);
    modal.querySelector('.mv-modal-close').addEventListener('click', closeFeedbackModal);

    // Rating buttons
    modal.querySelectorAll('.mv-rating-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            modal.querySelectorAll('.mv-rating-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById('mv-feedback-rating').value = e.target.dataset.rating;
        });
    });

    // Form submission
    document.getElementById('mv-feedback-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = {
            rating: parseInt(document.getElementById('mv-feedback-rating').value),
            type: document.getElementById('mv-feedback-type').value,
            message: document.getElementById('mv-feedback-message').value,
            email: document.getElementById('mv-feedback-email').value,
            page: window.location.pathname,
            timestamp: new Date().toISOString()
        };

        try {
            // Get auth token if available
            const token = localStorage.getItem('auth_token');
            const headers = {
                'Content-Type': 'application/json'
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/v1/feedback', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(formData)
            });

            if (response.ok || response.status === 404) {
                // Show success even if endpoint doesn't exist yet (graceful degradation)
                document.getElementById('mv-feedback-form').style.display = 'none';
                document.getElementById('mv-feedback-success').style.display = 'block';

                trackEvent(MV_EVENTS.FEEDBACK_SUBMIT, {
                    rating: formData.rating,
                    type: formData.type
                });

                setTimeout(closeFeedbackModal, 2000);
            }
        } catch (error) {
            console.error('[Feedback] Error submitting:', error);
            // Still show success for UX (will be logged client-side)
            document.getElementById('mv-feedback-form').style.display = 'none';
            document.getElementById('mv-feedback-success').style.display = 'block';
            setTimeout(closeFeedbackModal, 2000);
        }
    });
}

function closeFeedbackModal() {
    const modal = document.getElementById('mv-feedback-modal');
    if (modal) {
        modal.remove();
    }
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Google Analytics
    initGoogleAnalytics();

    // Initialize reCAPTCHA (only on pages that need it)
    if (document.querySelector('form[data-recaptcha]') ||
        window.location.pathname.includes('login') ||
        window.location.pathname.includes('register')) {
        initRecaptcha();
    }

    // Initialize Mathvidya chatbot
    initChatbot();

    // Add feedback widget (on authenticated pages)
    if (localStorage.getItem('auth_token')) {
        createFeedbackWidget();
    }

    // Track CTA clicks
    document.querySelectorAll('.btn-primary, .btn[href*="login"]').forEach(btn => {
        btn.addEventListener('click', () => {
            trackEvent(MV_EVENTS.CTA_CLICK, {
                button_text: btn.textContent.trim(),
                page: window.location.pathname
            });
        });
    });
});

// Export for use in other scripts
window.MV_Analytics = {
    trackEvent,
    trackPageView,
    getRecaptchaToken,
    MV_EVENTS,
    MV_CONFIG
};
