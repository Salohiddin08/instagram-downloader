from django import forms
from .models import DownloadedVideo


class VideoDownloadForm(forms.ModelForm):
    class Meta:
        model = DownloadedVideo
        fields = ['url']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Instagram video URL (post, reel, story, etc.)',
                'required': True
            })
        }
    
    def clean_url(self):
        url = self.cleaned_data['url']
        # Basic Instagram URL validation
        if 'instagram.com' not in url:
            raise forms.ValidationError("Please enter a valid Instagram URL.")
        return url