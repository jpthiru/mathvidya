"""
Analytics Schemas

Pydantic models for dashboards, reports, and performance analytics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ==================== Student Analytics ====================

class UnitPerformance(BaseModel):
    """Performance in a specific unit"""
    unit: str
    total_questions: int
    questions_attempted: int
    questions_correct: int

    total_marks: float
    marks_obtained: float
    percentage: float

    # Question type breakdown
    mcq_correct: int
    mcq_total: int
    vsa_marks: float
    vsa_total: float
    sa_marks: float
    sa_total: float
    la_marks: float
    la_total: float

    # Difficulty analysis
    easy_percentage: Optional[float]
    medium_percentage: Optional[float]
    hard_percentage: Optional[float]


class TopicPerformance(BaseModel):
    """Performance in a specific topic"""
    topic: str
    unit: str
    questions_attempted: int
    percentage: float
    strength_level: str = Field(..., description="strong, average, weak")


class QuestionTypeAnalysis(BaseModel):
    """Performance by question type"""
    question_type: str  # MCQ, VSA, SA, LA
    total_questions: int
    marks_possible: float
    marks_obtained: float
    percentage: float
    avg_marks_per_question: float


class ExamSummary(BaseModel):
    """Summary of a single exam"""
    exam_instance_id: str
    exam_type: str
    class_level: str

    started_at: datetime
    submitted_at: Optional[datetime]
    evaluated_at: Optional[datetime]

    total_marks: int
    mcq_score: float
    manual_score: float
    total_score: float
    percentage: float

    status: str
    time_taken_minutes: Optional[int]


class PerformanceTrend(BaseModel):
    """Performance trend over time"""
    exam_instance_id: str
    exam_date: datetime
    percentage: float
    total_score: float


class StrengthWeakness(BaseModel):
    """Identified strengths and weaknesses"""
    strengths: List[TopicPerformance] = Field(
        default_factory=list,
        description="Topics with >75% performance"
    )
    average: List[TopicPerformance] = Field(
        default_factory=list,
        description="Topics with 50-75% performance"
    )
    weaknesses: List[TopicPerformance] = Field(
        default_factory=list,
        description="Topics with <50% performance"
    )


class BoardScorePrediction(BaseModel):
    """Predicted board exam score"""
    predicted_percentage: float
    confidence_level: str = Field(..., description="high, medium, low")

    # Factors
    recent_exam_avg: float
    improvement_rate: float
    exams_analyzed: int

    # Range
    min_predicted: float
    max_predicted: float

    # Recommendations
    focus_areas: List[str] = Field(default_factory=list)


class StudentDashboardResponse(BaseModel):
    """Complete student dashboard"""
    student_id: str
    student_name: str
    class_level: str

    # Overall statistics
    total_exams: int
    exams_completed: int
    exams_evaluated: int

    overall_percentage: Optional[float]
    overall_rank: Optional[int]
    total_students: Optional[int]

    # Recent performance
    recent_exams: List[ExamSummary] = Field(
        default_factory=list,
        description="Last 5 evaluated exams"
    )

    # Unit-wise analysis
    unit_performance: List[UnitPerformance] = Field(default_factory=list)

    # Question type analysis
    question_type_analysis: List[QuestionTypeAnalysis] = Field(default_factory=list)

    # Strengths and weaknesses
    strength_weakness: Optional[StrengthWeakness]

    # Trends
    performance_trend: List[PerformanceTrend] = Field(
        default_factory=list,
        description="Last 10 exams"
    )

    # Prediction
    board_prediction: Optional[BoardScorePrediction]


# ==================== Parent Analytics ====================

class ParentDashboardResponse(BaseModel):
    """Parent dashboard (read-only view of student)"""
    parent_id: str
    parent_name: str

    # Children
    students: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of linked students with basic info"
    )

    # Selected student dashboard
    selected_student_dashboard: Optional[StudentDashboardResponse]


# ==================== Teacher Analytics ====================

class ClassPerformanceSummary(BaseModel):
    """Performance summary for a class"""
    class_level: str
    total_students: int
    exams_evaluated: int

    avg_percentage: float
    highest_percentage: float
    lowest_percentage: float

    # Distribution
    above_90: int
    between_75_90: int
    between_60_75: int
    between_40_60: int
    below_40: int


class QuestionDifficultyAnalysis(BaseModel):
    """Question difficulty analysis"""
    question_id: str
    question_text: str
    question_type: str
    unit: str

    times_used: int
    avg_marks_obtained: float
    marks_possible: float
    success_rate: float

    difficulty_rating: str = Field(..., description="too_easy, appropriate, too_hard")


class EvaluationPerformance(BaseModel):
    """Teacher's evaluation performance"""
    total_evaluations: int
    completed_on_time: int
    completed_late: int
    pending: int

    avg_completion_hours: float
    sla_compliance_rate: float

    fastest_evaluation_hours: Optional[float]
    slowest_evaluation_hours: Optional[float]


class TeacherDashboardResponse(BaseModel):
    """Complete teacher dashboard"""
    teacher_id: str
    teacher_name: str

    # Workload (from evaluation service)
    pending_evaluations: int
    in_progress_evaluations: int
    overdue_evaluations: int

    # Performance
    evaluation_performance: EvaluationPerformance

    # Class insights
    class_performance: List[ClassPerformanceSummary] = Field(default_factory=list)

    # Question bank contributions
    questions_created: int
    questions_active: int

    # Upcoming deadlines
    upcoming_deadlines: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== Admin Analytics ====================

class SystemOverview(BaseModel):
    """System-wide overview"""
    total_users: int
    total_students: int
    total_teachers: int
    total_parents: int

    active_subscriptions: int

    total_exams: int
    exams_in_progress: int
    exams_pending_evaluation: int
    exams_evaluated: int

    total_questions: int
    active_questions: int


class SubscriptionBreakdown(BaseModel):
    """Subscription plan distribution"""
    plan_name: str
    active_count: int
    revenue: float
    avg_exams_per_month: float


class SLACompliance(BaseModel):
    """SLA compliance metrics"""
    total_evaluations: int
    on_time: int
    breached: int
    compliance_rate: float

    avg_completion_hours: float

    # By plan
    centum_compliance_rate: Optional[float]
    other_plans_compliance_rate: Optional[float]


class PopularUnits(BaseModel):
    """Most practiced units"""
    unit: str
    class_level: str
    total_exams: int
    avg_percentage: float


class AdminDashboardResponse(BaseModel):
    """Complete admin dashboard"""
    # System overview
    system_overview: SystemOverview

    # Subscriptions
    subscription_breakdown: List[SubscriptionBreakdown] = Field(default_factory=list)

    # Performance
    overall_avg_percentage: float

    # Class-wise performance
    class_performance: List[ClassPerformanceSummary] = Field(default_factory=list)

    # SLA metrics
    sla_compliance: SLACompliance

    # Popular units
    popular_units: List[PopularUnits] = Field(default_factory=list)

    # Teacher performance
    top_teachers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 teachers by SLA compliance"
    )

    # Recent activity
    recent_registrations: int
    recent_exams: int


# ==================== Reports ====================

class StudentReportRequest(BaseModel):
    """Request for student performance report"""
    student_id: str
    start_date: Optional[datetime] = Field(None, description="Filter from date")
    end_date: Optional[datetime] = Field(None, description="Filter to date")
    include_detailed_analysis: bool = Field(True, description="Include unit/topic breakdown")


class StudentReportResponse(BaseModel):
    """Comprehensive student performance report"""
    student_id: str
    student_name: str
    class_level: str

    report_period: str
    generated_at: datetime

    # Summary
    exams_taken: int
    overall_percentage: float
    overall_rank: Optional[int]

    # Detailed metrics
    unit_performance: List[UnitPerformance] = Field(default_factory=list)
    strength_weakness: StrengthWeakness
    question_type_analysis: List[QuestionTypeAnalysis] = Field(default_factory=list)

    # Trends
    performance_trend: List[PerformanceTrend] = Field(default_factory=list)
    improvement_rate: Optional[float]

    # Prediction
    board_prediction: Optional[BoardScorePrediction]

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)


class ClassReportRequest(BaseModel):
    """Request for class performance report"""
    class_level: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ClassReportResponse(BaseModel):
    """Class performance report"""
    class_level: str
    report_period: str
    generated_at: datetime

    # Summary
    total_students: int
    total_exams: int
    avg_percentage: float

    # Distribution
    performance_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Grade distribution"
    )

    # Unit analysis
    unit_performance: List[UnitPerformance] = Field(default_factory=list)

    # Top performers
    top_students: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 10 students"
    )

    # Weak areas
    weak_topics: List[TopicPerformance] = Field(default_factory=list)


class TeacherReportRequest(BaseModel):
    """Request for teacher performance report"""
    teacher_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TeacherReportResponse(BaseModel):
    """Teacher performance report"""
    teacher_id: str
    teacher_name: str
    report_period: str
    generated_at: datetime

    # Evaluation metrics
    total_evaluations: int
    avg_completion_hours: float
    sla_compliance_rate: float

    # Question contributions
    questions_created: int
    questions_active: int

    # Student outcomes
    students_evaluated: int
    avg_student_improvement: Optional[float]


class SystemReportRequest(BaseModel):
    """Request for system-wide report"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SystemReportResponse(BaseModel):
    """System-wide analytics report"""
    report_period: str
    generated_at: datetime

    # User metrics
    total_users: int
    new_registrations: int
    active_users: int

    # Subscription metrics
    active_subscriptions: int
    subscription_breakdown: List[SubscriptionBreakdown] = Field(default_factory=list)

    # Exam metrics
    total_exams: int
    avg_percentage: float

    # SLA metrics
    sla_compliance: SLACompliance

    # Question bank
    total_questions: int
    questions_by_type: Dict[str, int] = Field(default_factory=dict)

    # Performance trends
    class_performance: List[ClassPerformanceSummary] = Field(default_factory=list)


# ==================== Leaderboard ====================

class LeaderboardEntry(BaseModel):
    """Single leaderboard entry"""
    rank: int
    student_id: str
    student_name: str
    class_level: str

    total_exams: int
    avg_percentage: float
    total_score: float

    # Badge/achievement (if any)
    badge: Optional[str] = None


class LeaderboardResponse(BaseModel):
    """Leaderboard (Top 10)"""
    class_level: str
    period: str = Field(..., description="monthly, quarterly, all-time")

    entries: List[LeaderboardEntry] = Field(
        default_factory=list,
        description="Top 10 students"
    )

    # Current user position (if not in top 10)
    current_user_rank: Optional[int]
    current_user_entry: Optional[LeaderboardEntry]

    eligibility_criteria: str = Field(
        default="Premium and Centum plan subscribers only",
        description="Who can view leaderboard"
    )

    last_updated: datetime


# ==================== Comparison ====================

class CompareStudentsRequest(BaseModel):
    """Request to compare two students"""
    student_id_1: str
    student_id_2: str


class StudentComparison(BaseModel):
    """Comparison between two students"""
    student_1: Dict[str, Any]
    student_2: Dict[str, Any]

    # Comparative metrics
    avg_percentage_diff: float
    rank_diff: Optional[int]

    # Unit comparison
    unit_comparison: List[Dict[str, Any]] = Field(default_factory=list)

    # Strength/weakness comparison
    student_1_stronger_in: List[str] = Field(default_factory=list)
    student_2_stronger_in: List[str] = Field(default_factory=list)
