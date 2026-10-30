from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'userprofile'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.my_profile, name='my_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('<int:user_id>/', views.public_profile, name='public_profile'),
    path('register/htmx/', views.register_htmx, name='register_htmx'),
    path('login/htmx/', views.login_htmx, name='login_htmx'),
    path('edit/htmx/', views.edit_profile_htmx, name='edit_profile_htmx'),
    path('edit/avatar/delete/', views.delete_avatar, name='delete_avatar'),
    path('delete/permanent/', views.hard_delete_account, name='hard_delete_account'),
    path('deactivate/', views.soft_delete_account, name='soft_delete_account'),
]