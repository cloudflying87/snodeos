from django import forms
from django.contrib.auth.forms import AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Member, RegistrationField


_OPTIONAL_FIELDS = ['phone', 'address', 'city', 'state', 'zip_code', 'snowmobile_brand']


class MembershipApplicationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    REFERRAL_CHOICES = [
        ('', '— Select one —'),
        ('Facebook', 'Facebook'),
        ('Friend or Family', 'Friend or Family'),
        ('Snowmobile Trail', 'Snowmobile Trail / Out Riding'),
        ('Local Business', 'Local Business'),
        ('MnUSA / State Club', 'MnUSA / State Snowmobile Association'),
        ('Google / Internet Search', 'Google / Internet Search'),
        ('Event or Show', 'Event or Show'),
        ('Other', 'Other (please describe below)'),
    ]
    referral_source = forms.ChoiceField(
        label='How did you find our club?',
        choices=REFERRAL_CHOICES,
        required=True,
    )
    referral_other = forms.CharField(
        label='Please describe',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Tell us more...'}),
    )

    ACCEPTS_TEXTS_CHOICES = [
        ('', '— Select —'),
        (True, 'Yes'),
        (False, 'No'),
    ]
    accepts_texts = forms.NullBooleanField(
        label='Can you receive text messages?',
        help_text='We send communications via email but at times text.',
        widget=forms.RadioSelect(choices=[('True', 'Yes'), ('False', 'No')]),
        required=True,
    )

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email',
            'phone', 'address', 'city', 'state', 'zip_code',
            'snowmobile_brand',
            'accepts_texts', 'num_snowmobiles', 'referral_source',
        ]
        widgets = {
            'state': forms.TextInput(attrs={'placeholder': 'MN'}),
            'num_snowmobiles': forms.NumberInput(attrs={'min': 0, 'max': 20}),
        }
        labels = {
            'num_snowmobiles': 'Number of Snowmobiles (MnUSA)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load configurable field config from DB
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

        # Build dynamic layout
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
            layout_items.append(Fieldset('Snowmobile Info',
                Row(
                    Column('snowmobile_brand', css_class='col-md-8'),
                    Column('num_snowmobiles', css_class='col-md-4'),
                ),
            ))
        else:
            layout_items.append(Fieldset('Snowmobile Info', 'num_snowmobiles'))

        layout_items.append(Fieldset('Communication',
            'accepts_texts',
        ))
        layout_items.append(Fieldset('Additional Info',
            'referral_source',
            'referral_other',
        ))
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

    def clean_referral_source(self):
        choice = self.cleaned_data.get('referral_source', '')
        other = self.data.get('referral_other', '').strip()
        if choice == 'Other':
            return f'Other: {other}' if other else 'Other'
        return choice

    def clean_accepts_texts(self):
        val = self.cleaned_data.get('accepts_texts')
        if val == 'True':
            return True
        if val == 'False':
            return False
        return val

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
