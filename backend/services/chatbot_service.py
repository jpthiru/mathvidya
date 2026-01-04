"""
Mathvidya Chatbot Service

A hybrid chatbot that uses:
1. Rule-based FAQ matching for common questions (instant, free)
2. Optional LLM integration for complex queries (configurable)

This keeps costs at zero for most interactions while providing
intelligent responses for complex questions.
"""

import re
import logging
from typing import Optional, List, Dict, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ============================================
# FAQ Knowledge Base
# ============================================

FAQ_DATABASE: List[Dict] = [
    # Getting Started
    {
        "keywords": ["start", "begin", "new", "account", "sign up", "register"],
        "patterns": [r"how.*(start|begin|get started)", r"new.*user", r"create.*account"],
        "question": "How do I get started with Mathvidya?",
        "answer": """Welcome to Mathvidya! Here's how to get started:

1. **Create an Account**: Click 'Sign Up' and fill in your details (name, email, class X or XII)
2. **Verify Email**: Enter the 6-digit code sent to your email
3. **Choose a Plan**: Select a subscription plan that fits your needs
4. **Start Practicing**: Take your first practice exam!

You can start with our free trial to explore the platform."""
    },
    {
        "keywords": ["login", "sign in", "can't login", "forgot password", "password reset"],
        "patterns": [r"(can't|cannot|unable).*(login|sign in)", r"forgot.*password", r"reset.*password"],
        "question": "I can't login / forgot my password",
        "answer": """If you're having trouble logging in:

1. **Forgot Password**: Click 'Forgot Password?' on the login page
2. **Enter Email**: Enter your registered email address
3. **Check Email**: Enter the 6-digit code we send you
4. **Reset Password**: Create a new password

If you're still having issues, make sure:
- You're using the correct email address
- Check your spam folder for verification emails
- Try clearing your browser cache"""
    },

    # Subscription & Pricing
    {
        "keywords": ["price", "cost", "plan", "subscription", "fee", "payment", "free"],
        "patterns": [r"how much", r"price|pricing", r"subscription.*plan", r"free.*trial"],
        "question": "What are the subscription plans and pricing?",
        "answer": """We offer several plans to suit your needs:

**Basic Plan** - For casual practice
- 5 exams per month
- Board exam pattern practice
- 48-hour evaluation

**Premium Plan** - Most popular
- 50 exams per month
- Unit-wise practice
- 48-hour evaluation
- Leaderboard access

**Centum Plan** - For serious students
- 50 exams per month
- Same-day evaluation
- Direct teacher access
- Priority support

Visit our Pricing page for current rates. Use code **MATHSTART** for a 14-day free trial!"""
    },
    {
        "keywords": ["promo", "discount", "coupon", "offer", "free trial"],
        "patterns": [r"promo.*code", r"discount", r"free.*trial", r"coupon"],
        "question": "Are there any promo codes or discounts?",
        "answer": """Yes! We have special offers:

**MATHSTART** - Get 14 days free trial for new users!

To apply a promo code:
1. Go to the signup page
2. Enter your details
3. Enter the promo code during checkout

Follow us on social media for seasonal discounts and special offers!"""
    },

    # Exams & Practice
    {
        "keywords": ["exam", "test", "practice", "mock", "question"],
        "patterns": [r"how.*(take|start).*exam", r"practice.*test", r"exam.*work"],
        "question": "How do exams work on Mathvidya?",
        "answer": """Mathvidya offers flexible exam practice:

**Exam Types:**
- **Full Board Exam**: Complete CBSE pattern (80 marks, 38 questions)
- **Unit-wise Practice**: Focus on specific units/chapters
- **MCQ Practice**: Quick multiple-choice practice

**Question Types:**
- MCQ (1 mark) - Auto-evaluated instantly
- VSA (2 marks) - Teacher-evaluated
- SA (3 marks) - Teacher-evaluated

**To start an exam:**
1. Go to your Dashboard
2. Click 'Start New Exam'
3. Select exam type and units
4. Complete and submit!"""
    },
    {
        "keywords": ["mcq", "multiple choice", "answer", "submit"],
        "patterns": [r"mcq.*answer", r"multiple.*choice", r"submit.*answer"],
        "question": "How do I answer MCQ questions?",
        "answer": """For MCQ questions:

1. Read the question carefully
2. Click on your chosen option (A, B, C, or D)
3. Your answer is auto-saved
4. You can change your answer before submitting
5. MCQs are auto-evaluated - results shown immediately!

**Tips:**
- Read all options before selecting
- Use process of elimination
- Manage your time wisely"""
    },
    {
        "keywords": ["vsa", "sa", "written", "handwritten", "upload", "scan"],
        "patterns": [r"(vsa|sa).*answer", r"upload.*answer", r"handwritten", r"scan.*paper"],
        "question": "How do I submit VSA/SA (written) answers?",
        "answer": """For Very Short Answer (VSA) and Short Answer (SA) questions:

1. **Write answers on paper** - Use clean white paper
2. **Take clear photos** - Good lighting, no shadows
3. **Upload images** - Click 'Upload Answer Sheet' in the exam
4. **Submit exam** - Click 'Submit' when done

**Tips for better evaluation:**
- Write clearly and legibly
- Number your answers correctly
- Show all working steps
- Take photos in good lighting"""
    },

    # Evaluation & Results
    {
        "keywords": ["result", "score", "marks", "evaluation", "grade"],
        "patterns": [r"when.*result", r"check.*score", r"see.*marks", r"evaluation.*time"],
        "question": "When will I get my results?",
        "answer": """Results timing depends on question type:

**MCQ Questions:**
- Instant results! Shown immediately after submission

**VSA/SA Questions (Teacher Evaluated):**
- **Centum Plan**: Same working day
- **Other Plans**: Within 48 working hours

**To check your results:**
1. Go to Dashboard → 'My Exams'
2. Click on the completed exam
3. View detailed question-wise results

You'll also receive an email notification when results are ready!"""
    },
    {
        "keywords": ["feedback", "comment", "teacher", "explanation"],
        "patterns": [r"teacher.*feedback", r"explanation", r"why.*wrong"],
        "question": "How do I see teacher feedback?",
        "answer": """To view teacher feedback:

1. Go to 'My Exams' in your dashboard
2. Click on a completed exam
3. Click 'View Results'
4. Each question shows:
   - Your answer
   - Correct answer
   - Marks obtained
   - Teacher's feedback (for VSA/SA)
   - Model answer explanation

Use this feedback to understand mistakes and improve!"""
    },

    # Technical Issues
    {
        "keywords": ["error", "problem", "not working", "bug", "issue", "help"],
        "patterns": [r"(not|isn't|doesn't).*work", r"error", r"problem", r"issue"],
        "question": "I'm facing a technical issue",
        "answer": """Sorry to hear that! Here are some common fixes:

**General Issues:**
- Refresh the page (Ctrl+F5)
- Clear browser cache
- Try a different browser (Chrome recommended)
- Check your internet connection

**Upload Issues:**
- Use JPEG or PNG format
- Keep file size under 5MB
- Ensure good image quality

**Still having problems?**
- Use the Feedback button to report the issue
- Email us at support@mathvidya.com
- Include screenshots if possible

We typically respond within 24 hours!"""
    },

    # CBSE Specific
    {
        "keywords": ["cbse", "board", "syllabus", "class 10", "class 12", "pattern"],
        "patterns": [r"cbse.*pattern", r"board.*exam", r"syllabus", r"class.*(10|12|x|xii)"],
        "question": "Does Mathvidya follow CBSE pattern?",
        "answer": """Yes! Mathvidya is 100% aligned with CBSE:

**We Follow:**
- Latest CBSE syllabus (2024-25)
- Official exam pattern and marking scheme
- Unit-wise weightage as per CBSE
- Question types: MCQ, VSA, SA (LA coming soon!)

**Classes Supported:**
- Class X Mathematics
- Class XII Mathematics

Our questions are curated by experienced CBSE teachers to match board exam standards!"""
    },

    # Contact & Support
    {
        "keywords": ["contact", "support", "email", "phone", "reach", "talk"],
        "patterns": [r"contact.*us", r"support.*team", r"email.*address", r"phone.*number"],
        "question": "How do I contact support?",
        "answer": """You can reach us through:

**Email:** support@mathvidya.com
**Response Time:** Within 24 hours

**In-App Options:**
- Click the 'Feedback' button on any page
- Use this chat for quick answers

**For urgent issues:**
- Describe your problem in detail
- Include screenshots if relevant
- Mention your registered email

We're here to help you succeed!"""
    },
]


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def find_matching_faq(user_message: str) -> Tuple[Optional[Dict], float]:
    """
    Find the best matching FAQ for a user message.

    Returns:
        Tuple of (matching_faq, confidence_score)
    """
    user_message_lower = user_message.lower().strip()
    best_match = None
    best_score = 0.0

    for faq in FAQ_DATABASE:
        score = 0.0

        # Check pattern matches (highest priority)
        for pattern in faq.get("patterns", []):
            if re.search(pattern, user_message_lower):
                score = max(score, 0.9)
                break

        # Check keyword matches
        keyword_matches = sum(
            1 for keyword in faq["keywords"]
            if keyword.lower() in user_message_lower
        )
        if keyword_matches > 0:
            keyword_score = min(0.7, 0.3 + (keyword_matches * 0.15))
            score = max(score, keyword_score)

        # Check question similarity
        question_similarity = calculate_similarity(user_message, faq["question"])
        if question_similarity > 0.5:
            score = max(score, question_similarity)

        if score > best_score:
            best_score = score
            best_match = faq

    return best_match, best_score


def get_greeting_response(user_message: str) -> Optional[str]:
    """Check if message is a greeting and return appropriate response."""
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste"]
    user_lower = user_message.lower().strip()

    for greeting in greetings:
        if user_lower.startswith(greeting) or user_lower == greeting:
            return """Hello! Welcome to Mathvidya! 👋

I'm here to help you with:
- Getting started with the platform
- Understanding our subscription plans
- Taking practice exams
- Checking your results
- Technical support

What would you like to know about?"""

    return None


def get_fallback_response() -> str:
    """Return a helpful fallback response when no FAQ matches."""
    return """I'm not sure I understand your question completely. Here are some things I can help with:

**Popular Topics:**
• How to get started
• Subscription plans & pricing
• Taking practice exams
• Checking results & feedback
• Technical issues

**Quick Actions:**
• Use promo code **MATHSTART** for 14 days free!
• Visit the Help section for detailed guides
• Contact support@mathvidya.com for specific issues

Could you please rephrase your question or choose one of the topics above?"""


def generate_response(user_message: str) -> Dict:
    """
    Generate a chatbot response for the user message.

    Returns:
        Dict with 'response', 'confidence', 'matched_question' keys
    """
    if not user_message or len(user_message.strip()) < 2:
        return {
            "response": "Please type your question and I'll do my best to help!",
            "confidence": 1.0,
            "matched_question": None,
            "source": "validation"
        }

    # Check for greetings
    greeting_response = get_greeting_response(user_message)
    if greeting_response:
        return {
            "response": greeting_response,
            "confidence": 1.0,
            "matched_question": "Greeting",
            "source": "greeting"
        }

    # Find matching FAQ
    matched_faq, confidence = find_matching_faq(user_message)

    if matched_faq and confidence >= 0.5:
        return {
            "response": matched_faq["answer"],
            "confidence": confidence,
            "matched_question": matched_faq["question"],
            "source": "faq"
        }

    # Fallback response
    return {
        "response": get_fallback_response(),
        "confidence": 0.0,
        "matched_question": None,
        "source": "fallback"
    }


# ============================================
# Suggested Questions
# ============================================

SUGGESTED_QUESTIONS = [
    "How do I get started?",
    "What are the subscription plans?",
    "How do exams work?",
    "When will I get my results?",
    "I'm facing a technical issue",
]


def get_suggested_questions() -> List[str]:
    """Return a list of suggested questions for the chat interface."""
    return SUGGESTED_QUESTIONS
