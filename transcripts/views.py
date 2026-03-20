from django.shortcuts import render

from .forms import YouTubeUrlForm
from .models import Transcript
from .services import fetch_transcript_from_supadata, fetch_youtube_title


def index(request):
    form = YouTubeUrlForm()
    transcript_obj = None
    error_message = None

    if request.method == "POST":
        form = YouTubeUrlForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]
            result = fetch_transcript_from_supadata(url)
            if result.get("ok") and result.get("transcript"):
                title = fetch_youtube_title(url)
                transcript_obj = Transcript.objects.create(
                    url=url,
                    video_title=title,
                    transcript_content=result["transcript"],
                )
            else:
                error_message = result.get("error") or "Transkript alınamadı."

    return render(
        request,
        "transcripts/index.html",
        {
            "form": form,
            "transcript": transcript_obj,
            "error_message": error_message,
        },
    )
