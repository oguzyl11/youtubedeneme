from django.db import models


class Transcript(models.Model):
    url = models.URLField(max_length=500)
    video_title = models.CharField(max_length=500)
    transcript_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.video_title[:50]}…" if len(self.video_title) > 50 else self.video_title
