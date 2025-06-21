# jobwishers.py

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import admin
from django.contrib.auth.decorators import login_required

# ----------------------- SETTINGS ---------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

settings.configure(
    DEBUG=True,
    SECRET_KEY='jobwishers_secret',
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=['*'],
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ],
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        '__main__',  # Refers to this file as the app
    ],
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    },
    STATIC_URL='/static/',
)

# ----------------------- MODELS ---------------------------

from django.apps import AppConfig, apps
from django.core.wsgi import get_wsgi_application

class MainAppConfig(AppConfig):
    name = '__main__'
    verbose_name = "Main"

if not apps.ready:
    apps.populate(settings.INSTALLED_APPS)

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)

# ----------------------- FORMS ---------------------------

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description']

# ----------------------- VIEWS ---------------------------

def index(request):
    jobs = Job.objects.all()
    return render(request, 'index.html', {'jobs': jobs})

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            return redirect('index')
    else:
        form = JobForm()
    return render(request, 'post_job.html', {'form': form})

# ----------------------- URLS ---------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('post/', post_job, name='post_job'),
]

# ----------------------- TEMPLATES ---------------------------

os.makedirs('templates', exist_ok=True)

with open('templates/index.html', 'w') as f:
    f.write("""
<h1>JobWishers - Jobs for Housewives</h1>
{% if user.is_authenticated %}
<p>Welcome, {{ user.username }} | <a href='/logout/'>Logout</a> | <a href='/post/'>Post a Job</a></p>
{% else %}
<p><a href='/login/'>Login</a> | <a href='/signup/'>Signup</a></p>
{% endif %}
<hr>
<ul>
{% for job in jobs %}
<li><b>{{ job.title }}</b> - {{ job.description }} (Posted by {{ job.posted_by.username }})</li>
{% endfor %}
</ul>
""")

with open('templates/signup.html', 'w') as f:
    f.write("""
<h2>Signup</h2>
<form method='post'>{% csrf_token %}{{ form.as_p }}<button type='submit'>Register</button></form>
<a href='/login/'>Already have an account?</a>
""")

with open('templates/login.html', 'w') as f:
    f.write("""
<h2>Login</h2>
<form method='post'>{% csrf_token %}{{ form.as_p }}<button type='submit'>Login</button></form>
<a href='/signup/'>Don't have an account?</a>
""")

with open('templates/post_job.html', 'w') as f:
    f.write("""
<h2>Post a Job</h2>
<form method='post'>{% csrf_token %}{{ form.as_p }}<button type='submit'>Post</button></form>
<a href='/'>Back to Home</a>
""")

# ----------------------- MAIN ---------------------------

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '__main__')
    django.setup()

    from django.core.management import call_command
    try:
        # Apply migrations if not already
        call_command('makemigrations', interactive=False)
        call_command('migrate', interactive=False)
    except Exception as e:
        print("Migration error:", e)

    execute_from_command_line(sys.argv)
