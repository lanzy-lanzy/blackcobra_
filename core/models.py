from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Belt(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='#000000')
    order = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Trainee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    belt = models.ForeignKey(Belt, on_delete=models.SET_NULL, null=True)
    contact_number = models.CharField(max_length=20)
    address = models.TextField()
    join_date = models.DateField(auto_now_add=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)  # Requires admin approval

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def win_rate(self):
        """Calculate win percentage"""
        total_matches = self.matches_as_trainee1.count() + self.matches_as_trainee2.count()
        if total_matches == 0:
            return 0
        wins = self.matches_won.count()
        return (wins / total_matches) * 100
    
    @property
    def outstanding_balance(self):
        """Calculate total unpaid amount"""
        return self.payments.filter(paid=False).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('tournament', 'Tournament'),
        ('training', 'Training Session'),
        ('seminar', 'Seminar'),
        ('grading', 'Belt Grading')
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, default='training')
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.start_date > timezone.now()
    
    @property
    def participant_count(self):
        """Count registered participants"""
        trainee_ids = set()
        for match in self.matches.all():
            trainee_ids.add(match.trainee1.id)
            trainee_ids.add(match.trainee2.id)
        return len(trainee_ids)

class Match(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='matches')
    trainee1 = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='matches_as_trainee1')
    trainee2 = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='matches_as_trainee2')
    winner = models.ForeignKey(Trainee, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    score1 = models.PositiveIntegerField(default=0)
    score2 = models.PositiveIntegerField(default=0)
    judge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'groups__name': "Judge"})
    match_time = models.DateTimeField()

    def __str__(self):
        return f"{self.trainee1} vs {self.trainee2} at {self.event}"

class Payment(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment of {self.amount} for {self.trainee} on {self.date}"

class Promotion(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='promotions')
    belt_from = models.ForeignKey(Belt, on_delete=models.SET_NULL, null=True, related_name='promotions_from')
    belt_to = models.ForeignKey(Belt, on_delete=models.SET_NULL, null=True, related_name='promotions_to')
    date = models.DateField()

    def __str__(self):
        return f"{self.trainee} promoted from {self.belt_from} to {self.belt_to} on {self.date}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('match', 'Match Notification'),
        ('payment', 'Payment Reminder'),
        ('promotion', 'Promotion'),
        ('event', 'Event Update')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} for {self.user.username}"


class DashboardStat(models.Model):
    stat_type = models.CharField(max_length=50, unique=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.stat_type} - Updated: {self.updated_at}"