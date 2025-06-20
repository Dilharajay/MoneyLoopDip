from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from pyexpat.errors import messages
from django.contrib import messages

from .forms import RegistrationForm, AddGroupForm, MakeContributionForm, CustomerUpdateForm
from .models import Customer, Group, Transaction, Notification, Contribution, GroupInvitation

# Invitations
from django.utils.crypto import get_random_string
from .services.notification_service import NotificationService
from django.urls import reverse

# payment service
from core.services.payment_service import DummyPaymentService
from .tasks import dummy_task


def home(request):
    return render(request, 'home.html')

def about_us_view (request):
    return render(request,'Errors/404.html')

class LegalDocumentsView(TemplateView):
    template_name = 'leagal/terms_and_conditions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin')
            elif user.role == 'A':
                messages.success(request, 'Login successful as an admin!')
                return redirect('admin_dashboard')
            elif user.role == 'U':
                messages.success(request, 'Login successful as an user!')
                return redirect('user_dashboard')
            else:
                messages.error(request, 'An error occurred while logging in!')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Extracting data
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email').lower().strip()
            nic = form.cleaned_data.get('nic')
            date_of_birth = form.cleaned_data.get('date_of_birth')
            phone = form.cleaned_data.get('phone')
            country = form.cleaned_data.get('country')
            street_address = form.cleaned_data.get('street_address')
            city = form.cleaned_data.get('city')
            zip_code = form.cleaned_data.get('zip_code')
            state = form.cleaned_data.get('state')
            role = form.cleaned_data.get('role')

            # Username/email validation
            if Customer.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            elif Customer.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
            elif Customer.objects.filter(nic=nic).exists():
                messages.error(request, "NIC already exists.")
            else:
                try:
                    customer = Customer.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        nic=nic,
                        date_of_birth=date_of_birth,
                        phone=phone,
                        country=country,
                        street_address=street_address,
                        city=city,
                        zip_code=zip_code,
                        state=state,
                        role=role
                    )
                    customer.save()
                    messages.success(request, "Registration successful.")
                    NotificationService.send_welcome_email(customer)
                    return redirect('login')
                except Exception as e:
                    messages.error(request, f"An error occurred while registering str{e}. Please try again.")

    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def group_add_view(request):
    if request.method == "POST":
        form = AddGroupForm(request.POST, creator=request.user)
        if form.is_valid():
            creator = request.user
            group = Group.objects.create(
                group_name=form.cleaned_data['group_name'],
                created_by=creator,
                size=form.cleaned_data['size'],
                cycle_duration=form.cleaned_data['cycle_duration'],
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                remaining_amount=form.cleaned_data['amount'],

            )
            # disabled for group invitation develop process
            # group.members.set(form.cleaned_data['members'])
            group.save()
            group.members.add(creator)  # Add the creator as a member
            # Send invitations to selected members (excluding creator)
            for member in form.cleaned_data['members']:
                if member != creator:
                    # Create invitation
                    invitation = GroupInvitation.objects.create(
                        group=group,
                        email=member.email,
                        invited_by=creator,
                    )
                    invitation.save()

                    # Build accept URL
                    accept_url = request.build_absolute_uri(
                        reverse('accept_invitation', args=[invitation.token])
                    )
                    # Send email
                    NotificationService.send_email_notification(
                        subject=f"You're invited to join the group '{group.group_name}'",
                        template_name='group_invitation',
                        recipient_email=member.email,
                        context={
                            'group': group,
                            'inviter': creator,
                            'accept_url': accept_url,
                        },
                    )

            messages.success(request, 'Group added successfully!')
            return redirect('manage_groups')  # Redirect to groups list after creation
    else:
        form = AddGroupForm(creator=request.user)

    return render(request, 'add_group.html', {'form': form})



@login_required
def manage_groups(request):
    return render(request, 'manage_groups.html')


@login_required
def view_groups(request):
    # Get groups where current user is the creator or a member
    created_groups = Group.objects.filter(created_by=request.user).order_by('-created_at')
    member_groups = Group.objects.filter(members=request.user).exclude(created_by=request.user)

    context = {
        'created_groups': created_groups,
        'member_groups': member_groups,
    }
    return render(request, 'view_groups.html', context)


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Check if user has permission to view this group
    if request.user != group.created_by and request.user not in group.members.all():
        messages.error(request, "You don't have permission to view this group")
        return redirect('manage_groups')

    contributions = Contribution.objects.filter(group=group)
    transactions = Transaction.objects.filter(group=group)

    context = {
        'group': group,
        'contributions': contributions,
        'transactions': transactions,
    }
    return render(request, 'group_detail.html', context)


@login_required
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.user != group.created_by:
        messages.error(request, "You don't have permission to delete this group")
        return redirect('manage_groups')

    if request.method == 'POST':
        group.delete()
        messages.success(request, "Group deleted successfully")
    return redirect('view_groups')


@login_required
def user_dashboard(request):
    contributions = Contribution.objects.filter(user=request.user).order_by('-date')[:5]

    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).order_by('-created_at')[:5]

    context = {
        'contributions': contributions,
        'notifications': notifications,
    }

    return render(request, 'user_dashboard.html', context)


@login_required
def user_group_view(request):
    # Get user's groups (both created and joined)
    member_groups = Group.objects.filter(members=request.user).exclude(created_by=request.user)

    context = {
        'member_groups': member_groups,
        # 'total_contributions': total_contributions,
    }
    return render(request, 'mygroups.html', context)


@login_required
def admin_dashboard(request):
    contributions = Contribution.objects.filter(user=request.user).order_by('-date')[:5]

    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).order_by('-created_at')[:5]

    context = {
        'contributions': contributions,
        'notifications': notifications,
    }

    return render(request, 'admin_dashboard.html', context)


def how_it_works_view(request):
    return render(request, 'how_it_works.html')


def features_view(request):
    return render(request, 'features.html')


# payment section
@login_required
def make_contribution(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    form = MakeContributionForm(group=group)

    if request.user not in group.members.all():
        messages.error(request, "You are not a member of this group")
        if request.user.role == 'U':
            return redirect('user_dashboard')
        elif request.user.role == 'A':
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Something went wrong!")

    # Check if group is still active
    if group.all_cycles_completed_state:
        messages.error(request, "This group has completed all contribution cycles")
        if request.user.role == 'U':
            return redirect('user_dashboard')
        elif request.user.role == 'A':
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Something went wrong!")

    # Check if user already contributed
    if DummyPaymentService.has_user_contributed_in_current_cycle(group, request.user):
        messages.error(request, "You have already contributed in this cycle")
        if request.user.role == 'U':
            return redirect('user_dashboard')
        elif request.user.role == 'A':
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Something went wrong!")

    if request.method == "POST":
        form = MakeContributionForm(request.POST, group=group)
        if form.is_valid():

            try:
                contribution = form.save(commit=False)
                contribution.user = request.user
                user_email = request.user.email
                contribution.group = group
                contribution.payment_reference = f"CONT-{int(timezone.now().timestamp())}"
                contribution.save()

                # Process payment using group's payment method
                payment_result = DummyPaymentService.process_contribution(contribution, user_email)

                if payment_result['success']:
                    messages.success(request, f"{payment_result['message']}")
                    group.rotate_recipient()
                    if request.user.role == 'U':
                        return redirect('user_dashboard')
                    else:
                        return redirect('admin_dashboard')

                else:
                    contribution.delete()
                    messages.error(request, f"{payment_result['message']}")
            except Exception as e:
                messages.error(request, f'An error occurred processing payment: {str(e)}')
        else:
            messages.error(request, "Something went wrong!")
            form = MakeContributionForm(group=group)

    context = {
        'form': form,
        'group': group,
    }
    return render(request, 'make_contribution.html', context)


@login_required
def cancel_contribution(request):
    user = request.user
    try:
        messages.success(request, f"Contribution for the group has been cancelled ")
        if user.role == 'U':
            return redirect('user_dashboard')
        else:
            return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return render(request, 'Errors/404.html')


@login_required
def invitation_view(request):
    invitations = GroupInvitation.objects.filter(email=request.user.email, status='pending')
    return render(request, 'received_invitations.html', {'invitations': invitations})


@login_required
def accept_invitation_web(request, invitation_id):
    invitation = get_object_or_404(GroupInvitation, id=invitation_id)

    # Check if the invitation is already accepted
    if invitation.status != 'pending':
        messages.error(request, "This invitation has already been accepted or rejected.")
        return redirect('user_dashboard')  # Redirect to user dashboard if invitation is not pending

    try:
        # Find the user by email
        user = Customer.objects.get(email=invitation.email)

        # Add user to the group
        group = invitation.group
        group.members.add(user)
        group.save()

        # Mark the invitation as accepted
        invitation.status = 'accepted'
        invitation.save()

        messages.success(request, "Invitation accepted successfully.")
        return redirect('user_dashboard')

    except Customer.DoesNotExist:
        messages.error(request, "No user account found for this invitation email.")
        return redirect('user_dashboard')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('user_dashboard')


def accept_invitation_view(request, token):
    invitation = get_object_or_404(GroupInvitation, token=token)
    if invitation.status != 'pending':
        messages.error(request, "This invitation has already been used.")
        return redirect('login')

    # Find the user by email
    try:
        user = Customer.objects.get(email=invitation.email)
    except Customer.DoesNotExist:
        messages.error(request, "No user account found for this invitation email. Register MoneyLoop in order to continue.")
        return redirect('register')

    # Add user to group
    group = invitation.group
    group.members.add(user)
    group.save()

    # Mark invitation as accepted
    invitation.status = 'accepted'
    invitation.save()

    # Optionally log the user in
    login(request, user)
    messages.success(request, f"You have joined the group '{group.group_name}'!")
    return redirect('user_dashboard')

def error_view(request):
    return render(request, 'Errors/404.html')

@login_required
def view_profile(request):
    user = request.user
    context = {
        'user': user,
        'title': 'My Profile',
        'active_tab': 'profile'
    }
    return render(request, 'view_profile.html', context)


@login_required
def update_customer_profile(request):
    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            # Handle password change
            new_password = form.cleaned_data.get('new_password')
            if new_password:
                user.set_password(new_password)
                messages.success(request, 'Your password has been updated successfully')
                # Re-authenticate user if password changed
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)

            user.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('view_profile')
    else:
        form = CustomerUpdateForm(instance=request.user)

    context = {
        'form': form,
        'title': 'Update Profile'
    }
    return render(request, 'update_profile.html', context)

def test(request):
    dummy_task.delay()
    return HttpResponse("Celery Online")