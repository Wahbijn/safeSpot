from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Accident, UserAccidentReport
from .forms import AccidentForm, UserAccidentReportForm, MinimalAccidentForm


# -----------------------------
# Witness / Passenger Report
# -----------------------------
@login_required
def add_user_accident_report(request):
    if request.method == "POST":
        form = UserAccidentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()
            messages.success(
                request,
                "Your accident report has been submitted successfully."
            )
            return redirect("dashboard_home")
    else:
        form = UserAccidentReportForm()
    return render(
        request,
        "add_user_accident_report.html",
        {"form": form}
    )


# -----------------------------
# Add Accident
# -----------------------------
@login_required
def add_accident(request):
    if request.method == "POST":
        form = MinimalAccidentForm(request.POST)
        if form.is_valid():
            accident = form.save(commit=False)
            accident.created_by = request.user
            accident.is_confirmed = False

            # Fill required fields with default values
            accident.reporter_name = request.user.username
            accident.reporter_phone = "N/A"
            accident.reporter_cin = "N/A"
            accident.car_type = "Unknown"
            accident.reason = accident.description if accident.description else "Quick report"
            accident.other_name = "N/A"
            accident.other_cin = "N/A"
            accident.other_phone = "N/A"
            accident.guilty = "me"

            accident.save()

            print(f"\n[INCIDENT CREATED] ID:{accident.id}, Location: {accident.localisation}, is_confirmed: {accident.is_confirmed}, confirmations: {accident.confirmations.count()}, created_by: {accident.created_by.username}\n")

            messages.success(
                request,
                f"Incident reported successfully! It is now pending confirmation by other users. (ID: {accident.id})"
            )
            return redirect("incidents:incident_list")
        else:
            print("[DEBUG] MinimalAccidentForm errors:", form.errors)
            print("[DEBUG] POST data:", request.POST)
    else:
        form = MinimalAccidentForm()
    return render(request, "add_accident.html", {"form": form})


# -----------------------------
# Accident List
# -----------------------------

# List of UserAccidentReport (Reported Accidents by users)
def accident_list(request):
    user_reports = UserAccidentReport.objects.order_by("-accident_datetime")
    return render(
        request,
        "accident_list.html",
        {
            "user_reports": user_reports,
        }
    )

# List of Accident (Reported Incidents)
def incident_list(request):
    incidents = Accident.objects.order_by("-accident_datetime")
    return render(
        request,
        "incident_list.html",
        {
            "incidents": incidents,
        }
    )


# -----------------------------
# Confirm Accident
# -----------------------------
@login_required
def confirm_accident(request, accident_id):
    accident = get_object_or_404(Accident, id=accident_id)

    # Remove cancellation if exists
    accident.cancellations.remove(request.user)

    if request.user not in accident.confirmations.all():
        accident.confirmations.add(request.user)

    # Rule: confirm after 3 confirmations
    if accident.confirmations.count() >= 3:
        accident.is_confirmed = True
        accident.save()

    messages.success(request, "Accident confirmed successfully.")
    return redirect("incidents:accident_list")


# -----------------------------
# Cancel Accident
# -----------------------------
@login_required
def cancel_accident(request, accident_id):
    accident = get_object_or_404(Accident, id=accident_id)

    # Remove confirmation if exists
    accident.confirmations.remove(request.user)

    if request.user not in accident.cancellations.all():
        accident.cancellations.add(request.user)

    # Rule: delete after 5 cancellations
    if accident.cancellations.count() >= 5:
        accident.delete()
        messages.success(
            request,
            "Accident removed after multiple cancellations."
        )
    else:
        messages.success(
            request,
            "Your cancellation has been recorded."
        )

    return redirect("incidents:accident_list")


# -----------------------------
# Pending Incidents (Need Confirmation)
# -----------------------------
@login_required
def pending_incidents(request):
    """Display ALL pending incidents including user's own (but they can't confirm their own)"""
    from django.db.models import Count, Q

    # Get ALL incidents with less than 2 confirmations (including user's own)
    incidents = Accident.objects.annotate(
        confirmation_count=Count('confirmations')
    ).filter(
        Q(confirmation_count__lt=2) &
        Q(is_confirmed=False)
    ).select_related('created_by').prefetch_related('confirmations', 'cancellations').order_by('-created_at')

    print(f"[DEBUG] All pending incidents (including own): {incidents.count()}")
    print(f"[DEBUG] User: {request.user.username}")

    # Calculate trust percentage for each incident
    incidents_with_trust = []
    for incident in incidents:
        confirmation_count = incident.confirmations.count()
        cancellation_count = incident.cancellations.count()
        total_votes = confirmation_count + cancellation_count

        # Calculate trust percentage (confirmations / total votes * 100)
        if total_votes > 0:
            trust_percentage = round((confirmation_count / total_votes) * 100)
        else:
            trust_percentage = 0

        # Check if current user has already confirmed or rejected
        user_confirmed = request.user in incident.confirmations.all()
        user_rejected = request.user in incident.cancellations.all()

        # Check if this is user's own incident
        is_own_incident = incident.created_by == request.user

        incidents_with_trust.append({
            'incident': incident,
            'confirmation_count': confirmation_count,
            'cancellation_count': cancellation_count,
            'trust_percentage': trust_percentage,
            'user_confirmed': user_confirmed,
            'user_rejected': user_rejected,
            'is_own_incident': is_own_incident,  # NEW: Flag for user's own incidents
            'can_vote': not user_confirmed and not user_rejected and not is_own_incident  # Can't vote on own
        })

    context = {
        'incidents_with_trust': incidents_with_trust,
        'total_pending': len(incidents_with_trust)
    }

    return render(request, "pending_incidents.html", context)


# -----------------------------
# API: Confirm Incident (AJAX)
# -----------------------------
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
@login_required
def confirm_incident_ajax(request, incident_id):
    """API endpoint to confirm an incident via AJAX"""
    try:
        incident = get_object_or_404(Accident, id=incident_id)

        # Check if user is trying to confirm their own incident
        if incident.created_by == request.user:
            return JsonResponse({
                'success': False,
                'error': 'You cannot confirm your own incident.'
            }, status=403)

        # Check if user already confirmed
        if request.user in incident.confirmations.all():
            return JsonResponse({
                'success': False,
                'error': 'You have already confirmed this incident.'
            }, status=400)

        # Check if user already rejected
        if request.user in incident.cancellations.all():
            return JsonResponse({
                'success': False,
                'error': 'You have already rejected this incident. Cannot confirm.'
            }, status=400)

        # Add confirmation
        incident.confirmations.add(request.user)

        # Check if incident should be marked as confirmed (2 confirmations needed)
        if incident.confirmations.count() >= 2:
            incident.is_confirmed = True
            incident.save()

        confirmation_count = incident.confirmations.count()
        cancellation_count = incident.cancellations.count()
        total_votes = confirmation_count + cancellation_count
        trust_percentage = round((confirmation_count / total_votes) * 100) if total_votes > 0 else 0

        return JsonResponse({
            'success': True,
            'message': 'Incident confirmed successfully!',
            'confirmation_count': confirmation_count,
            'cancellation_count': cancellation_count,
            'trust_percentage': trust_percentage,
            'is_confirmed': incident.is_confirmed
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# -----------------------------
# API: Reject Incident (AJAX)
# -----------------------------
@require_http_methods(["POST"])
@login_required
def reject_incident_ajax(request, incident_id):
    """API endpoint to reject an incident via AJAX"""
    try:
        incident = get_object_or_404(Accident, id=incident_id)

        # Check if user is trying to reject their own incident
        if incident.created_by == request.user:
            return JsonResponse({
                'success': False,
                'error': 'You cannot reject your own incident.'
            }, status=403)

        # Check if user already rejected
        if request.user in incident.cancellations.all():
            return JsonResponse({
                'success': False,
                'error': 'You have already rejected this incident.'
            }, status=400)

        # Check if user already confirmed
        if request.user in incident.confirmations.all():
            return JsonResponse({
                'success': False,
                'error': 'You have already confirmed this incident. Cannot reject.'
            }, status=400)

        # Add rejection
        incident.cancellations.add(request.user)

        # Rule: delete after 5 rejections
        confirmation_count = incident.confirmations.count()
        cancellation_count = incident.cancellations.count()

        if cancellation_count >= 5:
            incident.delete()
            return JsonResponse({
                'success': True,
                'message': 'Incident rejected and removed after multiple rejections.',
                'deleted': True
            })

        total_votes = confirmation_count + cancellation_count
        trust_percentage = round((confirmation_count / total_votes) * 100) if total_votes > 0 else 0

        return JsonResponse({
            'success': True,
            'message': 'Incident rejected successfully!',
            'confirmation_count': confirmation_count,
            'cancellation_count': cancellation_count,
            'trust_percentage': trust_percentage,
            'deleted': False
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# -----------------------------
# Admin Cancel Incident (Instant Delete)
# -----------------------------
@login_required
@require_http_methods(["POST"])
def admin_cancel_incident(request, incident_id):
    """
    Admin-only function to instantly cancel/delete an incident.
    No voting required - immediate deletion.
    """
    # Check if user is admin
    if not request.user.is_staff:
        return JsonResponse({
            "success": False,
            "error": "Only administrators can cancel incidents."
        }, status=403)

    try:
        incident = get_object_or_404(Accident, id=incident_id)

        # Store incident details for response message
        location = incident.localisation
        incident_id_str = str(incident_id)

        # Delete the incident
        incident.delete()

        return JsonResponse({
            "success": True,
            "message": f"Incident #{incident_id_str} at {location} has been cancelled successfully.",
            "incident_id": incident_id
        })

    except Accident.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Incident not found."
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
