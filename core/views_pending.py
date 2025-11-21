
@login_required
@user_passes_test(is_admin)
def pending_trainees(request):
    """
    Display list of pending trainees awaiting approval.
    """
    pending_list = Trainee.objects.filter(is_approved=False).select_related('user', 'belt').order_by('-join_date')
    
    return render(request, 'pending_trainees.html', {'pending_list': pending_list})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def approve_trainee(request, trainee_id):
    """
    Approve a pending trainee.
    """
    trainee = get_object_or_404(Trainee, pk=trainee_id)
    trainee.is_approved = True
    trainee.is_active = True
    trainee.save()
    
    # Create notification for the trainee
    create_notification(
        user=trainee.user,
        title='Account Approved',
        message='Your account has been approved. You can now access the trainee dashboard.',
        notification_type='event'
    )
    
    messages.success(request, f'Trainee {trainee.user.get_full_name()} has been approved.')
    
    # If HTMX, remove the row
    if request.headers.get('HX-Request'):
        return HttpResponse('')
        
    return redirect('pending_trainees')
