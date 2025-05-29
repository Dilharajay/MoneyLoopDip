from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import MinLengthValidator, RegexValidator, MaxLengthValidator
from django.contrib.auth.password_validation import validate_password

from core.models import Customer, Group, Contribution


class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        validators=[MinLengthValidator(4)]
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        validators=[validate_password]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    nic = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        #validators=[RegexValidator(r'^\d{9}[VvXx]|\d{12}$', 'Invalid NIC format.')]
    )
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}))
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        validators=[RegexValidator(r'^\+?\d{9,15}$', 'Invalid phone number.')]
    )

    country = forms.ChoiceField(
        choices=[
            ('', 'Select a country'),
            ('US', 'United States'),
            ('GB', 'United Kingdom'),
            ('CA', 'Canada'),
            ('AU', 'Australia'),
            ('IN', 'India'),
            ('LK', 'Sri Lanka'),
            ('DE', 'Germany'),
            ('FR', 'France'),
            ('JP', 'Japan'),
            ('CN', 'China'),
            ('BR', 'Brazil'),
            ('ZA', 'South Africa'),
            ('RU', 'Russia'),
        ],# Define COUNTRIES or use a library
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    street_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    state = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    zip_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        validators=[
        #    RegexValidator(r'^\d{5}(-\d{4})?$', 'Invalid ZIP code.')
        ]
    )
    role = forms.ChoiceField(
        choices=[('U', 'User'), ('A', 'Admin')],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class AddGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name', 'size','cycle_duration', 'members', 'amount', 'payment_method']
        widgets = {
            'group_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'placeholder': 'Enter group name'
            }),
            'size': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'min': 2,
                'max': 10
            }),

            'cycle_duration': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'min': 2,
                'max': 10
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6'
            }),
            'members': forms.CheckboxSelectMultiple(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'
            })
        }

    def __init__(self, *args, **kwargs):
        creator = kwargs.pop('creator')  # Get the creator from kwargs
        super().__init__(*args, **kwargs)
        # Exclude the creator from member selection
        self.fields['members'].queryset = Customer.objects.exclude(id=creator.id)
        # Make fields required
        self.fields['members'].required = True
        self.fields['amount'].required = True
        self.fields['cycle_duration'].required = True


    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data

# contribution making form
class MakeContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['amount']  # Only include existing field

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)

        # Set amount from group and make it readonly
        self.fields['amount'].initial = self.group.amount
        self.fields['amount'].widget.attrs.update({
            'readonly': 'readonly',
            'class': 'bg-gray-100 mt-2 cursor-not-allowed'
        })

    def clean_amount(self):
        # Ensure amount matches group's required amount
        if self.cleaned_data['amount'] != self.group.amount:
            raise forms.ValidationError(f'Amount must be {self.group.amount}')
        return self.cleaned_data['amount']


class CustomerUpdateForm(UserChangeForm):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Enter your current password to confirm changes"
    )

    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'date_of_birth', 'street_address', 'city',
                  'state', 'zip_code', 'country', 'nic']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'street_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password field from parent UserChangeForm
        self.fields.pop('password', None)
        # Make NIC read-only
        self.fields['nic'].widget.attrs['readonly'] = True
        self.fields['nic'].widget.attrs['class'] = 'form-control bg-light'

        # Add Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        current_password = cleaned_data.get('current_password')

        # Password change validation
        if new_password:
            if not current_password:
                raise ValidationError("Current password is required to change your password")
            if not self.instance.check_password(current_password):
                raise ValidationError("Current password is incorrect")
            if new_password != confirm_password:
                raise ValidationError("New passwords don't match")

        # Email uniqueness validation
        email = cleaned_data.get('email')
        if email and Customer.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use")

        return cleaned_data