from django.contrib import admin

from .models import Transcript


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("video_title", "url", "created_at")
    search_fields = ("video_title", "url", "transcript_content")
    readonly_fields = ("created_at",)
