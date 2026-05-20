from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from core.models import ClubStats, Officer, OfficerTitle, Sponsor, Announcement, TrailCondition, TrailWorkLog


class ClubStatsForm(forms.ModelForm):
    class Meta:
        model = ClubStats
        fields = ['members_count', 'miles_maintained', 'annual_budget', 'supporting_landowners']
        labels = {
            'members_count': 'Active Members',
            'miles_maintained': 'Miles of Trail Maintained',
            'annual_budget': 'Annual Trail Budget ($)',
            'supporting_landowners': 'Supporting Landowners',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('members_count', css_class='col-md-6'),
                Column('miles_maintained', css_class='col-md-6'),
            ),
            Row(
                Column('annual_budget', css_class='col-md-6'),
                Column('supporting_landowners', css_class='col-md-6'),
            ),
            Submit('submit', 'Save Stats', css_class='btn btn-primary mt-3'),
        )


class OfficerForm(forms.ModelForm):
    class Meta:
        model = Officer
        fields = ['name', 'title', 'snowmobile_brand', 'email', 'phone', 'photo', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate title choices dynamically from OfficerTitle model
        title_choices = [('', '— Select a title —')] + [
            (t.name, t.name) for t in OfficerTitle.objects.all()
        ]
        self.fields['title'] = forms.ChoiceField(choices=title_choices)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('title', css_class='col-md-6'),
            ),
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone', css_class='col-md-6'),
            ),
            Row(
                Column('snowmobile_brand', css_class='col-md-6'),
                Column('order', css_class='col-md-6'),
            ),
            'photo',
            Submit('submit', 'Save Officer', css_class='btn btn-primary mt-3'),
        )


class SponsorForm(forms.ModelForm):
    class Meta:
        model = Sponsor
        fields = ['name', 'website', 'description', 'logo', 'order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('order', css_class='col-md-4'),
            ),
            'website',
            'description',
            Row(
                Column('logo', css_class='col-md-8'),
                Column('is_active', css_class='col-md-4 d-flex align-items-end pb-3'),
            ),
            Submit('submit', 'Save Sponsor', css_class='btn btn-primary mt-3'),
        )


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'visibility', 'is_pinned']
        widgets = {'body': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            'body',
            'visibility',
            Field('is_pinned'),
        )


class TrailConditionForm(forms.ModelForm):
    class Meta:
        model = TrailCondition
        fields = ['title', 'trail', 'status', 'body', 'visibility', 'is_pinned', 'lat', 'lng']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
            'lat':  forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'optional'}),
            'lng':  forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'optional'}),
        }

    def __init__(self, *args, **kwargs):
        # Optional ?lat=&lng= URL query params pre-fill the form
        initial = kwargs.pop('initial', {}) or {}
        super().__init__(*args, **kwargs)
        if initial:
            for k, v in initial.items():
                self.fields[k].initial = v
        # Trail dropdown shows "— Not specific to one trail —" as the empty option
        self.fields['trail'].empty_label = '— Not specific to one trail —'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='col-md-8'),
                Column('status', css_class='col-md-4'),
            ),
            'trail',
            'body',
            'visibility',
            Field('is_pinned'),
            Row(
                Column('lat', css_class='col-6'),
                Column('lng', css_class='col-6'),
            ),
        )


class TrailWorkLogForm(forms.ModelForm):
    class Meta:
        model = TrailWorkLog
        fields = ['date', 'title', 'trail', 'description', 'volunteers', 'hours']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trail'].empty_label = '— Not specific to one trail —'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='col-md-4'),
                Column('volunteers', css_class='col-md-4'),
                Column('hours', css_class='col-md-4'),
            ),
            'title',
            'trail',
            'description',
        )
