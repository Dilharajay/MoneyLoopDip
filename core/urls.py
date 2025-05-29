from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('home/', home, name='home'),
    path('admindashboard/', admin_dashboard, name='admin_dashboard'),
    path('admindashboard/manage_groups', manage_groups, name='manage_groups'),
    path('admindashboard/manage_groups/addgroup', group_add_view, name='add_group'),
    path('admindashboard/manage_groups/viewgroups', view_groups, name='view_groups'),

    path('userdashboard/', user_dashboard, name='user_dashboard'),
    path('userdashboard/mygroups', user_group_view, name='mygroups'),

    path('how_it_works/', how_it_works_view, name='how_it_works'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('features/', features_view, name='features'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', view_profile, name='view_profile'),
    path('profile/update/', update_customer_profile, name='update_profile'),

    path('groups/<int:group_id>/', group_detail, name='group_detail'),
    path('groups/<int:group_id>/delete/', delete_group, name='delete_group'),
    path('groups/<int:group_id>/contribute/', make_contribution, name='make_contribution'),
    path('groups/contribute/cancel', cancel_contribution, name='cancel_contribution'),

    path('userdashboard/received-invitations', invitation_view, name='invitation_view'),
    path('accept-invitation/<str:token>/', accept_invitation_view, name='accept_invitation'),

    path('test/', test, name='dummy_task'),
    path('error/', error_view, name='error_view'),
]
