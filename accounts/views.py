from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList, ProfileForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile
from django.urls import reverse

@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')

def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')

def manager_login(request):
    """Manager-only login to access Django admin dashboard with dedicated template."""
    template_data = {}
    template_data['title'] = 'Manager Login'
    if request.method == 'GET':
        return render(request, 'accounts/manager_login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/manager_login.html', {'template_data': template_data})
        elif not user.is_staff:
            template_data['error'] = 'You are not authorized to access the admin dashboard.'
            return render(request, 'accounts/manager_login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    selected_role = request.GET.get('role', 'customer')
    selected_role = 'customer' if selected_role not in ['customer', 'manager'] else selected_role
    if request.method == 'GET':
        template_data['user_form'] = CustomUserCreationForm()
        template_data['profile_form'] = ProfileForm()
        template_data['show_customer_fields'] = (selected_role == 'customer')
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = user.profile
            role = request.POST.get('role', 'customer')
            profile.role = role
            profile.save()
            
            # Set is_staff and is_superuser for manager accounts
            if role == 'manager':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            return redirect('accounts.login')
        else:
            template_data['user_form'] = user_form
            template_data['profile_form'] = profile_form

            selected_role = request.POST.get('role', 'customer')
            selected_role = 'customer' if selected_role not in ['customer', 'manager'] else selected_role
            template_data['show_customer_fields'] = (selected_role == 'customer')
            return render(request, 'accounts/signup.html', {'template_data': template_data})

@login_required
def orders(request):
    template_data = {}
    template_data['title'] = 'Orders'
    template_data['orders'] = request.user.order_set.all()
    return render(request, 'accounts/orders.html', 
        {'template_data': template_data})

@login_required
def profile_view(request):
    profile = request.user.profile
    edit_mode = request.GET.get("edit") == "true"
    saved = False

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.postal_code = request.POST.get("postal_code")
        profile.phone = request.POST.get("phone")
        profile.save()
        saved = True
        edit_mode = False  # go back to view mode after saving

    context = {
        "profile": profile,
        "edit_mode": edit_mode,
        "saved": saved,
    }
    return render(request, "accounts/profile.html", context)
