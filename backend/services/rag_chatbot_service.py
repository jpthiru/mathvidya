"""
Mathvidya RAG-based Chatbot Service

A chatbot that uses Retrieval-Augmented Generation (RAG) with:
1. Sentence transformers for document embeddings
2. FAISS for vector similarity search
3. Local HuggingFace LLM for response generation
4. S3 for knowledge base storage

This provides intelligent, context-aware responses while keeping costs minimal
by using locally-hosted models.
"""

import os
import json
import logging
import hashlib
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import asyncio
from functools import lru_cache
from difflib import SequenceMatcher

import numpy as np

logger = logging.getLogger(__name__)

# ============================================
# Configuration
# ============================================

# Model configurations - using lightweight models for CPU deployment
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # ~80MB, fast
LLM_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # ~2GB, CPU-friendly

# Local cache directory for models and embeddings
CACHE_DIR = Path(__file__).parent.parent / "data" / "chatbot_cache"
EMBEDDINGS_FILE = CACHE_DIR / "knowledge_embeddings.npy"
DOCUMENTS_FILE = CACHE_DIR / "knowledge_documents.json"

# Confidence thresholds
SIMILARITY_THRESHOLD = 0.5  # Minimum similarity to use RAG response
FALLBACK_THRESHOLD = 0.3   # Below this, use pure fallback

# Check if ML models are available at module load time
_ML_AVAILABLE = False
try:
    import sentence_transformers
    _ML_AVAILABLE = True
except ImportError:
    logger.info("ML models not available - using fast keyword matching")


# ============================================
# Knowledge Base - Expanded FAQ Database
# ============================================

KNOWLEDGE_BASE: List[Dict] = [
    # ==================== Getting Started ====================
    {
        "category": "getting_started",
        "title": "How to get started with Mathvidya",
        "content": """Welcome to Mathvidya! Here's how to get started:

1. **Create an Account**: Click 'Sign Up' on the homepage and fill in your details:
   - Your name
   - Email address (will be verified)
   - Your class (X or XII)
   - Password

2. **Verify Your Email**: Enter the 6-digit code sent to your email inbox

3. **Choose a Subscription Plan**:
   - Basic: 5 exams/month, ideal for occasional practice
   - Premium: 50 exams/month with unit-wise practice
   - Centum: Same-day evaluation with direct teacher access

4. **Start Practicing**: Click 'Start New Exam' from your dashboard

**Pro Tip**: Use promo code MATHSTART for a 14-day free trial!""",
        "keywords": ["start", "begin", "new", "account", "sign up", "register", "create account", "join"]
    },
    {
        "category": "account",
        "title": "Login problems and password reset",
        "content": """If you're having trouble logging in:

**Forgot Password?**
1. Click 'Forgot Password?' on the login page
2. Enter your registered email address
3. Check your inbox for a 6-digit verification code
4. Enter the code and create a new password

**Still can't login?**
- Make sure you're using the correct email address
- Check your spam/junk folder for verification emails
- Clear your browser cache and cookies
- Try a different browser (Chrome recommended)
- Ensure Caps Lock is off when entering password

**Account locked?**
If you've attempted too many incorrect logins, your account may be temporarily locked. Wait 15 minutes and try again, or contact support@mathvidya.com""",
        "keywords": ["login", "sign in", "can't login", "forgot password", "password reset", "locked", "account access"]
    },

    # ==================== Subscription & Pricing ====================
    {
        "category": "subscription",
        "title": "Subscription plans and pricing",
        "content": """Mathvidya offers flexible subscription plans:

**Basic Plan** - For casual learners
- 5 exams per month
- Board exam pattern practice only
- 48-hour teacher evaluation
- Email support
- Price: Affordable monthly rate

**Premium Plan** - Most Popular!
- 50 exams per month
- Board exam + Unit-wise practice
- 48-hour teacher evaluation
- Leaderboard access
- 1 hour coaching per month
- Priority email support

**Centum Plan** - For serious achievers
- 50 exams per month
- All practice modes
- SAME-DAY teacher evaluation
- Direct teacher WhatsApp access
- Personalized coaching sessions
- Highest priority support

**All plans include:**
- MCQ auto-evaluation (instant results)
- VSA/SA teacher evaluation
- Detailed performance analytics
- Predicted board scores
- CBSE-aligned questions

Visit our Pricing page for current rates!""",
        "keywords": ["price", "cost", "plan", "subscription", "fee", "payment", "premium", "basic", "centum", "monthly"]
    },
    {
        "category": "subscription",
        "title": "Promo codes and discounts",
        "content": """We offer several ways to save:

**Active Promo Codes:**
- **MATHSTART** - 14 days FREE trial for new users!

**How to apply a promo code:**
1. Sign up for a new account
2. During checkout, enter your promo code
3. Click 'Apply' to see the discount
4. Complete your subscription

**Other ways to save:**
- Annual subscriptions get 2 months free
- Refer a friend program (coming soon)
- Follow us on social media for seasonal offers

**Note:** Only one promo code can be used per account. Promo codes cannot be combined with other offers.""",
        "keywords": ["promo", "discount", "coupon", "offer", "free trial", "save", "code", "MATHSTART"]
    },

    # ==================== Exams & Practice ====================
    {
        "category": "exams",
        "title": "How exams work on Mathvidya",
        "content": """Mathvidya provides flexible exam practice aligned with CBSE patterns:

**Exam Types:**

1. **Full Board Exam** (Standard Pattern)
   - 38 questions, 80 marks
   - Mix of MCQ, VSA, and SA questions
   - Simulates actual board exam experience
   - Great for final preparation

2. **Unit-wise Practice**
   - Focus on specific chapters/units
   - Choose topics you want to practice
   - Perfect for targeted revision

3. **MCQ-only Practice**
   - Quick 20-30 minute sessions
   - Instant auto-evaluation
   - Great for concept testing

**Question Types:**
- **MCQ (1 mark)**: Multiple choice, auto-evaluated instantly
- **VSA (2 marks)**: Very Short Answer, teacher-evaluated
- **SA (3 marks)**: Short Answer, teacher-evaluated

**To start an exam:**
1. Go to your Dashboard
2. Click 'Start New Exam'
3. Select exam type (Board/Unit-wise/MCQ)
4. Choose units if applicable
5. Begin your exam!""",
        "keywords": ["exam", "test", "practice", "mock", "question", "board exam", "unit wise", "start exam"]
    },
    {
        "category": "exams",
        "title": "Answering MCQ questions",
        "content": """For Multiple Choice Questions (MCQ):

**How to answer:**
1. Read the question carefully
2. Review all four options (A, B, C, D)
3. Click on your chosen option
4. Your answer is auto-saved immediately
5. You can change your answer before submitting the exam

**Features:**
- Question navigation panel shows answered/unanswered questions
- Mark questions for review to revisit later
- Timer shows remaining time

**Results:**
- MCQ results are shown INSTANTLY after submission
- See correct answers with explanations
- View your score breakdown by unit

**Tips for MCQs:**
- Read all options before selecting
- Use process of elimination
- Watch for keywords like "always", "never", "most"
- Don't spend too long on difficult questions - mark and move on""",
        "keywords": ["mcq", "multiple choice", "answer", "submit", "option", "select"]
    },
    {
        "category": "exams",
        "title": "Submitting VSA and SA answers",
        "content": """For Very Short Answer (VSA) and Short Answer (SA) questions:

**Step-by-step guide:**

1. **Write your answers on paper**
   - Use clean white paper
   - Write clearly and legibly
   - Number your answers correctly (e.g., Q1, Q2)
   - Show all working steps

2. **Take photos of your answer sheet**
   - Good lighting (natural light is best)
   - Avoid shadows on the paper
   - Ensure all text is readable
   - Take separate photos if multiple pages

3. **Upload your answer images**
   - Click 'Upload Answer Sheet' in the exam
   - Select your image file(s)
   - Preview to ensure quality
   - Max file size: 5MB per image

4. **Submit your exam**
   - Review all answers
   - Click 'Submit Exam'
   - Wait for confirmation

**Tips for better evaluation:**
- Write step-by-step solutions
- Box your final answers
- Use proper mathematical notation
- Keep answers organized and spaced""",
        "keywords": ["vsa", "sa", "written", "handwritten", "upload", "scan", "answer sheet", "photo"]
    },

    # ==================== Evaluation & Results ====================
    {
        "category": "results",
        "title": "When will I get my results?",
        "content": """Results timing depends on the question type:

**MCQ Questions - INSTANT!**
- Results shown immediately after exam submission
- See correct answers and explanations right away
- Score breakdown by unit/chapter

**VSA/SA Questions - Teacher Evaluated:**
Timing depends on your subscription plan:

| Plan | Evaluation Time |
|------|-----------------|
| Centum | Same working day |
| Premium | Within 48 working hours |
| Basic | Within 48 working hours |

**What counts as working hours?**
- Monday to Saturday: 9 AM - 6 PM IST
- Sundays are excluded
- Public holidays are excluded

**How to check your results:**
1. Go to Dashboard > 'My Exams'
2. Look for exams with 'Completed' status
3. Click 'View Results'
4. See detailed question-wise marks

**You'll receive an email notification when your results are ready!**""",
        "keywords": ["result", "score", "marks", "evaluation", "grade", "when", "time", "waiting"]
    },
    {
        "category": "results",
        "title": "Understanding teacher feedback",
        "content": """After teacher evaluation, you get detailed feedback:

**What you'll see:**
- Your uploaded answer image
- Teacher's annotations (tick marks, corrections)
- Marks awarded for each part
- Model answer for comparison
- Explanation of marking scheme

**How to access feedback:**
1. Go to 'My Exams' in dashboard
2. Click on a completed exam
3. Click 'View Results'
4. Select any question to see details

**Types of annotations:**
- Green tick: Correct step/answer
- Red cross: Incorrect step
- Comments: Suggestions for improvement

**Using feedback effectively:**
- Compare your solution with the model answer
- Note where you lost marks
- Review the marking scheme
- Practice similar questions
- Track improvement over time

**Questions about your marks?**
If you believe there's an error, contact support@mathvidya.com with:
- Exam ID
- Question number
- Your concern""",
        "keywords": ["feedback", "comment", "teacher", "explanation", "marks", "annotation", "correction"]
    },

    # ==================== Analytics & Performance ====================
    {
        "category": "analytics",
        "title": "Performance dashboard and analytics",
        "content": """Mathvidya provides detailed analytics to track your progress:

**Dashboard Features:**

1. **Overall Score Trend**
   - Graph showing your scores over time
   - Compare with class average
   - Track improvement

2. **Unit-wise Analysis**
   - Scores by chapter/unit
   - Identify strong and weak areas
   - Focused practice recommendations

3. **Predicted Board Score**
   - AI-powered prediction based on your performance
   - Updates after each exam
   - Confidence range provided

4. **Question Type Breakdown**
   - MCQ vs VSA vs SA performance
   - Time spent on each type
   - Accuracy rates

5. **Leaderboard** (Premium/Centum only)
   - See your class rank
   - Top 10 performers shown
   - Updated weekly

**How to use analytics:**
1. Go to Dashboard > 'Analytics'
2. Select date range
3. Filter by exam type or unit
4. Download reports as PDF

**Tips:**
- Review analytics weekly
- Focus practice on weak units
- Track predicted board score trend""",
        "keywords": ["analytics", "dashboard", "performance", "score", "trend", "graph", "prediction", "leaderboard"]
    },

    # ==================== Technical Support ====================
    {
        "category": "technical",
        "title": "Technical issues and troubleshooting",
        "content": """Having technical problems? Here are common solutions:

**Page not loading?**
- Refresh the page (Ctrl+F5 or Cmd+Shift+R)
- Clear browser cache and cookies
- Try incognito/private mode
- Use Chrome or Firefox (recommended browsers)
- Check your internet connection

**Images not uploading?**
- Use JPEG or PNG format only
- Keep file size under 5MB
- Ensure image is clear and readable
- Check internet connection stability
- Try compressing the image first

**Exam not submitting?**
- Don't close the browser - wait for confirmation
- Check if all required questions are answered
- Try a different browser if stuck
- Screenshot your answers as backup

**Video/Math not displaying?**
- Enable JavaScript in browser
- Update your browser to latest version
- Disable ad blockers temporarily
- Clear browser cache

**Still having issues?**
Contact support@mathvidya.com with:
- Screenshot of the error
- Browser name and version
- Device type (phone/laptop)
- Steps to reproduce the issue

We typically respond within 24 hours!""",
        "keywords": ["error", "problem", "not working", "bug", "issue", "help", "upload", "loading", "technical"]
    },
    {
        "category": "technical",
        "title": "Browser and device requirements",
        "content": """For the best Mathvidya experience:

**Recommended Browsers:**
- Google Chrome (latest version) - BEST
- Mozilla Firefox (latest version)
- Microsoft Edge (latest version)
- Safari (latest version for Mac)

**Not Recommended:**
- Internet Explorer (not supported)
- Very old browser versions

**Device Requirements:**
- Smartphone, tablet, laptop, or desktop
- Minimum screen size: 320px width
- Stable internet connection (3G or better)
- Camera for uploading answer sheets

**For answer sheet upload:**
- Phone camera: 8MP or higher recommended
- Good lighting conditions
- Steady hands (or use a stand)

**Internet Requirements:**
- Minimum: 1 Mbps for browsing
- Recommended: 5 Mbps for smooth experience
- 10 Mbps+ for quick uploads

**Tips:**
- Update your browser regularly
- Enable JavaScript
- Allow pop-ups for mathvidya.com
- Keep at least 100MB free storage""",
        "keywords": ["browser", "device", "chrome", "firefox", "mobile", "phone", "laptop", "requirements"]
    },

    # ==================== CBSE & Curriculum ====================
    {
        "category": "curriculum",
        "title": "CBSE alignment and syllabus coverage",
        "content": """Mathvidya is 100% aligned with CBSE Mathematics curriculum:

**Classes Covered:**
- Class X Mathematics
- Class XII Mathematics

**Syllabus Alignment:**
- Latest CBSE syllabus (2024-25)
- All chapters and units covered
- Proper weightage as per CBSE
- Updated when CBSE makes changes

**Question Paper Pattern:**
We follow official CBSE pattern:

**Class XII (80 marks):**
- Section A: 20 MCQs (1 mark each) = 20 marks
- Section B: 5 VSA questions (2 marks each) = 10 marks
- Section C: 6 SA questions (3 marks each) = 18 marks
- Section D: 4 LA questions (5 marks each) = 20 marks
- Section E: 3 Case-based questions (4 marks each) = 12 marks

**Note:** Long Answer (LA) and Case Study questions coming soon!

**Question Sources:**
- Previous year board papers
- NCERT textbook exercises
- Sample papers by CBSE
- Questions by expert CBSE teachers

**Marking Scheme:**
We follow official CBSE marking scheme for:
- Step marking
- Alternative correct methods
- Partial credit where applicable""",
        "keywords": ["cbse", "board", "syllabus", "class 10", "class 12", "pattern", "ncert", "curriculum"]
    },

    # ==================== Contact & Support ====================
    {
        "category": "contact",
        "title": "How to contact support",
        "content": """Multiple ways to reach us:

**Email Support:**
support@mathvidya.com
Response time: Within 24 hours

**For faster help, include:**
- Your registered email
- Exam ID (if exam-related)
- Screenshot of the issue
- Device and browser details

**In-App Support:**
- Use this chat for quick answers
- Click 'Feedback' button on any page
- Detailed feedback form available

**Social Media:**
- Follow us for updates and tips
- DM for quick queries

**Common Support Requests:**
- Technical issues: Include screenshots
- Billing queries: Include transaction ID
- Evaluation concerns: Include exam ID and question number
- Account issues: Use registered email to contact

**Support Hours:**
Monday - Saturday: 9 AM - 6 PM IST
(Closed on Sundays and public holidays)

**Emergency?**
For urgent exam-related issues during an active exam, email with subject line: "URGENT: [Your Issue]"

We're here to help you succeed!""",
        "keywords": ["contact", "support", "email", "phone", "reach", "talk", "help", "query"]
    },

    # ==================== Parent Access ====================
    {
        "category": "parents",
        "title": "Parent access and monitoring",
        "content": """Parents can monitor their child's progress on Mathvidya:

**Parent Account Features:**
- View student's exam scores
- Track performance trends
- See analytics and predictions
- Access subscription details
- Read-only access (cannot take exams)

**How to set up parent access:**
1. Student creates account first
2. Add parent email in profile settings
3. Parent receives invitation email
4. Parent creates account and links to student

**What parents can see:**
- All completed exam scores
- Performance analytics
- Unit-wise progress
- Predicted board scores
- Subscription status

**What parents cannot do:**
- Take exams on behalf of student
- Change student's answers
- Modify account settings

**Privacy Note:**
- Student data is protected
- Only linked parents can view
- Compliant with child data protection

**Multiple children?**
One parent account can be linked to multiple student accounts.""",
        "keywords": ["parent", "guardian", "monitor", "child", "access", "view", "family"]
    },

    # ==================== Refunds ====================
    {
        "category": "billing",
        "title": "Refund and cancellation policy",
        "content": """Our refund and cancellation policy:

**Free Trial:**
- No charge during trial period
- Cancel anytime before trial ends
- No payment information needed for trial

**Paid Subscriptions:**

**Cancellation:**
- Cancel anytime from account settings
- Access continues until period ends
- No automatic renewal after cancellation

**Refunds:**
- Full refund within 7 days of purchase if:
  - No exams taken
  - Technical issues preventing use
- Partial refund may be considered for:
  - Extended technical issues
  - Service unavailability

**How to request refund:**
1. Email support@mathvidya.com
2. Subject: "Refund Request - [Your Email]"
3. Include:
   - Reason for refund
   - Transaction ID
   - Date of purchase

**Processing Time:**
- Refund requests: 3-5 business days
- Amount credited: 5-10 business days to bank

**Non-refundable:**
- Exams already taken
- Partial month usage after 7 days
- Promo code redeemed subscriptions (check terms)""",
        "keywords": ["refund", "cancel", "money back", "billing", "payment", "subscription cancel"]
    },
]


# ============================================
# Global State for Models (Lazy Loading)
# ============================================

_embedding_model = None
_tokenizer = None
_llm_model = None
_faiss_index = None
_document_embeddings = None
_documents_loaded = False


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# Embedding Functions
# ============================================

def get_embedding_model():
    """Lazy load the sentence transformer embedding model."""
    global _embedding_model

    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed. Using fallback.")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None

    return _embedding_model


def compute_embeddings(texts: List[str]) -> Optional[np.ndarray]:
    """Compute embeddings for a list of texts."""
    model = get_embedding_model()
    if model is None:
        return None

    try:
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings
    except Exception as e:
        logger.error(f"Failed to compute embeddings: {e}")
        return None


# ============================================
# Vector Store Functions (FAISS)
# ============================================

def get_combined_knowledge_base() -> List[Dict]:
    """
    Get combined knowledge base from static + S3 documents.
    """
    all_docs = list(KNOWLEDGE_BASE)  # Start with static knowledge

    # Try to load S3 documents
    try:
        from services.s3_knowledge_loader import get_all_knowledge_documents
        s3_docs = get_all_knowledge_documents()
        if s3_docs:
            all_docs.extend(s3_docs)
            logger.info(f"Added {len(s3_docs)} documents from S3")
    except ImportError:
        logger.warning("S3 knowledge loader not available")
    except Exception as e:
        logger.warning(f"Failed to load S3 documents: {e}")

    return all_docs


# Global combined knowledge base
_combined_knowledge: List[Dict] = []


def build_knowledge_index():
    """Build FAISS index from knowledge base."""
    global _faiss_index, _document_embeddings, _documents_loaded, _combined_knowledge

    if _documents_loaded:
        return _faiss_index is not None

    _ensure_cache_dir()

    # Get combined knowledge base
    _combined_knowledge = get_combined_knowledge_base()

    # Check for cached embeddings
    if EMBEDDINGS_FILE.exists() and DOCUMENTS_FILE.exists():
        try:
            _document_embeddings = np.load(str(EMBEDDINGS_FILE))
            with open(DOCUMENTS_FILE, 'r') as f:
                cached_docs = json.load(f)

            # Verify cache is still valid (same documents)
            current_hash = hashlib.md5(
                json.dumps([d['content'] for d in _combined_knowledge]).encode()
            ).hexdigest()

            if cached_docs.get('hash') == current_hash:
                logger.info("Using cached knowledge embeddings")
                _init_faiss_index(_document_embeddings)
                _documents_loaded = True
                return True
        except Exception as e:
            logger.warning(f"Failed to load cached embeddings: {e}")

    # Compute new embeddings
    logger.info(f"Computing embeddings for {len(_combined_knowledge)} documents...")
    texts = [f"{doc['title']}\n{doc['content']}" for doc in _combined_knowledge]

    _document_embeddings = compute_embeddings(texts)
    if _document_embeddings is None:
        _documents_loaded = True  # Mark as attempted
        return False

    # Cache the embeddings
    try:
        np.save(str(EMBEDDINGS_FILE), _document_embeddings)
        current_hash = hashlib.md5(
            json.dumps([d['content'] for d in _combined_knowledge]).encode()
        ).hexdigest()
        with open(DOCUMENTS_FILE, 'w') as f:
            json.dump({'hash': current_hash}, f)
        logger.info("Cached knowledge embeddings")
    except Exception as e:
        logger.warning(f"Failed to cache embeddings: {e}")

    _init_faiss_index(_document_embeddings)
    _documents_loaded = True
    return True


def _init_faiss_index(embeddings: np.ndarray):
    """Initialize FAISS index with embeddings."""
    global _faiss_index

    try:
        import faiss

        dimension = embeddings.shape[1]
        _faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        _faiss_index.add(embeddings)

        logger.info(f"FAISS index built with {embeddings.shape[0]} documents")
    except ImportError:
        logger.warning("faiss-cpu not installed. Using numpy fallback.")
        _faiss_index = None
    except Exception as e:
        logger.error(f"Failed to build FAISS index: {e}")
        _faiss_index = None


def search_similar_documents(query: str, top_k: int = 3) -> List[Tuple[Dict, float]]:
    """Search for similar documents using vector similarity."""
    global _combined_knowledge

    build_knowledge_index()

    if _document_embeddings is None:
        return []

    # Use combined knowledge base (populated during build_knowledge_index)
    knowledge_base = _combined_knowledge if _combined_knowledge else KNOWLEDGE_BASE

    query_embedding = compute_embeddings([query])
    if query_embedding is None:
        return []

    try:
        import faiss
        faiss.normalize_L2(query_embedding)

        if _faiss_index is not None:
            scores, indices = _faiss_index.search(query_embedding, top_k)
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if idx >= 0 and score > 0 and idx < len(knowledge_base):
                    results.append((knowledge_base[idx], float(score)))
            return results
    except ImportError:
        pass

    # Numpy fallback
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    doc_norms = _document_embeddings / np.linalg.norm(_document_embeddings, axis=1, keepdims=True)
    similarities = np.dot(doc_norms, query_norm.T).flatten()

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    results = [(knowledge_base[i], float(similarities[i])) for i in top_indices if i < len(knowledge_base)]

    return results


# ============================================
# LLM Response Generation
# ============================================

def get_llm_model():
    """Lazy load the LLM model for response generation."""
    global _tokenizer, _llm_model

    if _llm_model is None:
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            logger.info(f"Loading LLM model: {LLM_MODEL}")

            _tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
            _llm_model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL,
                torch_dtype=torch.float32,  # Use float32 for CPU
                device_map="cpu",
                low_cpu_mem_usage=True
            )

            logger.info("LLM model loaded successfully")
        except ImportError:
            logger.warning("transformers not installed. Using template responses.")
            return None, None
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            return None, None

    return _tokenizer, _llm_model


def generate_llm_response(query: str, context: str, max_length: int = 512) -> Optional[str]:
    """Generate a response using the LLM with retrieved context."""
    tokenizer, model = get_llm_model()

    if tokenizer is None or model is None:
        return None

    try:
        # TinyLlama chat format
        prompt = f"""<|system|>
You are a helpful assistant for Mathvidya, an online CBSE mathematics practice platform.
Answer the user's question based ONLY on the provided context. Be concise and helpful.
If the context doesn't contain relevant information, politely say you don't have that information.
</s>
<|user|>
Context:
{context}

Question: {query}
</s>
<|assistant|>
"""

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)

        outputs = model.generate(
            inputs.input_ids,
            max_new_tokens=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()

        return response

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return None


# ============================================
# Fallback: Keyword-based Response
# ============================================

def keyword_search(query: str) -> Tuple[Optional[Dict], float]:
    """Fallback keyword-based search when embeddings aren't available."""
    query_lower = query.lower()
    best_match = None
    best_score = 0.0

    for doc in KNOWLEDGE_BASE:
        score = 0.0

        # Check keywords
        keyword_matches = sum(
            1 for keyword in doc.get("keywords", [])
            if keyword.lower() in query_lower
        )
        if keyword_matches > 0:
            score = min(0.8, 0.3 + (keyword_matches * 0.15))

        # Check title similarity
        title_similarity = SequenceMatcher(
            None, query_lower, doc["title"].lower()
        ).ratio()
        if title_similarity > 0.5:
            score = max(score, title_similarity)

        if score > best_score:
            best_score = score
            best_match = doc

    return best_match, best_score


# ============================================
# Greeting Detection
# ============================================

GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste", "hii", "helo"]
THANKS = ["thank", "thanks", "thank you", "thankyou", "ty"]
BYES = ["bye", "goodbye", "good bye", "see you", "later"]

def detect_special_intent(message: str) -> Optional[str]:
    """Detect greetings, thanks, and farewells."""
    msg_lower = message.lower().strip()

    for greeting in GREETINGS:
        if msg_lower.startswith(greeting) or msg_lower == greeting:
            return "greeting"

    for thank in THANKS:
        if thank in msg_lower:
            return "thanks"

    for bye in BYES:
        if bye in msg_lower:
            return "bye"

    return None


SPECIAL_RESPONSES = {
    "greeting": """Hello! Welcome to Mathvidya Support! I'm here to help you with:

- Getting started with the platform
- Understanding subscription plans
- Taking practice exams
- Checking your results
- Technical support

What would you like to know about?""",

    "thanks": """You're welcome! I'm glad I could help.

Is there anything else you'd like to know about Mathvidya? I'm happy to assist with:
- Exam practice questions
- Subscription plans
- Technical issues
- Any other queries

Just ask away!""",

    "bye": """Goodbye! Best of luck with your CBSE Mathematics preparation!

Remember:
- Use promo code MATHSTART for a 14-day free trial
- Practice regularly for best results
- Contact support@mathvidya.com if you need help

See you soon!"""
}


# ============================================
# Main Response Generation
# ============================================

def generate_response(user_message: str) -> Dict:
    """
    Generate a chatbot response using RAG.

    Priority:
    1. Special intents (greetings, thanks)
    2. RAG with vector similarity + LLM
    3. Keyword-based fallback
    4. Generic fallback
    """
    if not user_message or len(user_message.strip()) < 2:
        return {
            "response": "Please type your question and I'll do my best to help!",
            "confidence": 1.0,
            "matched_question": None,
            "source": "validation"
        }

    # Check special intents
    intent = detect_special_intent(user_message)
    if intent and intent in SPECIAL_RESPONSES:
        return {
            "response": SPECIAL_RESPONSES[intent],
            "confidence": 1.0,
            "matched_question": intent.capitalize(),
            "source": "intent"
        }

    # Fast path: Skip RAG if ML models not available
    if not _ML_AVAILABLE:
        # Use keyword-based search directly (fast)
        keyword_match, keyword_score = keyword_search(user_message)

        if keyword_match and keyword_score >= FALLBACK_THRESHOLD:
            return {
                "response": keyword_match["content"],
                "confidence": keyword_score,
                "matched_question": keyword_match["title"],
                "source": "keyword"
            }

        # Generic fallback
        return {
            "response": """I'm not sure I fully understand your question. Here are some topics I can help with:

**Getting Started**
- How to create an account
- Taking your first exam

**Subscriptions**
- Plan options and pricing
- Using promo codes (try MATHSTART!)

**Exams & Results**
- How exams work
- Checking your scores
- Understanding feedback

**Technical Help**
- Upload issues
- Browser problems

Could you please rephrase your question, or ask about one of these topics?

For specific issues, email support@mathvidya.com""",
            "confidence": 0.0,
            "matched_question": None,
            "source": "fallback"
        }

    # Try RAG with vector similarity (only if ML available)
    similar_docs = search_similar_documents(user_message, top_k=3)

    if similar_docs and similar_docs[0][1] >= SIMILARITY_THRESHOLD:
        best_doc, score = similar_docs[0]

        # Build context from top documents
        context = "\n\n---\n\n".join([
            f"**{doc['title']}**\n{doc['content']}"
            for doc, s in similar_docs if s >= FALLBACK_THRESHOLD
        ])

        # Try LLM generation for natural response
        llm_response = generate_llm_response(user_message, context)

        if llm_response:
            return {
                "response": llm_response,
                "confidence": score,
                "matched_question": best_doc["title"],
                "source": "rag_llm"
            }

        # Fall back to direct document content
        return {
            "response": best_doc["content"],
            "confidence": score,
            "matched_question": best_doc["title"],
            "source": "rag_document"
        }

    # Try keyword-based search as fallback
    keyword_match, keyword_score = keyword_search(user_message)

    if keyword_match and keyword_score >= FALLBACK_THRESHOLD:
        return {
            "response": keyword_match["content"],
            "confidence": keyword_score,
            "matched_question": keyword_match["title"],
            "source": "keyword"
        }

    # Generic fallback
    return {
        "response": """I'm not sure I fully understand your question. Here are some topics I can help with:

**Getting Started**
- How to create an account
- Taking your first exam

**Subscriptions**
- Plan options and pricing
- Using promo codes (try MATHSTART!)

**Exams & Results**
- How exams work
- Checking your scores
- Understanding feedback

**Technical Help**
- Upload issues
- Browser problems

Could you please rephrase your question, or ask about one of these topics?

For specific issues, email support@mathvidya.com""",
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
    "How do I upload my answer sheet?",
]


def get_suggested_questions() -> List[str]:
    """Return suggested questions for the chat interface."""
    return SUGGESTED_QUESTIONS


# ============================================
# Pre-warm Models (Optional - call at startup)
# ============================================

def initialize_models():
    """Pre-load models at application startup for faster first response."""
    logger.info("Initializing RAG chatbot models...")

    # Load embedding model
    get_embedding_model()

    # Build knowledge index
    build_knowledge_index()

    # Optionally load LLM (heavy - might skip for faster startup)
    # get_llm_model()

    logger.info("RAG chatbot initialization complete")
