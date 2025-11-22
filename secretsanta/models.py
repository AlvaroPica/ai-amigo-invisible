from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Game(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        DRAWN = 'drawn', _('Drawn')
        EMAILS_SENT = 'emails_sent', _('Emails Sent')
        EMAILS_ERROR = 'emails_error', _('Emails Error')

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    def __str__(self):
        return self.name

class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    is_dependent = models.BooleanField(default=False)
    note = models.TextField(blank=True, help_text="Optional note for the organizer or Santa")

    def __str__(self):
        return f"{self.name} ({self.game.name})"

class ForbiddenPair(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='forbidden_pairs')
    giver = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='forbidden_as_giver')
    receiver = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='forbidden_as_receiver')
    is_reciprocal = models.BooleanField(
        default=False, 
        help_text="Si es recíproca, también se prohíbe que receiver regale a giver"
    )

    class Meta:
        unique_together = ('giver', 'receiver')

    def __str__(self):
        if self.is_reciprocal:
            return f"{self.giver.name} ↔ {self.receiver.name} (recíproca)"
        return f"{self.giver.name} → {self.receiver.name}"

class Assignment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='assignments')
    giver = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='assignment_as_giver')
    receiver = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='assignment_as_receiver')

    class Meta:
        unique_together = ('game', 'giver') # Redundant with OneToOne but good for clarity
        # Also unique_together ('game', 'receiver') implicitly via OneToOne

    def __str__(self):
        return f"{self.giver.name} -> {self.receiver.name}"

class DependentProxy(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='proxies')
    dependent = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='proxy_assignment')
    proxy = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='proxy_for')

    def __str__(self):
        return f"{self.proxy.name} buys for {self.dependent.name}"

class EmailLog(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='email_logs')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='email_logs')
    to_email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email to {self.player.name}: {self.status}"
