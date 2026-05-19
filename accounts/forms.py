from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Member, RegistrationField


# All optional fields that can be toggled via the management panel
_OPTIONAL_FIELDS = ['phone', 'address', 'city', 'state', 'zip_code', 'snowmobile_brand']


class MembershipApplicationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Member
        # Include all possible fields; __init__ removes disabled ones
        fields = [
            'first_name', 'last_name', 'email',
            'phone', 'address', 'city', 'state', 'zip_code',
            'snowmobile_brand',
        ]
        widgets = {
            'state': forms.TextInput(attrs={'placeholder': 'MN'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load field config from DB
        try:
            config = {f.field_name: f for f in RegistrationField.objects.all()}
        except Exception:
            config = {}

        # Remove disabled optional fields; apply labels and required flags
        for field_name in _OPTIONAL_FIELDS:
            cfg = config.get(field_name)
            if cfg is None or not cfg.is_enabled:
                self.fields.pop(field_name, None)
            else:
                if cfg.label:
                    self.fields[field_name].label = cfg.label
                self.fields[field_name].required = cfg.is_required

        # Build dynamic layout based on remaining fields
        personal_fields = [
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('email', css_class='col-md-6'),
                *(([Column('phone', css_class='col-md-6')]) if 'phone' in self.fields else [])),
        ]

        address_fields = []
        if 'address' in self.fields:
            address_fields.append('address')
        addr_row = []
        for f, css in [('city', 'col-md-5'), ('state', 'col-md-3'), ('zip_code', 'col-md-4')]:
            if f in self.fields:
                addr_row.append(Column(f, css_class=css))
        if addr_row:
            address_fields.append(Row(*addr_row))

        layout_items = [Fieldset('Personal Information', *personal_fields)]
        if address_fields:
            layout_items.append(Fieldset('Address', *address_fields))
        if 'snowmobile_brand' in self.fields:
            layout_items.append(Fieldset('Snowmobile Info', 'snowmobile_brand'))
        layout_items.append(Fieldset('Account Setup',
            Row(Column('password1', css_class='col-md-6'), Column('password2', css_class='col-md-6')),
        ))
        layout_items.append(Submit('submit', 'Submit Application', css_class='btn btn-primary btn-lg mt-3'))

        self.helper = FormHelper()
        self.helper.layout = Layout(*layout_items)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def save(self, commit=True):
        member = super().save(commit=False)
        member.set_password(self.cleaned_data['password1'])
        member.membership_status = 'pending'
        if commit:
            member.save()
        return member


class MemberLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email Address', widget=forms.EmailInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Log In', css_class='btn btn-primary w-100 mt-2'),
        )
