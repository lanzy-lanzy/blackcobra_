from django.urls import path
from .views import (
    home,
    custom_login,
    register,
    admin_dashboard, 
    judge_dashboard, 
    trainee_dashboard,
    upcoming_matches,
    recent_matches,
    trainee_profile,
    trainee_matches,
    trainee_payments,
    notifications,
    mark_notification_read,
    mark_all_notifications_read,
    dashboard_statistics,
    trainee_list,
    trainee_create,
    trainee_update,
    trainee_delete,
    trainee_delete_confirm,
    event_list,
    event_calendar_data,
    event_create,
    event_update,
    event_delete,
    event_delete_confirm,
    event_detail,
    match_scoring,
    match_update_score,
    match_complete,
    match_complete_form,
    promotion_list,
    promotion_create,
    promotion_history,
    payment_list,
    payment_create,
    payment_mark_paid,
    payment_reports,
    reports_dashboard,
    api_chart_data,
    pending_trainees,
    approve_trainee,
    trainee_events_list,
    trainee_event_detail,
    event_register,
    event_unregister
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', custom_login, name='custom_login'),
    path('register/', register, name='register'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/judge/', judge_dashboard, name='judge_dashboard'),
    path('dashboard/trainee/', trainee_dashboard, name='trainee_dashboard'),

    # Partials for Judge Dashboard
    path('matches/upcoming/', upcoming_matches, name='upcoming_matches'),
    path('matches/recent/', recent_matches, name='recent_matches'),

    # Partials for Trainee Dashboard
    path('trainee/profile/', trainee_profile, name='trainee_profile'),
    path('trainee/matches/', trainee_matches, name='trainee_matches'),
    path('trainee/payments/', trainee_payments, name='trainee_payments'),

    # Notifications
    path('notifications/', notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Admin Dashboard Statistics
    path('api/dashboard/statistics/', dashboard_statistics, name='dashboard_statistics'),
    
    # Trainee Management
    path('trainees/', trainee_list, name='trainee_list'),
    path('trainees/create/', trainee_create, name='trainee_create'),
    path('trainees/<int:trainee_id>/update/', trainee_update, name='trainee_update'),
    path('trainees/<int:trainee_id>/delete/', trainee_delete, name='trainee_delete'),
    path('trainees/<int:trainee_id>/delete/confirm/', trainee_delete_confirm, name='trainee_delete_confirm'),
    path('trainees/pending/', pending_trainees, name='pending_trainees'),
    path('trainees/<int:trainee_id>/approve/', approve_trainee, name='approve_trainee'),
    
    # Event Management
    path('events/', event_list, name='event_list'),
    path('events/calendar/', event_calendar_data, name='event_calendar_data'),
    path('events/create/', event_create, name='event_create'),
    path('events/<int:event_id>/update/', event_update, name='event_update'),
    path('events/<int:event_id>/delete/', event_delete, name='event_delete'),
    path('events/<int:event_id>/delete/confirm/', event_delete_confirm, name='event_delete_confirm'),
    path('events/<int:event_id>/', event_detail, name='event_detail'),
    
    # Match Scoring
    path('matches/<int:match_id>/score/', match_scoring, name='match_scoring'),
    path('matches/<int:match_id>/update-score/', match_update_score, name='match_update_score'),
    path('matches/<int:match_id>/complete/', match_complete, name='match_complete'),
    path('matches/<int:match_id>/complete/form/', match_complete_form, name='match_complete_form'),

    # Promotion Management
    path('promotions/', promotion_list, name='promotion_list'),
    path('promotions/create/<int:trainee_id>/', promotion_create, name='promotion_create'),
    path('promotions/history/', promotion_history, name='promotion_history'),

    # Payment Management
    path('payments/', payment_list, name='payment_list'),
    path('payments/create/', payment_create, name='payment_create'),
    path('payments/<int:payment_id>/mark-paid/', payment_mark_paid, name='payment_mark_paid'),
    path('payments/reports/', payment_reports, name='payment_reports'),
    
    # Reports & Analytics
    path('reports/', reports_dashboard, name='reports_dashboard'),
    path('api/chart-data/', api_chart_data, name='api_chart_data'),
    
    # Trainee Event Registration
    path('trainee/events/', trainee_events_list, name='trainee_events_list'),
    path('trainee/events/<int:event_id>/', trainee_event_detail, name='trainee_event_detail'),
    path('trainee/events/<int:event_id>/register/', event_register, name='event_register'),
    path('trainee/events/<int:event_id>/unregister/', event_unregister, name='event_unregister'),
]
