from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from accounts.models import Member


class MemberEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'photo',
            'address', 'city', 'state', 'zip_code',
            'snowmobile_brand', 'num_snowmobiles',
            'membership_status', 'membership_year', 'date_approved', 'is_active',
            'dues_paid', 'dues_paid_date',
            'accepts_texts',
            'is_officer', 'officer_title', 'is_site_admin',
            'referral_source', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Personal Info',
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('phone', css_class='col-md-6'),
                ),
                'photo',
            ),
            Fieldset('Address',
                'address',
                Row(
                    Column('city', css_class='col-md-5'),
                    Column('state', css_class='col-md-3'),
                    Column('zip_code', css_class='col-md-4'),
                ),
            ),
            Fieldset('Snowmobile',
                Row(
                    Column('snowmobile_brand', css_class='col-md-6'),
                    Column('num_snowmobiles', css_class='col-md-6'),
                ),
            ),
            Fieldset('Membership',
                Row(
                    Column('membership_status', css_class='col-md-4'),
                    Column('membership_year', css_class='col-md-4'),
                    Column('date_approved', css_class='col-md-4'),
                ),
                Row(
                    Column('is_active', css_class='col-md-4'),
                    Column('accepts_texts', css_class='col-md-4'),
                ),
            ),
            Fieldset('Dues',
                Row(
                    Column('dues_paid', css_class='col-md-4'),
                    Column('dues_paid_date', css_class='col-md-4'),
                ),
            ),
            Fieldset('Roles',
                Row(
                    Column('is_officer', css_class='col-md-4'),
                    Column('officer_title', css_class='col-md-8'),
                ),
                'is_site_admin',
            ),
            Fieldset('Additional Info',
                'referral_source',
                'notes',
            ),
            Submit('submit', 'Save Changes', css_class='btn btn-primary mt-3'),
        )


class ProfileEditForm(forms.ModelForm):
    """Self-service form — members can only edit their own safe fields."""
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'state', 'zip_code', 'snowmobile_brand', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.layout = Layout(
            Fieldset('Profile Photo',
                'photo',
            ),
            Fieldset('Personal Info',
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                Row(
                    Column('phone', css_class='col-md-6'),
                    Column('snowmobile_brand', css_class='col-md-6'),
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
            Submit('submit', 'Save Profile', css_class='btn btn-primary mt-3'),
        )


class MemberFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search name or email...'}))
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Member.MEMBERSHIP_STATUS,
    )
