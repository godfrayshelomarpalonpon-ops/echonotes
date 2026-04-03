"""
ADD this model to the bottom of your blog/models.py
(before the signal handlers)
"""


class AIBroadcast(models.Model):
    """
    Stores AI-generated broadcasts about platform activity.
    Generated hourly by the ai_monitor management command.
    """
    message = models.TextField()
    stats = models.TextField(blank=True)  # JSON string of stats
    created_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'Broadcast at {self.created_date}: {self.message[:50]}'

    def get_stats(self):
        import json
        try:
            return json.loads(self.stats)
        except Exception:
            return {}
