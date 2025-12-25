# Mathvidya Frontend

Modern, student-friendly web interface for the Mathvidya CBSE Mathematics Practice Platform.

## 🎨 Design Philosophy

**Target Audience:** 15-18 year old students (Classes X & XII)

**Design Principles:**
- Clean, modern UI with vibrant colors
- Mobile-first responsive design
- Interactive animations and micro-interactions
- Instant visual feedback
- Gamification elements (badges, leaderboards, progress bars)
- Dark mode support (coming soon)

## 📁 Project Structure

```
frontend/
├── index.html                 # Landing page
├── login.html                 # Login page (all roles)
├── register.html             # Registration (TODO)
├── student/
│   ├── dashboard.html        # Student dashboard ✅
│   ├── take-exam.html        # MCQ exam interface ✅
│   ├── exam-results.html     # Results page (TODO)
│   ├── performance.html      # Analytics (TODO)
│   └── leaderboard.html      # Leaderboard (TODO)
├── teacher/
│   ├── dashboard.html        # Teacher dashboard (TODO)
│   ├── questions.html        # Question management ✅
│   └── evaluate.html         # Evaluation interface (TODO)
├── admin/
│   └── dashboard.html        # Admin dashboard (TODO)
├── css/
│   ├── main.css              # Global styles & design system ✅
│   ├── landing.css           # Landing page styles (TODO)
│   └── auth.css              # Login/Register styles (TODO)
├── js/
│   ├── main.js               # Global utilities ✅
│   ├── api.js                # API client ✅
│   ├── auth.js               # Authentication logic (TODO)
│   └── exam.js               # Exam logic (TODO)
└── assets/
    ├── images/               # Images and illustrations
    └── icons/                # Custom icons
```

## ✅ Implemented Pages

### 1. Landing Page (`index.html`)
**Features:**
- Hero section with gradient background
- Features grid with Font Awesome icons
- Pricing cards for 4 subscription plans
- How It Works section
- Responsive footer
- Smooth scroll animations

**CDN Dependencies:**
- Font Awesome 6.4.0
- Google Fonts (Poppins, Inter)

### 2. Login Page (`login.html`)
**Features:**
- Split-screen design
- Role selector tabs (Student/Teacher/Admin)
- Form validation with visual feedback
- Password visibility toggle
- Role-based redirect to dashboards
- Mobile-responsive

**Authentication:**
- Integrates with `/api/v1/login`
- JWT token storage in localStorage
- Auto-redirect for authenticated users

### 3. Student Dashboard (`student/dashboard.html`)
**Features:**
- Sticky header with profile dropdown
- Welcome card with greeting
- Quick stats (3 cards): Exams taken, Average score, Class rank
- Start New Exam section:
  - **Unit-Wise Practice:** Multi-select checkboxes for 13 CBSE units
  - **Board Exam:** Full CBSE pattern exam
- Recent exams table with status badges
- Empty state messaging
- Logout functionality

**API Integration:**
- `GET /api/v1/analytics/dashboard/student`
- `GET /api/v1/exams/templates`
- `POST /api/v1/exams/start`

### 4. Teacher Question Management (`teacher/questions.html`)
**Features:**
- Advanced filter bar (Type, Class, Unit, Difficulty)
- Questions table with CRUD actions
- Add/Edit modal with comprehensive form:
  - Question type selection (MCQ priority)
  - Class & unit dropdowns (cascading)
  - Difficulty selector
  - Question text with LaTeX mention
  - 4 MCQ options with correct answer selection
  - Explanation field
  - Image upload with drag-and-drop
- Confirmation dialogs for deletion
- Empty state when no questions found
- Dynamic unit population based on class

**API Integration:**
- `GET /api/v1/questions` (with filters)
- `POST /api/v1/questions`
- `PUT /api/v1/questions/{id}`
- `DELETE /api/v1/questions/{id}`
- `POST /api/v1/questions/upload-image`

### 5. MCQ Exam Interface (`student/take-exam.html`)
**Features:**
- **Header:**
  - Logo
  - Countdown timer with color-coded warnings
  - Submit button (always visible)

- **Question Display (Left 70%):**
  - Progress bar and text
  - Question card with number, marks, text
  - Image support
  - 4 large radio button options
  - Previous | Mark for Review | Next buttons

- **Question Palette (Right 30%, Sticky):**
  - Grid of question numbers
  - Color coding: Green (answered), Gray (unanswered), Orange (marked)
  - Live counts
  - Quick navigation

- **Advanced Features:**
  - Auto-save to API and localStorage
  - Timer with auto-submit at 0:00
  - Progress persistence on refresh
  - Keyboard shortcuts (arrows, A/B/C/D)
  - Submit confirmation modal
  - Auto-save every 60 seconds
  - Warn before leaving page

**API Integration:**
- `POST /api/v1/exams/{id}/mcq` (submit each answer)
- `POST /api/v1/exams/{id}/submit` (final submit)

## 🎨 Design System

### Color Palette
```css
--color-primary: #6366F1 (Indigo)
--color-secondary: #EC4899 (Pink)
--color-accent: #10B981 (Green - success)
--color-warning: #F59E0B (Amber)
--color-error: #EF4444 (Red)
```

### Typography
- **Headings:** Poppins (Google Font)
- **Body:** Inter (Google Font)
- **Monospace:** JetBrains Mono

### Components
All components follow consistent design patterns defined in `main.css`:
- Buttons (variants: primary, secondary, success, outline, ghost)
- Cards (with hover effects)
- Form inputs (with focus states)
- Badges (color-coded)
- Alerts (success, error, warning, info)
- Modals
- Toast notifications

### Animations
- fadeIn
- slideUp
- slideDown
- scaleIn
- Smooth transitions on all interactive elements

## 🔧 JavaScript Utilities

### API Client (`api.js`)
Centralized HTTP client for all backend communication:

**Authentication:**
- `register(userData)`
- `login(email, password)`
- `logout()`
- `getMe()`

**Exams:**
- `getAvailableExams()`
- `startExam(templateId, examType, units)`
- `getExamInstance(examId)`
- `submitMCQAnswer(examId, questionNumber, selectedOption)`
- `submitExam(examId)`

**Questions:**
- `getQuestions(filters)`
- `createQuestion(questionData)`
- `updateQuestion(questionId, questionData)`
- `deleteQuestion(questionId)`
- `uploadQuestionImage(file)`

**Analytics:**
- `getStudentDashboard()`
- `getLeaderboard(studentClass)`

**Subscriptions:**
- `getSubscriptionPlans()`
- `getMySubscription()`
- `checkExamEntitlement()`

### Utilities (`main.js`)

**Toast Notifications:**
```javascript
Toast.success('Exam submitted successfully!');
Toast.error('Login failed. Please try again.');
Toast.warning('You have only 5 exams remaining.');
Toast.info('New feature available!');
```

**Modals:**
```javascript
Modal.show(content, {
  title: 'Confirm Action',
  onConfirm: () => { /* action */ },
  confirmText: 'Yes',
  cancelText: 'No'
});

Modal.confirm('Are you sure?', () => { /* if yes */ });
```

**Validation:**
- `validateEmail(email)`
- `validatePassword(password)` (min 8 chars)
- `validateRequired(value)`

**Formatting:**
- `formatDate(dateString)` → "24 Dec, 2025"
- `formatDateTime(dateString)` → "24 Dec, 2025, 14:30"
- `formatScore(score, total)` → "75/80 (93.8%)"

**Loading States:**
- `showLoading(button)` - Disable button and show spinner
- `hideLoading(button)` - Re-enable and restore text

**Authentication Helpers:**
- `getUser()` - Get current user from localStorage
- `getToken()` - Get JWT token
- `isAuthenticated()` - Check if user is logged in
- `getUserRole()` - Get user role (student/teacher/admin)

**Scroll Animations:**
- `observeElements(selector, className)` - Trigger animations on scroll

## 🔐 Authentication Flow

1. **Login:**
   - User enters email/password and selects role
   - `api.login()` sends credentials to `/api/v1/login`
   - Backend returns JWT token and user object
   - Token stored in `localStorage` as `auth_token`
   - User object stored as `user`
   - Redirect based on role:
     - student → `student/dashboard.html`
     - teacher → `teacher/dashboard.html`
     - admin → `admin/dashboard.html`

2. **Protected Pages:**
   - Check `isAuthenticated()` on page load
   - Redirect to login if not authenticated
   - Verify role matches page requirements
   - Include token in all API requests via Authorization header

3. **Logout:**
   - Call `api.logout()`
   - Clear `auth_token` and `user` from localStorage
   - Redirect to login page

## 📱 Responsive Breakpoints

```css
Mobile: < 768px
Tablet: 768px - 1024px
Desktop: > 1024px
```

**Mobile Adaptations:**
- Hamburger menu for navigation
- Stacked cards instead of grid
- Bottom navigation for main actions
- Swipeable carousels
- Touch-friendly button sizes (min 44px)

## 🚀 Running the Frontend

### Option 1: Local Server (Recommended)
```bash
# Using Python (if installed)
cd frontend
python -m http.server 8080

# Using Node.js (if installed)
npx http-server -p 8080

# Using PHP (if installed)
php -S localhost:8080
```

Then open: `http://localhost:8080`

### Option 2: Live Server (VS Code Extension)
1. Install "Live Server" extension in VS Code
2. Right-click `index.html`
3. Select "Open with Live Server"

### Option 3: Direct File Open
Open `index.html` directly in browser (CORS issues may occur with API calls)

## 🔗 Backend Integration

**Backend API:** `http://localhost:8000/api/v1`

Ensure backend is running before using the frontend:
```bash
cd ../backend
source mvenv/Scripts/activate  # Windows Git Bash
uvicorn main:app --reload
```

**API Documentation:** `http://localhost:8000/api/docs`

## ✨ Future Enhancements (TODO)

### Pages
- [ ] Registration page with multi-step form
- [ ] Student exam results page
- [ ] Student performance analytics page
- [ ] Student leaderboard page
- [ ] Teacher dashboard
- [ ] Teacher evaluation interface
- [ ] Admin dashboard
- [ ] Parent dashboard

### Features
- [ ] MathJax integration for LaTeX rendering
- [ ] Dark mode toggle
- [ ] VSA/SA question types (teacher)
- [ ] Answer sheet upload (student)
- [ ] Image annotation tools (teacher)
- [ ] Real-time leaderboard updates
- [ ] Push notifications
- [ ] Offline support with service workers
- [ ] PWA capabilities
- [ ] Advanced analytics charts (Chart.js)

### Technical
- [ ] Add loading skeletons
- [ ] Implement proper error boundaries
- [ ] Add E2E tests with Playwright
- [ ] Optimize images (WebP format)
- [ ] Add service worker for caching
- [ ] Implement Redux/Zustand for state management
- [ ] Migrate to React/Vue (optional)
- [ ] Add TypeScript

## 🎯 CBSE Units Reference

### Class X
1. Number Systems
2. Algebra
3. Coordinate Geometry
4. Geometry
5. Trigonometry
6. Mensuration
7. Statistics & Probability

### Class XII
1. Relations and Functions
2. Inverse Trigonometric Functions
3. Matrices
4. Determinants
5. Continuity and Differentiability
6. Applications of Derivatives
7. Integrals
8. Applications of Integrals
9. Differential Equations
10. Vectors
11. Three Dimensional Geometry
12. Linear Programming
13. Probability

## 📝 Notes

- All pages use Google Fonts loaded via CDN (no font files needed)
- Font Awesome 6 icons loaded via CDN (no icon files needed)
- No build process required - pure HTML/CSS/JS
- API responses follow Pydantic schemas from backend
- All timestamps in ISO format from backend
- Image uploads go to S3 (signed URLs returned)
- Subscription validation happens on backend
- RBAC enforced at API level

## 🐛 Known Issues

1. **CORS:** If running frontend with `file://` protocol, API calls may fail. Use local server.
2. **LaTeX:** MathJax not yet integrated - LaTeX displays as raw text.
3. **Pagination:** Question list and recent exams don't have pagination yet (loads all).
4. **Image Upload:** No client-side image compression yet.

## 📄 License

Copyright © 2025 Mathvidya. All rights reserved.

---

**Built with ❤️ for CBSE Students**
