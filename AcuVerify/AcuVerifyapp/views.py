from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Staff, Students
from .forms import StaffRegistrationForm, StudentRegistrationForm, EmailForm, PasswordForm, CreatePasswordForm


# Create your views here.

def home(request):
    return render(request, 'home.html')

def login_user(request):
    # Reset session if requested
    if request.GET.get('reset') == 'true':
        request.session.pop('login_email', None)
        request.session.pop('step', None)
        request.session.pop('user_type', None)
        request.session.pop('staff_id', None)
        request.session.pop('student_id', None)
        return redirect('login')
    
    # Step 1: Check email
    if 'step' not in request.session or request.session.get('step') == 'email':
        if request.method == 'POST':
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                email = email_form.cleaned_data['email'].lower()
                
                # Check if email exists in User table
                try:
                    user = User.objects.get(email=email)
                    # User exists, go to password step
                    request.session['login_email'] = email
                    request.session['step'] = 'password'
                    request.session['user_type'] = 'existing_user'
                    return redirect('login')
                except User.DoesNotExist:
                    # Check Staff table
                    try:
                        staff = Staff.objects.get(email__iexact=email)
                        request.session['login_email'] = email
                        request.session['step'] = 'create_password'
                        request.session['user_type'] = 'staff'
                        request.session['staff_id'] = staff.id
                        return redirect('login')
                    except Staff.DoesNotExist:
                        # Check Students table
                        try:
                            student = Students.objects.get(email__iexact=email)
                            request.session['login_email'] = email
                            request.session['step'] = 'create_password'
                            request.session['user_type'] = 'student'
                            request.session['student_id'] = student.id
                            return redirect('login')
                        except Students.DoesNotExist:
                            messages.error(request, 'A user with this email does not exist.')
                            email_form = EmailForm()
        else:
            email_form = EmailForm()
        
        return render(request, 'login.html', {'form': email_form, 'step': 'email'})
    
    # Step 2a: Existing user - enter password
    elif request.session.get('step') == 'password':
        if request.method == 'POST':
            password_form = PasswordForm(request.POST)
            if password_form.is_valid():
                email = request.session.get('login_email')
                password = password_form.cleaned_data['password']
                
                # Authenticate user
                try:
                    user = User.objects.get(email=email)
                    user = authenticate(request, username=user.username, password=password)
                    if user is not None:
                        auth_login(request, user)
                        # Clear session
                        request.session.pop('login_email', None)
                        request.session.pop('step', None)
                        request.session.pop('user_type', None)
                        messages.success(request, 'Login successful!')
                        return redirect('home')
                    else:
                        messages.error(request, 'Invalid password.')
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
                    request.session.pop('login_email', None)
                    request.session.pop('step', None)
                    request.session.pop('user_type', None)
                    return redirect('login')
        else:
            password_form = PasswordForm()
        
        return render(request, 'login.html', {
            'form': password_form, 
            'step': 'password',
            'email': request.session.get('login_email')
        })
    
    # Step 2b: New user (Staff/Student) - create password
    elif request.session.get('step') == 'create_password':
        if request.method == 'POST':
            create_password_form = CreatePasswordForm(request.POST)
            if create_password_form.is_valid():
                email = request.session.get('login_email')
                password = create_password_form.cleaned_data['password']
                user_type = request.session.get('user_type')
                
                # Create User account
                try:
                    # Use email as username (or generate unique username if email already taken as username)
                    username = email.split('@')[0]
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{email.split('@')[0]}{counter}"
                        counter += 1
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    
                    # Log in the user
                    auth_login(request, user)
                    
                    # Clear session
                    request.session.pop('login_email', None)
                    request.session.pop('step', None)
                    request.session.pop('user_type', None)
                    request.session.pop('staff_id', None)
                    request.session.pop('student_id', None)
                    
                    messages.success(request, f'Password created successfully! Welcome, {user_type.title()}!')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, f'Error creating account: {str(e)}')
        else:
            create_password_form = CreatePasswordForm()
        
        user_type = request.session.get('user_type', 'user')
        return render(request, 'login.html', {
            'form': create_password_form,
            'step': 'create_password',
            'email': request.session.get('login_email'),
            'user_type': user_type
        })
    
    # Default: reset to email step
    else:
        request.session.pop('login_email', None)
        request.session.pop('step', None)
        request.session.pop('user_type', None)
        return redirect('login')

def register_staff(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print(form.cleaned_data)
            return redirect('home')
    else:
        form = StaffRegistrationForm()
    return render(request, 'staffregistrationform.html', {'form': form})
        
    
def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = StudentRegistrationForm()
    return render(request, 'studentregistration.html', {'form': form})

