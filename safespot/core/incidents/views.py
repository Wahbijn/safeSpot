from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
            accident.save()
            messages.success(
                request,
                "Accident added successfully and is pending confirmation."
            )
            return redirect("incidents:accident_list")
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