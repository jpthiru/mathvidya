"""Pydantic schemas for request/response validation"""

from .auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
]

from .exam import (
    ExamTemplateResponse,
    StartExamRequest,
    QuestionResponse,
    ExamInstanceResponse,
    SubmitMCQRequest,
    MCQResultResponse,
    UploadAnswerSheetRequest,
    UploadAnswerSheetResponse,
    ConfirmUploadRequest,
    DeclareUnansweredRequest,
    SubmitExamRequest,
    ExamHistoryResponse,
    ExamStatusResponse,
    AvailableTemplatesResponse
)

__all__ += [
    "ExamTemplateResponse",
    "StartExamRequest",
    "QuestionResponse",
    "ExamInstanceResponse",
    "SubmitMCQRequest",
    "MCQResultResponse",
    "UploadAnswerSheetRequest",
    "UploadAnswerSheetResponse",
    "ConfirmUploadRequest",
    "DeclareUnansweredRequest",
    "SubmitExamRequest",
    "ExamHistoryResponse",
    "ExamStatusResponse",
    "AvailableTemplatesResponse",
]

from .question import (
    CreateQuestionRequest,
    UpdateQuestionRequest,
    QuestionDetailResponse,
    QuestionSummaryResponse,
    QuestionListResponse,
    BulkQuestionUploadRequest,
    BulkUploadResponse,
    QuestionFilterRequest,
    QuestionStatsResponse,
    UploadQuestionImageRequest,
    UploadQuestionImageResponse,
    ArchiveQuestionRequest,
    CloneQuestionRequest
)

__all__ += [
    "CreateQuestionRequest",
    "UpdateQuestionRequest",
    "QuestionDetailResponse",
    "QuestionSummaryResponse",
    "QuestionListResponse",
    "BulkQuestionUploadRequest",
    "BulkUploadResponse",
    "QuestionFilterRequest",
    "QuestionStatsResponse",
    "UploadQuestionImageRequest",
    "UploadQuestionImageResponse",
    "ArchiveQuestionRequest",
    "CloneQuestionRequest",
]

from .evaluation import (
    QuestionMarkRequest,
    AnnotationStamp,
    PageAnnotation,
    StartEvaluationRequest,
    SubmitMarksRequest,
    CompleteEvaluationRequest,
    EvaluationDetailResponse,
    EvaluationSummaryResponse,
    EvaluationListResponse,
    QuestionMarkResponse,
    EvaluationProgressResponse,
    AssignEvaluationRequest,
    AssignEvaluationResponse,
    PendingEvaluationFilterRequest,
    TeacherWorkloadResponse,
    EvaluationStatsResponse,
    UploadAnnotatedImageRequest,
    UploadAnnotatedImageResponse,
    BulkAssignEvaluationsRequest,
    BulkAssignEvaluationsResponse
)

__all__ += [
    "QuestionMarkRequest",
    "AnnotationStamp",
    "PageAnnotation",
    "StartEvaluationRequest",
    "SubmitMarksRequest",
    "CompleteEvaluationRequest",
    "EvaluationDetailResponse",
    "EvaluationSummaryResponse",
    "EvaluationListResponse",
    "QuestionMarkResponse",
    "EvaluationProgressResponse",
    "AssignEvaluationRequest",
    "AssignEvaluationResponse",
    "PendingEvaluationFilterRequest",
    "TeacherWorkloadResponse",
    "EvaluationStatsResponse",
    "UploadAnnotatedImageRequest",
    "UploadAnnotatedImageResponse",
    "BulkAssignEvaluationsRequest",
    "BulkAssignEvaluationsResponse",
]

from .analytics import (
    StudentDashboardResponse,
    ParentDashboardResponse,
    TeacherDashboardResponse,
    AdminDashboardResponse,
    LeaderboardResponse,
    StudentReportRequest,
    StudentReportResponse,
    ClassReportRequest,
    ClassReportResponse,
    TeacherReportRequest,
    TeacherReportResponse,
    SystemReportRequest,
    SystemReportResponse,
    CompareStudentsRequest,
    StudentComparison
)

__all__ += [
    "StudentDashboardResponse",
    "ParentDashboardResponse",
    "TeacherDashboardResponse",
    "AdminDashboardResponse",
    "LeaderboardResponse",
    "StudentReportRequest",
    "StudentReportResponse",
    "ClassReportRequest",
    "ClassReportResponse",
    "TeacherReportRequest",
    "TeacherReportResponse",
    "SystemReportRequest",
    "SystemReportResponse",
    "CompareStudentsRequest",
    "StudentComparison",
]

from .subscription import (
    SubscriptionPlanListResponse,
    SubscriptionPlanResponse,
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
    SubscriptionResponse,
    SubscriptionUsageResponse,
    FeatureAccessResponse,
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
    SubscriptionStatsResponse,
    GrantTrialRequest,
    GrantTrialResponse
)

__all__ += [
    "SubscriptionPlanListResponse",
    "SubscriptionPlanResponse",
    "CreateSubscriptionRequest",
    "UpdateSubscriptionRequest",
    "SubscriptionResponse",
    "SubscriptionUsageResponse",
    "FeatureAccessResponse",
    "CancelSubscriptionRequest",
    "CancelSubscriptionResponse",
    "SubscriptionStatsResponse",
    "GrantTrialRequest",
    "GrantTrialResponse",
]

from .notification import (
    NotificationType,
    NotificationPriority,
    NotificationCategory,
    CreateNotificationRequest,
    NotificationResponse,
    NotificationListResponse,
    MarkNotificationReadRequest,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    SendEmailRequest,
    EmailResponse,
    NotificationStatsResponse,
    EvaluationCompleteAlert,
    SLAReminderAlert,
    SLABreachAlert,
    SubscriptionExpiringAlert,
    ExamLimitWarningAlert
)

__all__ += [
    "NotificationType",
    "NotificationPriority",
    "NotificationCategory",
    "CreateNotificationRequest",
    "NotificationResponse",
    "NotificationListResponse",
    "MarkNotificationReadRequest",
    "NotificationPreferencesRequest",
    "NotificationPreferencesResponse",
    "SendEmailRequest",
    "EmailResponse",
    "NotificationStatsResponse",
    "EvaluationCompleteAlert",
    "SLAReminderAlert",
    "SLABreachAlert",
    "SubscriptionExpiringAlert",
    "ExamLimitWarningAlert",
]
