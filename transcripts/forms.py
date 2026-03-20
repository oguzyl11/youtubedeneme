from django import forms
from django.core.validators import URLValidator

from .services import extract_youtube_video_id


class YouTubeUrlForm(forms.Form):
    url = forms.CharField(
        label="YouTube video URL",
        max_length=500,
        widget=forms.URLInput(
            attrs={
                "class": (
                    "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 "
                    "text-slate-900 shadow-sm outline-none transition "
                    "placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                ),
                "placeholder": "https://www.youtube.com/watch?v=…",
                "autocomplete": "off",
            }
        ),
    )

    def clean_url(self):
        value = (self.cleaned_data.get("url") or "").strip()
        if not value:
            raise forms.ValidationError("URL gerekli.")
        validator = URLValidator()
        try:
            validator(value)
        except forms.ValidationError:
            raise forms.ValidationError("Geçerli bir URL girin.")
        if extract_youtube_video_id(value) is None:
            raise forms.ValidationError(
                "Geçerli bir YouTube video URL’si girin (watch, youtu.be, embed vb.)."
            )
        return value
