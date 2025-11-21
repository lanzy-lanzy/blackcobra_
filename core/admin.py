from django.contrib import admin
from .models import Belt, Trainee, Event, Match, Payment, Promotion, Notification, DashboardStat

@admin.register(Belt)
class BeltAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)

@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin):
    list_display = ('user', 'belt', 'join_date', 'is_active')
    list_filter = ('belt', 'join_date', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'emergency_contact')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'location', 'is_published')
    list_filter = ('event_type', 'is_published', 'start_date')
    search_fields = ('name', 'location')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'trainee1', 'trainee2', 'winner', 'match_time')
    list_filter = ('event', 'match_time')
    search_fields = ('trainee1__user__username', 'trainee2__user__username', 'event__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'amount', 'date', 'paid')
    list_filter = ('paid', 'date')
    search_fields = ('trainee__user__username',)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'belt_from', 'belt_to', 'date')
    list_filter = ('date',)
    search_fields = ('trainee__user__username',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)

@admin.register(DashboardStat)
class DashboardStatAdmin(admin.ModelAdmin):
    list_display = ('stat_type', 'updated_at')
    readonly_fields = ('updated_at',)
