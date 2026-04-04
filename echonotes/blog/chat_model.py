# ADD this class to blog/models.py before the signals section

class ChatMessage(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.CharField(max_length=500)
    created_date = models.DateTimeField(default=timezone.now)
    room = models.CharField(max_length=50, default='general')

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.author.username}: {self.message[:40]}'
