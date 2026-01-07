from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Profile
from .forms import UserEditForm, PasswordChangeForm, ProfileEditForm, forms

User = get_user_model()


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard_home")   # change later
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")

        if password != confirm:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            password=password,
        )

        messages.success(request, "Account created! Please login.")
        return redirect("login")

    return render(request, "accounts/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url='login')
def profile_view(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)

    # Calculate points dynamically from confirmed incidents
    points = profile.get_points()

    # Get count of user's confirmed incidents for display
    from incidents.models import Accident
    confirmed_incidents = Accident.objects.filter(created_by=user, is_confirmed=True).count()

    context = {
        'user': user,
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
        'points': points,
        'confirmed_incidents': confirmed_incidents,
    }

    return render(request, 'accounts/profile.html', context)


# ============================================
# ADMIN VIEWS FOR MANAGING CLIENTS
# ============================================

@login_required(login_url='login')
def admin_clients_list(request):
    """Admin view to list all clients"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    clients = User.objects.filter(role='client').order_by('-date_joined')
    
    context = {
        'clients': clients,
    }
    
    return render(request, 'accounts/admin/clients_list.html', context)


@login_required(login_url='login')
def admin_client_edit(request, client_id):
    """Admin view to edit a client's profile"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    client = get_object_or_404(User, id=client_id, role='client')
    try:
        profile = Profile.objects.get(user=client)
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=client)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client.username}' updated successfully!")
            return redirect('admin_clients_list')
    else:
        form = UserEditForm(instance=client)
    
    context = {
        'form': form,
        'client': client,
        'profile': profile,
    }
    
    return render(request, 'accounts/admin/client_edit.html', context)


@login_required(login_url='login')
def admin_client_delete(request, client_id):
    """Admin view to delete a client"""
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    client = get_object_or_404(User, id=client_id, role='client')
    
    if request.method == 'POST':
        # Récupérer la valeur saisie pour la confirmation
        confirm_username = request.POST.get('confirm', '').strip()
        
        if confirm_username != client.username:
            messages.error(request, "Username does not match. Deletion cancelled.")
        else:
            username = client.username
            client.delete()
            messages.success(request, f"Client '{username}' deleted successfully!")
            return redirect('admin_clients_list')
    
    context = {
        'client': client,
    }
    
    return render(request, 'accounts/admin/client_delete.html', context)

def admin_client_add(request):
    if request.method == "POST":
        form = UserEditForm(request.POST, request.FILES)
        if form.is_valid():
            # Create new user
            user = form.save(commit=False)
            user.username = form.cleaned_data["email"].split("@")[0]
            user.set_password("defaultpassword123")
            user.role = "client"
            user.save()

            # Update the auto-created profile instead of creating a new one
            profile = user.profile  # already exists thanks to signals

            profile.phone = form.cleaned_data.get("phone")
            profile.avatar = form.cleaned_data.get("avatar")
            profile.save()

            messages.success(request, "Client added successfully!")
            return redirect("admin_clients_list")
    else:
        form = UserEditForm()

    context = {
        "form": form,
    }
    return render(request, "accounts/admin/client_add.html", context)
