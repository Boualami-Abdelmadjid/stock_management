from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required

from main.views import *

urlpatterns = [
    path('',login_required(HomePage.as_view()), name="homepage"),
    path('signup/',SignupView.as_view(), name="signup"),
    path('login/',LoginView.as_view(), name="login"),
    path('logout/',LogoutView.as_view(), name="logout"),
    path('profile/',ProfileView.as_view(), name="profile"),
    path('dashboard/',DashboardView.as_view(), name="dashboard"),
    path('category/',CategoryView.as_view(), name="category"),
    path('router/',RouterView.as_view(), name="router"),
    path('routers-suggestions/',RouterSuggestions.as_view(), name="categories-suggestions"),
    path('categories-suggestions/',CategorySuggestions.as_view(), name="categories-suggestions"),
    path('create-store/',login_required(CreateStoreView.as_view()), name="create-store"),
    path('create-category/',login_required(CreateCategoryView.as_view()), name="create-category"),
    path('create-router/',login_required(CreateRouterView.as_view()), name="create-router"),
    path('actions/',ActionsView.as_view(), name='actions'),
    path('logs/',LogsView.as_view(), name='logs'),
    path('logs-operations/',LogsOpsView.as_view(), name='logs-operations')
]