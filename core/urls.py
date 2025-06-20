from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    # Main pages
    path('', home, name='home'),  # Made this the root URL
    path('how-it-works/', how_it_works_view, name='how_it_works'),
    path('about/', about_us_view, name='about_us'),
    path('features/', features_view, name='features'),
    path('legal/', LegalDocumentsView.as_view(), name='legal-documents'),

    # Authentication
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User profile
    path('profile/', view_profile, name='view_profile'),
    path('profile/update/', update_customer_profile, name='update_profile'),

    # Admin dashboard and group management
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/groups/', manage_groups, name='manage_groups'),
    path('admin/groups/create/', group_add_view, name='add_group'),
    path('admin/groups/all/', view_groups, name='view_groups'),

    # User dashboard
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('dashboard/groups/', user_group_view, name='mygroups'),
    path('dashboard/invitations/', invitation_view, name='invitation_view'),

    # Group operations
    path('groups/<int:group_id>/', group_detail, name='group_detail'),
    path('groups/<int:group_id>/delete/', delete_group, name='delete_group'),
    path('groups/<int:group_id>/contribute/', make_contribution, name='make_contribution'),
    path('groups/contribution/cancel/', cancel_contribution, name='cancel_contribution'),

    # Invitations
    path('invitations/accept/<str:token>/', accept_invitation_view, name='accept_invitation'),

    # Testing and error
    path('test/', test, name='dummy_task'),
    path('error/', error_view, name='error_view'),
]