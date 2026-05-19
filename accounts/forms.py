from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Member


class MembershipApplicationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'state', 'zip_code', 'snowmobile_brand',
        ]
        widgets = {
            'state': forms.TextInput(attrs={'placeholder': 'MN'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Personal Information',
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('phone', css_class='col-md-6'),
                ),
            ),
            Fieldset('Address',
                'address',
                Row(
                    Column('city', css_class='col-md-5'),
                    Column('state', css_class='col-md-3'),
                    Column('zip_code', css_class='col-md-4'),
                ),
            ),
            Fieldset('Snowmobile Info',
                'snowmobile_brand',
            ),
            Fieldset('Account Setup',
                Row(
                    Column('password1', css_class='col-md-6'),
                    Column('password2', css_class='col-md-6'),
                ),
            ),
            Submit('submit', 'Submit Application', css_class='btn btn-primary btn-lg mt-3'),
        )

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
