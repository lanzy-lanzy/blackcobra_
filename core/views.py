from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
from .models import Match, Trainee, Payment, Event, Promotion, DashboardStat
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import json
from django.db import models
from .forms import TraineeForm, EventForm, PaymentForm, PromotionForm
from django.views.decorators.http import require_http_methods
from .utils import create_notification

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def is_judge(user):
    return user.groups.filter(name='Judge').exists()

def is_trainee(user):
    return user.groups.filter(name='Trainee').exists()

def custom_login(request):
    """Custom login view with role-based redirection"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if trainee is approved
            if user.groups.filter(name='Trainee').exists():
                try:
                    trainee = Trainee.objects.get(user=user)
                    if not trainee.is_approved:
                        messages.warning(request, 'Your account is pending approval. Please wait for administrator confirmation.')
                        return render(request, 'registration/login.html')
                except Trainee.DoesNotExist:
                    pass
            
            login(request, user)
            
            # Redirect based on user role
            if user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')
            elif user.groups.filter(name='Judge').exists():
                return redirect('judge_dashboard')
            elif user.groups.filter(name='Trainee').exists():
                return redirect('trainee_dashboard')
            else:
                messages.warning(request, 'No role assigned. Please contact administrator.')
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'registration/login.html')
    
    return render(request, 'registration/login.html')

def register(request):
    """Registration view for new trainees"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        contact_number = request.POST.get('contact_number')
        address = request.POST.get('address')
        
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'registration/register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Add to Trainee group
            trainee_group, _ = Group.objects.get_or_create(name='Trainee')
            user.groups.add(trainee_group)
            
            # Get white belt (first belt)
            from .models import Belt
            white_belt = Belt.objects.filter(order=1).first()
            
            # Create trainee profile (not approved by default)
            Trainee.objects.create(
                user=user,
                date_of_birth=date_of_birth,
                belt=white_belt,
                contact_number=contact_number,
                address=address,
                is_approved=False,  # Requires admin approval
                is_active=False  # Inactive until approved
            )
            
            messages.success(request, 'Registration successful! Your account is pending approval from an administrator.')
            return redirect('custom_login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'registration/register.html')
    
    return render(request, 'registration/register.html')

def home(request):
    """Home page - redirect authenticated users to their dashboard"""
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_judge(request.user):
            return redirect('judge_dashboard')
        elif is_trainee(request.user):
            return redirect('trainee_dashboard')
    return render(request, 'home.html')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
@user_passes_test(is_judge)
def judge_dashboard(request):
    return render(request, 'judge_dashboard.html')

@login_required
@user_passes_test(is_trainee)
def trainee_dashboard(request):
    trainee = get_object_or_404(Trainee.objects.select_related('belt', 'user'), user=request.user)
    
    # Matches - optimized with select_related
    matches = Match.objects.filter(
        Q(trainee1=trainee) | Q(trainee2=trainee)
    ).select_related(
        'event', 'winner', 'trainee1', 'trainee2', 'trainee1__belt', 'trainee2__belt'
    ).order_by('-match_time')
    
    # Calculate stats
    now = timezone.now()
    completed_matches = matches.filter(match_time__lt=now)
    total_completed = completed_matches.count()
    wins = completed_matches.filter(winner=trainee).count()
    losses = total_completed - wins
    
    win_rate = 0
    if total_completed > 0:
        win_rate = (wins / total_completed) * 100
        
    # Upcoming matches
    upcoming_matches = matches.filter(match_time__gte=now).order_by('match_time')[:5]
    
    # Recent matches history
    recent_matches = completed_matches.order_by('-match_time')[:5]

    # Payments - optimized
    all_payments = Payment.objects.filter(trainee=trainee).select_related('trainee').order_by('-date')
    pending_payments_count = all_payments.filter(paid=False).count()
    recent_payments = all_payments[:5]
    
    context = {
        'trainee': trainee,
        'total_matches': total_completed,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'upcoming_matches': upcoming_matches,
        'recent_matches': recent_matches,
        'recent_payments': recent_payments,
        'pending_payments_count': pending_payments_count,
    }
    
    return render(request, 'trainee_dashboard.html', context)

@login_required
@user_passes_test(is_judge)
def upcoming_matches(request):
    """
    Display upcoming matches for the judge with countdown timers.
    Highlights matches within 15 minutes.
    """
    now = timezone.now()
    matches = Match.objects.filter(
        judge=request.user, 
        match_time__gte=now
    ).select_related('trainee1', 'trainee2', 'event').order_by('match_time')
    
    # Add time_until and is_imminent flags to each match
    for match in matches:
        time_diff = match.match_time - now
        match.time_until = time_diff
        match.is_imminent = time_diff.total_seconds() <= 900  # 15 minutes
    
    return render(request, 'partials/upcoming_matches.html', {'matches': matches})

@login_required
@user_passes_test(is_judge)
def recent_matches(request):
    """
    Display recent matches for the judge showing results.
    """
    matches = Match.objects.filter(
        judge=request.user, 
        match_time__lt=timezone.now()
    ).select_related('trainee1', 'trainee2', 'winner', 'event').order_by('-match_time')[:10]
    
    return render(request, 'partials/recent_matches.html', {'matches': matches})

@login_required
@user_passes_test(is_trainee)
def trainee_profile(request):
    trainee = Trainee.objects.get(user=request.user)
    return render(request, 'partials/trainee_profile.html', {'trainee': trainee})

@login_required
@user_passes_test(is_trainee)
def trainee_matches(request):
    trainee = Trainee.objects.get(user=request.user)
    matches = Match.objects.filter(Q(trainee1=trainee) | Q(trainee2=trainee)).order_by('-match_time')
    return render(request, 'partials/trainee_matches.html', {'matches': matches})

@login_required
@user_passes_test(is_trainee)
def trainee_payments(request):
    trainee = Trainee.objects.get(user=request.user)
    payments = Payment.objects.filter(trainee=trainee).order_by('-date')
    return render(request, 'partials/trainee_payments.html', {'payments': payments})

@login_required
def notifications(request):
    """
    Return list of notifications for the current user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    
    return render(request, 'partials/notification_list.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read.
    """
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Return updated unread count for the badge
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return render(request, 'partials/notification_badge.html', {'unread_count': unread_count})


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Mark all notifications as read.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'partials/notification_badge.html', {'unread_count': 0})


@login_required
@user_passes_test(is_admin)
def dashboard_statistics(request):
    """
    View that aggregates and returns dashboard statistics.
    Supports both full page render and HTMX partial updates.
    """
    # Calculate statistics
    total_trainees = Trainee.objects.filter(is_active=True).count()
    
    # Upcoming events (events that haven't ended yet)
    upcoming_events = Event.objects.filter(
        end_date__gte=timezone.now(),
        is_published=True
    ).count()
    
    # Pending payments (unpaid payments)
    pending_payments_data = Payment.objects.filter(paid=False).aggregate(
        count=models.Count('id'),
        total=Sum('amount')
    )
    pending_payments_count = pending_payments_data['count'] or 0
    pending_payments_amount = pending_payments_data['total'] or 0
    
    # Recent promotions (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_promotions = Promotion.objects.filter(
        date__gte=thirty_days_ago
    ).count()
    
    stats = {
        'total_trainees': total_trainees,
        'upcoming_events': upcoming_events,
        'pending_payments': pending_payments_count,
        'pending_payments_amount': float(pending_payments_amount),
        'recent_promotions': recent_promotions,
    }
    
    # Cache the statistics
    DashboardStat.objects.update_or_create(
        stat_type='admin_dashboard',
        defaults={'value': stats}
    )
    
    # If this is an HTMX request, return just the statistics partial
    if request.headers.get('HX-Request'):
        return render(request, 'partials/dashboard_stats.html', {'stats': stats})
    
    # Otherwise return full context
    return render(request, 'partials/dashboard_stats.html', {'stats': stats})


# Trainee Management Views

@login_required
@user_passes_test(is_admin)
def trainee_list(request):
    """
    Display list of trainees with search and filter functionality.
    Supports HTMX for real-time filtering.
    """
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset with related data
    trainees = Trainee.objects.select_related('user', 'belt').filter(is_active=True)
    
    # Apply search filter
    if search_query:
        trainees = trainees.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(belt__name__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )
    
    # Order by join date (newest first)
    trainees = trainees.order_by('-join_date')
    
    # If HTMX request, return only the table body
    if request.headers.get('HX-Request'):
        return render(request, 'partials/trainee_table_body.html', {
            'trainees': trainees,
            'search_query': search_query
        })
    
    # Full page render
    return render(request, 'trainee_list.html', {
        'trainees': trainees,
        'search_query': search_query
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def trainee_create(request):
    """
    Create a new trainee.
    Returns modal form for GET, processes form for POST.
    """
    if request.method == 'POST':
        form = TraineeForm(request.POST, request.FILES)
        if form.is_valid():
            trainee = form.save()
            
            # Add user to Trainee group
            trainee_group, created = Group.objects.get_or_create(name='Trainee')
            trainee.user.groups.add(trainee_group)
            
            # Set success message header for HTMX
            response = render(request, 'partials/trainee_row.html', {'trainee': trainee})
            response['HX-Trigger'] = 'traineeCreated'
            messages.success(request, f'Trainee {trainee.user.get_full_name()} created successfully.')
            return response
        else:
            # Return form with errors - retarget to modal content
            response = render(request, 'partials/trainee_form_modal.html', {
                'form': form,
                'action': 'create'
            }, status=400)
            response['HX-Retarget'] = '#modal-content'
            response['HX-Reswap'] = 'innerHTML'
            return response
    
    # GET request - return empty form
    form = TraineeForm()
    return render(request, 'partials/trainee_form_modal.html', {
        'form': form,
        'action': 'create'
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def trainee_update(request, trainee_id):
    """
    Update an existing trainee.
    Returns modal form for GET, processes form for POST.
    """
    trainee = get_object_or_404(Trainee, pk=trainee_id)
    
    if request.method == 'POST':
        form = TraineeForm(request.POST, request.FILES, instance=trainee)
        if form.is_valid():
            trainee = form.save()
            
            # Set success message header for HTMX
            response = render(request, 'partials/trainee_row.html', {'trainee': trainee})
            response['HX-Trigger'] = 'traineeUpdated'
            messages.success(request, f'Trainee {trainee.user.get_full_name()} updated successfully.')
            return response
        else:
            # Return form with errors - retarget to modal content
            response = render(request, 'partials/trainee_form_modal.html', {
                'form': form,
                'trainee': trainee,
                'action': 'update'
            }, status=400)
            response['HX-Retarget'] = '#modal-content'
            response['HX-Reswap'] = 'innerHTML'
            return response
    
    # GET request - return form with trainee data
    form = TraineeForm(instance=trainee)
    return render(request, 'partials/trainee_form_modal.html', {
        'form': form,
        'trainee': trainee,
        'action': 'update'
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def trainee_delete(request, trainee_id):
    """
    Delete (deactivate) a trainee.
    """
    trainee = get_object_or_404(Trainee, pk=trainee_id)
    trainee_name = trainee.user.get_full_name()
    
    # Soft delete - set is_active to False
    trainee.is_active = False
    trainee.save()
    
    # Return empty response with trigger for list refresh
    response = HttpResponse('')
    response['HX-Trigger'] = 'traineeDeleted'
    messages.success(request, f'Trainee {trainee_name} has been deactivated.')
    return response


@login_required
@user_passes_test(is_admin)
def trainee_delete_confirm(request, trainee_id):
    """
    Return confirmation modal for trainee deletion.
    """
    trainee = get_object_or_404(Trainee, pk=trainee_id)
    return render(request, 'partials/trainee_delete_confirm.html', {'trainee': trainee})


# Event Management Views

@login_required
@user_passes_test(is_admin)
def event_list(request):
    """
    Display list of events with calendar and list views.
    Supports HTMX for view switching.
    """
    # Get all events ordered by start date
    events = Event.objects.all().order_by('start_date')
    
    # Get view type from query parameter (default to calendar)
    view_type = request.GET.get('view', 'calendar')
    
    # If HTMX request for list view, return just the event cards
    if request.headers.get('HX-Request') and view_type == 'list':
        return render(request, 'partials/event_list_view.html', {
            'events': events
        })
    
    # Full page render
    return render(request, 'event_list.html', {
        'events': events,
        'view_type': view_type
    })


@login_required
@user_passes_test(is_admin)
def event_calendar_data(request):
    """
    Return events data for calendar rendering.
    """
    # Get month and year from query parameters
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if year and month:
        # Filter events for specific month
        events = Event.objects.filter(
            start_date__year=year,
            start_date__month=month
        ).order_by('start_date')
    else:
        # Get current month events
        now = timezone.now()
        events = Event.objects.filter(
            start_date__year=now.year,
            start_date__month=now.month
        ).order_by('start_date')
    
    # Return calendar partial
    return render(request, 'partials/event_calendar.html', {
        'events': events
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def event_create(request):
    """
    Create a new event.
    Returns modal form for GET, processes form for POST.
    """
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            
            # Set success message header for HTMX
            response = render(request, 'partials/event_card.html', {'event': event})
            response['HX-Trigger'] = 'eventCreated'
            messages.success(request, f'Event "{event.name}" created successfully.')
            return response
        else:
            # Return form with errors - retarget to modal content
            response = render(request, 'partials/event_form_modal.html', {
                'form': form,
                'action': 'create'
            }, status=400)
            response['HX-Retarget'] = '#modal-content'
            response['HX-Reswap'] = 'innerHTML'
            return response
    
    # GET request - return empty form
    form = EventForm()
    return render(request, 'partials/event_form_modal.html', {
        'form': form,
        'action': 'create'
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def event_update(request, event_id):
    """
    Update an existing event.
    Returns modal form for GET, processes form for POST.
    """
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            
            # Set success message header for HTMX
            response = render(request, 'partials/event_card.html', {'event': event})
            response['HX-Trigger'] = 'eventUpdated'
            messages.success(request, f'Event "{event.name}" updated successfully.')
            return response
        else:
            # Return form with errors - retarget to modal content
            response = render(request, 'partials/event_form_modal.html', {
                'form': form,
                'event': event,
                'action': 'update'
            }, status=400)
            response['HX-Retarget'] = '#modal-content'
            response['HX-Reswap'] = 'innerHTML'
            return response
    
    # GET request - return form with event data
    form = EventForm(instance=event)
    return render(request, 'partials/event_form_modal.html', {
        'form': form,
        'event': event,
        'action': 'update'
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def event_delete(request, event_id):
    """
    Delete an event.
    """
    event = get_object_or_404(Event, pk=event_id)
    event_name = event.name
    
    # Delete the event
    event.delete()
    
    # Return empty response with trigger for list refresh
    response = HttpResponse('')
    response['HX-Trigger'] = 'eventDeleted'
    messages.success(request, f'Event "{event_name}" has been deleted.')
    return response


@login_required
@user_passes_test(is_admin)
def event_delete_confirm(request, event_id):
    """
    Return confirmation modal for event deletion.
    """
    event = get_object_or_404(Event, pk=event_id)
    return render(request, 'partials/event_delete_confirm.html', {'event': event})


@login_required
@user_passes_test(is_admin)
def event_detail(request, event_id):
    """
    Display event details with associated matches and participants.
    """
    event = get_object_or_404(Event, pk=event_id)
    
    # Get all matches for this event
    matches = event.matches.select_related('trainee1', 'trainee2', 'winner', 'judge').all()
    
    # Get unique participants
    participant_ids = set()
    for match in matches:
        participant_ids.add(match.trainee1.id)
        participant_ids.add(match.trainee2.id)
    
    participants = Trainee.objects.filter(id__in=participant_ids).select_related('user', 'belt')
    
    # If HTMX request, return just the detail partial
    if request.headers.get('HX-Request'):
        return render(request, 'partials/event_detail.html', {
            'event': event,
            'matches': matches,
            'participants': participants
        })
    
    # Full page render
    return render(request, 'event_detail.html', {
        'event': event,
        'matches': matches,
        'participants': participants
    })


# Match Scoring Views

@login_required
@user_passes_test(is_judge)
def match_scoring(request, match_id):
    """
    Display match scoring interface for judges.
    Shows current match state with score controls.
    """
    match = get_object_or_404(
        Match.objects.select_related('trainee1', 'trainee2', 'event', 'winner'),
        pk=match_id,
        judge=request.user
    )
    
    # Check if match is in the future
    now = timezone.now()
    match.is_future = match.match_time > now
    match.is_completed = match.winner is not None
    
    # If HTMX request, return just the scoring partial
    if request.headers.get('HX-Request'):
        return render(request, 'partials/match_scoring_interface.html', {'match': match})
    
    # Full page render
    return render(request, 'match_scoring.html', {'match': match})


@login_required
@user_passes_test(is_judge)
@require_http_methods(["POST"])
def match_update_score(request, match_id):
    """
    Update match scores via HTMX.
    Supports increment/decrement operations.
    """
    match = get_object_or_404(
        Match.objects.select_related('trainee1', 'trainee2'),
        pk=match_id,
        judge=request.user
    )
    
    # Check if match is already completed
    if match.winner is not None:
        return HttpResponse("Match already completed", status=400)
    
    # Get the action and trainee
    action = request.POST.get('action')  # 'increment' or 'decrement'
    trainee = request.POST.get('trainee')  # 'trainee1' or 'trainee2'
    
    if action not in ['increment', 'decrement'] or trainee not in ['trainee1', 'trainee2']:
        return HttpResponse("Invalid action or trainee", status=400)
    
    # Update the score
    if trainee == 'trainee1':
        if action == 'increment':
            match.score1 += 1
        elif action == 'decrement' and match.score1 > 0:
            match.score1 -= 1
    else:  # trainee2
        if action == 'increment':
            match.score2 += 1
        elif action == 'decrement' and match.score2 > 0:
            match.score2 -= 1
    
    match.save()
    
    # Return updated score display
    return render(request, 'partials/match_scoring_interface.html', {'match': match})


@login_required
@user_passes_test(is_judge)
@require_http_methods(["POST"])
def match_complete(request, match_id):
    """
    Complete a match by declaring a winner.
    """
    match = get_object_or_404(
        Match.objects.select_related('trainee1', 'trainee2'),
        pk=match_id,
        judge=request.user
    )
    
    # Check if match is already completed
    if match.winner is not None:
        return HttpResponse("Match already completed", status=400)
    
    # Get the winner ID
    winner_id = request.POST.get('winner_id')
    
    if not winner_id:
        return HttpResponse("Winner must be selected", status=400)
    
    # Validate winner is one of the trainees
    if int(winner_id) not in [match.trainee1.id, match.trainee2.id]:
        return HttpResponse("Invalid winner selection", status=400)
    
    # Set the winner
    match.winner_id = winner_id
    match.save()
    
    # Create notifications for both trainees
    winner = match.trainee1 if int(winner_id) == match.trainee1.id else match.trainee2
    loser = match.trainee2 if winner == match.trainee1 else match.trainee1
    
    # Notification for winner
    Notification.objects.create(
        user=winner.user,
        title='Match Victory!',
        message=f'Congratulations! You won your match against {loser.user.get_full_name()} at {match.event.name}.',
        notification_type='match',
        link=f'/trainee/matches/'
    )
    
    # Notification for loser
    Notification.objects.create(
        user=loser.user,
        title='Match Result',
        message=f'Your match against {winner.user.get_full_name()} at {match.event.name} has been completed.',
        notification_type='match',
        link=f'/trainee/matches/'
    )
    
    # Return success response with trigger to refresh match list
    response = HttpResponse('')
    response['HX-Trigger'] = 'matchCompleted'
    messages.success(request, f'Match completed. Winner: {winner.user.get_full_name()}')
    return response


@login_required
@user_passes_test(is_judge)
def match_complete_form(request, match_id):
    """
    Return match completion form modal.
    """
    match = get_object_or_404(
        Match.objects.select_related('trainee1', 'trainee2'),
        pk=match_id,
        judge=request.user
    )
    
    return render(request, 'partials/match_complete_form.html', {'match': match})


# Promotion Management Views

@login_required
@user_passes_test(is_admin)
def promotion_list(request):
    """
    List all trainees and their promotion eligibility status.
    """
    trainees = Trainee.objects.select_related('belt', 'user').filter(is_active=True)
    
    # Calculate eligibility for each trainee
    for trainee in trainees:
        # Get last promotion date or join date
        last_promotion = trainee.promotions.order_by('-date').first()
        last_date = last_promotion.date if last_promotion else trainee.join_date
        
        # Time since last date (in days)
        days_since = (timezone.now().date() - last_date).days
        
        # Criteria (example): 6 months (180 days)
        trainee.time_eligible = days_since >= 180
        trainee.days_since_promotion = days_since
        
        # Performance: Win rate > 50% (if they have matches)
        matches = Match.objects.filter(Q(trainee1=trainee) | Q(trainee2=trainee)).exclude(winner=None)
        match_count = matches.count()
        wins = matches.filter(winner=trainee).count()
        win_rate = (wins / match_count * 100) if match_count > 0 else 0
        
        trainee.performance_eligible = match_count >= 5 and win_rate >= 40
        trainee.match_count = match_count
        trainee.win_rate = round(win_rate, 1)
        
        # Overall eligibility (can be adjusted)
        trainee.is_eligible = trainee.time_eligible
        
        # Next belt
        if trainee.belt:
            trainee.next_belt = Belt.objects.filter(order__gt=trainee.belt.order).order_by('order').first()
        else:
            trainee.next_belt = Belt.objects.order_by('order').first()

    context = {
        'trainees': trainees,
    }
    return render(request, 'promotion_list.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def promotion_create(request, trainee_id):
    """
    Handle promotion of a trainee.
    """
    trainee = get_object_or_404(Trainee, pk=trainee_id)
    current_belt = trainee.belt
    
    if request.method == 'POST':
        form = PromotionForm(request.POST, trainee=trainee)
        if form.is_valid():
            new_belt = form.cleaned_data['belt']
            
            # Create promotion record
            Promotion.objects.create(
                trainee=trainee,
                belt_from=current_belt,
                belt_to=new_belt,
                date=timezone.now().date()
            )
            
            # Update trainee belt
            trainee.belt = new_belt
            trainee.save()
            
            # Notification
            create_notification(
                user=trainee.user,
                title='Belt Promotion!',
                message=f'Congratulations! You have been promoted to {new_belt.name}.',
                notification_type='promotion',
                link='/trainee/profile/'
            )
            
            # HTMX response
            response = render(request, 'partials/promotion_row.html', {'trainee': trainee})
            response['HX-Trigger'] = 'promotionCompleted'
            messages.success(request, f'{trainee.user.get_full_name()} promoted to {new_belt.name}.')
            return response
            
        # Form invalid
        response = render(request, 'partials/promotion_form_modal.html', {
            'trainee': trainee,
            'current_belt': current_belt,
            'form': form
        }, status=400)
        response['HX-Retarget'] = '#modal-content'
        response['HX-Reswap'] = 'innerHTML'
        return response
            
    else:
        form = PromotionForm(trainee=trainee)
        
    context = {
        'trainee': trainee,
        'current_belt': current_belt,
        'form': form
    }
    return render(request, 'partials/promotion_form_modal.html', context)


@login_required
@user_passes_test(is_admin)
def promotion_history(request):
    """
    View promotion history.
    """
    promotions = Promotion.objects.select_related('trainee', 'belt_from', 'belt_to').order_by('-date')
    return render(request, 'promotion_history.html', {'promotions': promotions})


# Payment Management Views

@login_required
@user_passes_test(is_admin)
def payment_list(request):
    """
    List all payments with filtering.
    """
    status_filter = request.GET.get('status', 'all')
    
    payments = Payment.objects.select_related('trainee', 'trainee__user').order_by('-date')
    
    if status_filter == 'pending':
        payments = payments.filter(paid=False)
    elif status_filter == 'paid':
        payments = payments.filter(paid=True)
    elif status_filter == 'overdue':
        payments = payments.filter(paid=False, date__lt=timezone.now().date())
        
    # Calculate totals
    total_collected = Payment.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Payment.objects.filter(paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Mark overdue
    now = timezone.now().date()
    for payment in payments:
        payment.is_overdue = not payment.paid and payment.date < now
        
    context = {
        'payments': payments,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'status_filter': status_filter
    }
    return render(request, 'payment_list.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def payment_create(request):
    """
    Create a new payment record.
    """
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.paid = False
            payment.save()
            
            # Notification
            create_notification(
                user=payment.trainee.user,
                title='New Payment Due',
                message=f'A new payment of ${payment.amount} for {payment.description} is due on {payment.date}.',
                notification_type='payment',
                link='/trainee/payments/'
            )
            
            messages.success(request, 'Payment record created successfully.')
            
            if request.headers.get('HX-Request'):
                response = render(request, 'partials/payment_row.html', {'payment': payment})
                response['HX-Trigger'] = 'paymentCreated'
                response['HX-Retarget'] = '#payment-table-body'
                response['HX-Reswap'] = 'afterbegin'
                return response
            
            return redirect('payment_list')
        
        # Form invalid
        if request.headers.get('HX-Request'):
            response = render(request, 'partials/payment_form_modal.html', {'form': form}, status=400)
            response['HX-Retarget'] = '#modal-container'
            response['HX-Reswap'] = 'innerHTML'
            return response
            
    else:
        form = PaymentForm()
        
    # GET - return modal
    return render(request, 'partials/payment_form_modal.html', {'form': form})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def payment_mark_paid(request, payment_id):
    """
    Mark a payment as paid.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    payment.paid = True
    payment.save()
    
    # Notification
    create_notification(
        user=payment.trainee.user,
        title='Payment Received',
        message=f'Your payment of ${payment.amount} for {payment.description} has been received.',
        notification_type='payment',
        link='/trainee/payments/'
    )
    
    messages.success(request, f'Payment of ${payment.amount} marked as paid.')
    
    if request.headers.get('HX-Request'):
        response = render(request, 'partials/payment_row.html', {'payment': payment})
        response['HX-Trigger'] = 'paymentUpdated'
        return response
        
    return redirect('payment_list')


@login_required
@user_passes_test(is_admin)
def payment_reports(request):
    """
    Display payment reports and statistics.
    """
    total_collected = Payment.objects.filter(paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Payment.objects.filter(paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Overdue payments (due date passed and not paid)
    overdue_payments = Payment.objects.filter(paid=False, date__lt=timezone.now().date())
    total_overdue = overdue_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'total_collected': total_collected,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
    }
    return render(request, 'payment_reports.html', context)


@login_required
@user_passes_test(is_admin)
def reports_dashboard(request):
    """
    Display the reporting and analytics dashboard.
    """
    # Default date range: last 6 months
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=180)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def api_chart_data(request):
    """
    API endpoint to fetch chart data.
    """
    chart_type = request.GET.get('type')
    
    data = {}
    labels = []
    
    if chart_type == 'trainee_growth':
        # Trainee growth over last 6 months
        datasets_data = []
        for i in range(5, -1, -1):
            date = timezone.now().date() - timezone.timedelta(days=i*30)
            month_name = date.strftime('%B')
            # Count trainees who joined on or before this date
            count = Trainee.objects.filter(join_date__lte=date).count()
            labels.append(month_name)
            datasets_data.append(count)
            
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Total Trainees',
                'data': datasets_data,
                'borderColor': 'rgb(79, 70, 229)',
                'tension': 0.1,
                'fill': False
            }]
        })
        
    elif chart_type == 'belt_distribution':
        # Belt distribution
        belts = Belt.objects.all().order_by('order')
        counts = []
        colors = []
        
        for belt in belts:
            labels.append(belt.name)
            counts.append(Trainee.objects.filter(belt=belt).count())
            # Simple color generation
            colors.append(f'hsl({belt.order * 45 % 360}, 70%, 50%)')
            
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'Trainees per Belt',
                'data': counts,
                'backgroundColor': colors
            }]
        })
        
    elif chart_type == 'payment_status':
        # Payment status
        paid = Payment.objects.filter(paid=True).count()
        pending = Payment.objects.filter(paid=False).count()
        
        return JsonResponse({
            'labels': ['Paid', 'Pending'],
            'datasets': [{
                'data': [paid, pending],
                'backgroundColor': ['rgb(34, 197, 94)', 'rgb(239, 68, 68)']
            }]
        })
        
    return JsonResponse({'error': 'Invalid chart type'}, status=400)
