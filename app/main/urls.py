from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import path

from main.views import HomePage, SignupView, LoginView, ProfileView, CategoryView, RouterView,CategorySuggestions, CreateStoreView, CreateCategoryView, CreateRouterView, ActionsView, LogsOpsView, SwitchStore, ServiceCenter, ManagementCenter, ReturnToCCD, TransferToStore, StockTakeView

urlpatterns = [ 
    path('', login_required(HomePage.as_view()), name="homepage"),
    path('signup/', SignupView.as_view(), name="signup"),
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('profile/', ProfileView.as_view(), name="profile"),
    path('category/', CategoryView.as_view(), name="category"),
    path('router/', RouterView.as_view(), name="router"),
    path('categories-suggestions/', CategorySuggestions.as_view(), name="categories-suggestions"),
    path('create-store/', login_required(CreateStoreView.as_view()), name="create-store"),
    path('create-category/', login_required(CreateCategoryView.as_view()), name="create-category"),
    path('create-router/', login_required(CreateRouterView.as_view()), name="create-router"),
    path('actions/', ActionsView.as_view(), name='actions'),
    path('logs-operations/', LogsOpsView.as_view(), name='logs-operations'),
    path('switch-store/', SwitchStore.as_view(), name='switch-store'),
    path('service_center/', ServiceCenter.as_view(), name='service_center'),
    path('management_center/', ManagementCenter.as_view(), name='management_center'),
    path('ccd-return/', ReturnToCCD.as_view(), name='ccd-return'),
    path('transfer/', TransferToStore.as_view(), name='transfer'),
    path('stock-take/', StockTakeView.as_view(), name='stock-take'),
]
