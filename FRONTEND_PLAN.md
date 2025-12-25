# Mathvidya Frontend - Implementation Plan

## Target Audience Analysis

### Students (Class X & XII)
**Age Group:** 15-18 years
**Digital Habits:**
- Mobile-first mindset
- Social media influenced (Instagram, YouTube aesthetics)
- Short attention span - need quick, visual content
- Gaming culture - appreciate gamification (badges, leaderboards)
- Meme culture - humor resonates
- Value peer recognition and competition

**Likes:**
- Clean, modern UI with vibrant colors
- Interactive animations and micro-interactions
- Progress bars and achievement indicators
- Dark mode option
- Mobile-responsive design
- Quick loading times
- Emojis and visual feedback

**Dislikes:**
- Cluttered, text-heavy pages
- Slow, boring interfaces
- Corporate/institutional look
- Mandatory long forms
- Complex navigation
- Lack of visual feedback

## Color Palette & Theme

### Primary Colors
- **Brand Primary:** #6366F1 (Indigo - modern, trustworthy)
- **Brand Secondary:** #EC4899 (Pink - energetic, youthful)
- **Accent:** #10B981 (Green - success, growth)
- **Warning:** #F59E0B (Amber - alerts)
- **Error:** #EF4444 (Red - errors)

### Neutral Colors
- **Dark:** #1F2937 (Gray-800)
- **Medium:** #6B7280 (Gray-500)
- **Light:** #F3F4F6 (Gray-100)
- **White:** #FFFFFF

### Gradient Accents
- Hero gradient: Indigo → Purple → Pink
- Success gradient: Green → Teal
- Card hover: Subtle indigo glow

## Typography
- **Headings:** Poppins (Google Font) - Modern, friendly
- **Body:** Inter (Google Font) - Highly readable
- **Monospace:** JetBrains Mono - For code/scores

## Frontend Technology Stack

### Core
- **HTML5** - Semantic markup
- **CSS3** - Animations, Grid, Flexbox
- **Vanilla JavaScript** - No framework overhead for V1
- **LocalStorage** - Session management

### Libraries (CDN)
- **Axios** - HTTP requests to backend
- **Chart.js** - Performance graphs
- **Animate.css** - Pre-built animations
- **Font Awesome** - Icons
- **MathJax** - LaTeX rendering for math equations

### Future (Post-V1)
- React/Vue for complex state management
- TypeScript for type safety
- Tailwind CSS for utility classes

## Page Structure

### 1. Static Marketing Pages (Public)

#### 1.1 Landing Page (`index.html`)
**Purpose:** Convert visitors to users

**Sections:**
1. **Hero Section**
   - Animated gradient background
   - Bold headline: "Master CBSE Mathematics with Expert Guidance"
   - Subheadline: "Practice Smart. Get Evaluated. Score Higher."
   - CTA buttons: "Start Free Trial" + "View Plans"
   - Animated illustration: Student solving math → getting feedback → celebrating

2. **Problem-Solution Section**
   - Problem: "Struggling with board exam preparation?"
   - Solution cards (animated on scroll):
     - 📝 Practice with real CBSE patterns
     - 👨‍🏫 Get expert teacher evaluation
     - 📊 Track your progress with AI predictions
     - 🏆 Compete on leaderboards

3. **Class-Specific Tabs**
   - Toggle between Class X and Class XII
   - Different content, exam patterns, success stories
   - Animated tab switching

4. **Features Grid**
   - Icon + Title + Description cards
   - Hover animations (lift + glow)
   - Features:
     - MCQ Auto-Evaluation
     - Teacher-Graded Answers
     - Unit-Wise Practice
     - Board Score Prediction
     - 24/48hr Evaluation SLA
     - Parent Dashboard

5. **How It Works** (Timeline Animation)
   - Step 1: Register & Choose Plan
   - Step 2: Take Practice Exams
   - Step 3: Get Expert Evaluation
   - Step 4: Review & Improve
   - Step 5: Ace Board Exams 🎉

6. **Subscription Plans** (Pricing Cards)
   - 4 cards: Basic, Premium MCQ, Premium, Centum
   - Highlight "Most Popular" tag
   - Feature comparison table
   - Animated price hover effects

7. **Testimonials** (Carousel)
   - Student success stories
   - Parent reviews
   - Auto-rotating carousel
   - Star ratings

8. **Teacher Highlight**
   - "Meet Our Expert Evaluators"
   - Teacher profiles with credentials
   - "Join as Teacher" CTA

9. **FAQ Section** (Accordion)
   - Common questions
   - Smooth expand/collapse animations

10. **Footer**
    - Links: About, Contact, Terms, Privacy
    - Social media icons
    - Copyright notice

#### 1.2 Class X Page (`class-x.html`)
**Specific Content:**
- CBSE Class X exam pattern
- Unit breakdown (Number Systems, Algebra, Geometry, etc.)
- Sample questions
- Success stories from Class X students
- Class X leaderboard preview

#### 1.3 Class XII Page (`class-xii.html`)
**Specific Content:**
- CBSE Class XII exam pattern
- Unit breakdown (Relations, Calculus, Vectors, Probability, etc.)
- Sample questions
- Success stories from Class XII students
- Class XII leaderboard preview

#### 1.4 About Us (`about.html`)
- Mission & Vision
- Team introduction
- Why Mathvidya is different
- Contact information

### 2. Authentication Pages

#### 2.1 Login Page (`login.html`)
**Design:**
- Split screen layout:
  - Left: Animated illustration + testimonial rotation
  - Right: Login form
- Role selector: Student | Teacher | Admin
- Email + Password fields
- "Remember Me" checkbox
- "Forgot Password?" link
- "Login" button with loading animation
- "Don't have an account? Register" link

**Features:**
- Form validation with visual feedback
- Error messages below fields
- Success animation on login
- Redirect based on role:
  - Student → Student Dashboard
  - Teacher → Teacher Dashboard
  - Admin → Admin Dashboard

#### 2.2 Register Page (`register.html`)
**Multi-step Form:**
- Step 1: Choose Role (Student/Parent/Teacher)
- Step 2: Personal Details
- Step 3: Class Selection (for students)
- Step 4: Choose Plan (for students)
- Progress indicator at top
- "Previous" and "Next" buttons
- Final "Create Account" button

**Validation:**
- Real-time field validation
- Password strength meter
- Email format check
- Terms acceptance checkbox

### 3. Student Pages

#### 3.1 Student Dashboard (`student-dashboard.html`)
**Header:**
- Mathvidya logo (left)
- Navigation: Dashboard | My Exams | Performance | Leaderboard
- Profile card (right): Avatar/Initials + Name + Dropdown (Profile, Settings, Logout)

**Main Content:**
- **Welcome Card**
  - Greeting: "Welcome back, [Name]! 👋"
  - Motivational quote
  - Current streak: "🔥 5 days"

- **Quick Stats Row** (4 cards)
  - Exams Taken This Month: 3/50
  - Average Score: 78.5%
  - Board Score Prediction: 85-92%
  - Current Rank: #12 🥉

- **Start New Exam Section**
  - Tab selector: Unit-Wise | Board Exam
  - **Unit-Wise Tab:**
    - Grid of unit cards with icons
    - Progress ring showing completion %
    - "Practice" button
  - **Board Exam Tab:**
    - Full board exam card
    - "Start Full Board Exam" button
    - Timer estimate: "⏱️ 3 hours"

- **Recent Exams Table**
  - Columns: Date | Type | Score | Status | Actions
  - Status badges: Evaluated | Pending | In Progress
  - Actions: View Results | Download Report

- **Performance Graph**
  - Line chart showing score trends
  - Last 10 exams

#### 3.2 Take Exam Page (`take-exam.html`)
**MCQ Interface:**
- Timer at top (countdown)
- Progress bar: "Question 5 of 38"
- Question display area:
  - Question number + marks
  - Question text with LaTeX rendering
  - Image (if applicable)
- Answer options (radio buttons):
  - A, B, C, D with hover effects
  - Visual feedback on selection
- Navigation:
  - Question palette (sidebar): Shows all questions
    - Answered: Green
    - Unanswered: Gray
    - Marked for review: Orange
  - Buttons: Previous | Next | Mark for Review | Submit Exam
- Sticky "Submit Exam" button (always visible)

**Submit Confirmation:**
- Modal dialog showing:
  - Answered: X questions
  - Unanswered: Y questions
  - Marked for review: Z questions
  - "Confirm Submit" | "Go Back"

#### 3.3 Exam Results Page (`exam-results.html`)
- Overall score card (large, animated reveal)
- Score breakdown:
  - MCQ section: X/Y
  - VSA section: X/Y (if evaluated)
  - SA section: X/Y (if evaluated)
- Unit-wise performance
- Question-by-question review:
  - Your answer vs correct answer
  - Teacher comments (for manual questions)
  - Annotated answer sheet images
- Download PDF report button
- "Take Another Exam" CTA

#### 3.4 Performance Analytics (`performance.html`)
- **Overview Cards:**
  - Total exams taken
  - Average score
  - Improvement rate
  - Board prediction

- **Unit-Wise Performance** (Bar chart)
- **Strength & Weaknesses** (Tag cloud)
- **Score Trend** (Line graph)
- **Question Type Breakdown** (Pie chart)
- **Recent Activity Timeline**

#### 3.5 Leaderboard (`leaderboard.html`)
- Class selector: X | XII
- Top 10 table with ranks
- Podium for top 3 (animated)
- Badges: 🥇 Gold, 🥈 Silver, 🥉 Bronze
- Your position highlighted
- Filter: This Week | This Month | All Time

### 4. Teacher Pages

#### 4.1 Teacher Dashboard (`teacher-dashboard.html`)
**Header:** Same as student with teacher role

**Main Content:**
- **Welcome Card**
  - "Welcome, Prof. [Name]! 👨‍🏫"

- **Stats Row:**
  - Pending Evaluations: 5
  - Completed This Week: 12
  - Average Turnaround: 18 hrs
  - SLA Compliance: 98%

- **Pending Evaluations Queue**
  - Table: Student | Exam Type | Submitted | SLA Deadline | Priority | Action
  - Priority badges: 🔴 High (Centum) | 🟡 Normal
  - SLA countdown timer
  - "Start Evaluation" button

- **Quick Actions:**
  - Add New Question
  - View Question Bank
  - My Statistics

#### 4.2 Question Management (`questions.html`)
**Priority: MCQ Questions**

**Layout:**
- Left sidebar: Filters
  - Class: X | XII
  - Type: MCQ | VSA | SA
  - Unit: Dropdown
  - Difficulty: Easy | Medium | Hard
  - Status: Active | Archived

- Main area: Question list + Action buttons
  - "Add New Question" button (top right)

**Question List Table:**
- Columns: ID | Question Text (truncated) | Type | Unit | Difficulty | Actions
- Actions: Edit | Archive | Clone | Preview

**Add/Edit Question Form Modal:**
For MCQ:
- Class selection (X or XII)
- Unit dropdown (populated based on class)
- Topic dropdown (populated based on unit)
- Difficulty (easy/medium/hard)
- Marks (default: 1 for MCQ)
- **Question Text:** Rich text editor with LaTeX support
  - Toolbar: Bold, Italic, Insert Math (LaTeX)
  - Preview pane
- **Question Image:** Upload button
  - Image preview
  - S3 upload on submit
- **Options:**
  - Option A: Text input + LaTeX support
  - Option B: Text input + LaTeX support
  - Option C: Text input + LaTeX support
  - Option D: Text input + LaTeX support
- **Correct Answer:** Radio buttons (A/B/C/D)
- **Explanation:** Rich text editor
  - Detailed solution with LaTeX
- **Tags:** Comma-separated tags
- **Status:** Active | Archived

**Buttons:**
- Save Question
- Save & Add Another
- Cancel

**Validation:**
- All fields required
- At least one correct answer
- Explanation recommended but optional

#### 4.3 Evaluate Exam Page (`evaluate-exam.html`)
**Layout:**
- Left: Answer sheet images (scrollable)
  - Zoom controls
  - Annotation tools:
    - ✓ Tick stamp
    - ✗ Cross stamp
    - Pen tool
    - Undo/Redo
- Right: Question list with marking
  - Question text
  - Possible marks
  - Marks input field
  - Teacher comment textarea
  - Save & Next button

**Footer:**
- Total marks awarded: X/Y
- Submit Evaluation button (with confirmation)

### 5. Admin Pages

#### 5.1 Admin Dashboard (`admin-dashboard.html`)
- System statistics
- User management
- Subscription overview
- SLA compliance monitoring
- System configuration

## Animations & Interactions

### Micro-Animations
1. **Button Hover Effects**
   - Scale up slightly (1.05)
   - Add shadow
   - Gradient shift

2. **Card Hover**
   - Lift effect (translateY)
   - Glow border
   - Shadow increase

3. **Loading States**
   - Spinner on buttons during API calls
   - Skeleton screens for content loading
   - Progress bars for uploads

4. **Success/Error Feedback**
   - Toast notifications (slide in from top)
   - Checkmark animation on success
   - Shake animation on error

5. **Page Transitions**
   - Fade in on load
   - Smooth scroll behavior

### Scroll Animations
- Fade in as elements enter viewport
- Slide in from sides
- Counter animations (numbers count up)
- Progress bars animate to value

### Interactive Elements
1. **Stat Cards:** Animate numbers on hover
2. **Charts:** Animate on load with staggered delays
3. **Timeline:** Progressive reveal as you scroll
4. **Accordion:** Smooth expand/collapse
5. **Tabs:** Slide transition between content

## Responsive Design

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Mobile Adaptations
- Hamburger menu for navigation
- Stacked cards instead of grid
- Bottom navigation bar for main actions
- Swipeable carousels
- Touch-friendly button sizes (min 44px)

## Assets Required

### Images
1. **Landing Page:**
   - Hero illustration (student studying)
   - Feature icons (custom or Font Awesome)
   - How it works step illustrations
   - Testimonial avatars

2. **Class Pages:**
   - CBSE board logo
   - Unit icons
   - Sample question screenshots

3. **Dashboard:**
   - Default avatar images
   - Empty state illustrations
   - Achievement badges

### Icons
- Font Awesome 6 (CDN)
- Custom SVG icons for specific features

### Fonts
- Google Fonts: Poppins, Inter

## API Integration Points

### Authentication
- POST `/api/v1/register` - User registration
- POST `/api/v1/login` - User login
- POST `/api/v1/logout` - User logout
- GET `/api/v1/me` - Get current user

### Student
- GET `/api/v1/exams/templates` - Get available exams
- POST `/api/v1/exams/start` - Start new exam
- GET `/api/v1/exams/{id}` - Get exam instance
- POST `/api/v1/exams/{id}/mcq` - Submit MCQ answer
- POST `/api/v1/exams/{id}/submit` - Submit exam
- GET `/api/v1/analytics/dashboard/student` - Student dashboard data
- GET `/api/v1/analytics/leaderboard` - Leaderboard

### Teacher
- GET `/api/v1/questions` - List questions
- POST `/api/v1/questions` - Create question
- PUT `/api/v1/questions/{id}` - Update question
- DELETE `/api/v1/questions/{id}` - Delete question
- POST `/api/v1/questions/upload-image` - Upload question image
- GET `/api/v1/evaluations/pending` - Pending evaluations
- POST `/api/v1/evaluations/{id}/start` - Start evaluation
- POST `/api/v1/evaluations/{id}/marks` - Submit marks
- POST `/api/v1/evaluations/{id}/complete` - Complete evaluation

### Admin
- GET `/api/v1/subscriptions/stats` - Subscription statistics
- GET `/api/v1/evaluations/stats` - Evaluation statistics

## File Structure

```
frontend/
├── index.html                 # Landing page
├── class-x.html              # Class X page
├── class-xii.html            # Class XII page
├── about.html                # About page
├── login.html                # Login page
├── register.html             # Registration page
├── student/
│   ├── dashboard.html        # Student dashboard
│   ├── take-exam.html        # Exam taking interface
│   ├── exam-results.html     # Results page
│   ├── performance.html      # Analytics page
│   └── leaderboard.html      # Leaderboard
├── teacher/
│   ├── dashboard.html        # Teacher dashboard
│   ├── questions.html        # Question management
│   └── evaluate.html         # Evaluation interface
├── admin/
│   └── dashboard.html        # Admin dashboard
├── css/
│   ├── main.css              # Global styles
│   ├── landing.css           # Landing page styles
│   ├── auth.css              # Login/Register styles
│   ├── student.css           # Student page styles
│   ├── teacher.css           # Teacher page styles
│   └── admin.css             # Admin page styles
├── js/
│   ├── main.js               # Global utilities
│   ├── api.js                # API integration
│   ├── auth.js               # Authentication logic
│   ├── student-dashboard.js  # Student dashboard logic
│   ├── take-exam.js          # Exam taking logic
│   ├── questions.js          # Question management logic
│   └── evaluate.js           # Evaluation logic
├── assets/
│   ├── images/               # Images and illustrations
│   └── icons/                # Custom icons
└── README.md                 # Frontend documentation
```

## Implementation Priority

### Phase 1 (Current Sprint)
1. ✅ Landing page with animations
2. ✅ Login page for all roles
3. ✅ Student dashboard
4. ✅ MCQ exam interface (unit-wise + board exam)
5. ✅ Teacher question management (MCQ priority)

### Phase 2 (Future)
6. Student performance analytics
7. Leaderboard
8. Teacher evaluation interface
9. Answer sheet upload
10. Admin dashboard

### Phase 3 (Future)
11. Parent dashboard
12. VSA/SA question management
13. Advanced analytics
14. Mobile app considerations

## Development Guidelines

1. **Code Quality:**
   - Use semantic HTML5
   - BEM methodology for CSS class naming
   - ES6+ JavaScript features
   - Comments for complex logic

2. **Performance:**
   - Lazy load images
   - Minify CSS/JS for production
   - Use CDN for libraries
   - Optimize images (WebP format)

3. **Accessibility:**
   - ARIA labels for interactive elements
   - Keyboard navigation support
   - Alt text for images
   - Sufficient color contrast (WCAG AA)

4. **Browser Support:**
   - Chrome (latest 2 versions)
   - Firefox (latest 2 versions)
   - Safari (latest 2 versions)
   - Edge (latest 2 versions)

5. **Testing:**
   - Test on real devices
   - Cross-browser testing
   - Responsive design testing
   - API integration testing

---

**Ready to implement!** Let's start with Phase 1.
