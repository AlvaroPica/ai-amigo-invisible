from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from secretsanta.models import Game, EmailLog

def send_game_emails(game):
    """
    Sends emails to all players in the game with their assignment.
    """
    assignments = game.assignments.all().select_related('giver', 'receiver')
    proxies = {p.dependent_id: p.proxy for p in game.proxies.all()}
    
    results = []
    
    for assignment in assignments:
        giver = assignment.giver
        receiver = assignment.receiver
        
        # Check if giver is a proxy for someone
        proxy_for_list = []
        # This is inefficient, better to query properly or map
        # But for <20 players it's fine.
        # Let's use the reverse relation on Player if possible, but we have game.proxies
        
        # Find if 'giver' is a proxy for anyone
        # dependent_proxy table: dependent -> proxy
        # We want to find dependents where proxy == giver
        dependents_proxied = [dp.dependent for dp in game.proxies.filter(proxy=giver)]
        
        context = {
            'game': game,
            'giver': giver,
            'receiver': receiver,
            'dependents_proxied': dependents_proxied,
        }
        
        subject = f"Amigo Invisible: {game.name}"
        html_message = render_to_string('secretsanta/email_notification.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,  # Usar el email configurado
                [giver.email],
                html_message=html_message,
                fail_silently=False,
            )
            status = EmailLog.Status.SENT
            error = ''
        except Exception as e:
            status = EmailLog.Status.FAILED
            error = str(e)
            
        # Log result
        EmailLog.objects.create(
            game=game,
            player=giver,
            to_email=giver.email,
            status=status,
            error_message=error
        )
        
    # Update game status if all sent?
    # Or just mark as emails_sent if at least attempted?
    # Requirement: "Si hay fallos, el estado pasa a emails_error. Si todos se envían, emails_sent."
    
    failed_count = EmailLog.objects.filter(game=game, status=EmailLog.Status.FAILED).count()
    if failed_count > 0:
        game.status = Game.Status.EMAILS_ERROR
    else:
        game.status = Game.Status.EMAILS_SENT
    game.save()

def retry_email(email_log):
    """
    Retries sending a specific email.
    """
    game = email_log.game
    giver = email_log.player
    
    # Re-fetch assignment
    try:
        assignment = game.assignments.get(giver=giver)
    except:
        email_log.status = EmailLog.Status.FAILED
        email_log.error_message = "Assignment not found"
        email_log.save()
        return

    receiver = assignment.receiver
    dependents_proxied = [dp.dependent for dp in game.proxies.filter(proxy=giver)]
    
    context = {
        'game': game,
        'giver': giver,
        'receiver': receiver,
        'dependents_proxied': dependents_proxied,
    }
    
    subject = f"Amigo Invisible: {game.name}"
    html_message = render_to_string('secretsanta/email_notification.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,  # Usar el email configurado
            [giver.email], # Use current email of player
            html_message=html_message,
            fail_silently=False,
        )
        email_log.status = EmailLog.Status.SENT
        email_log.error_message = ''
    except Exception as e:
        email_log.status = EmailLog.Status.FAILED
        email_log.error_message = str(e)
        
    email_log.save()
    
    # Update game status check
    # If no more failed logs, update to EMAILS_SENT
    # Note: This logic is a bit simplistic because we might have multiple logs for same player?
    # But let's assume we update the existing log or create new?
    # The requirement says "No se regenera el sorteo, solo el email."
    # "Editar email del jugador" -> implies we update Player.email
    
    # Check if any failed logs remain for this game
    # We should probably only care about the *latest* log for each player?
    # Or just check if there are any FAILED logs that haven't been superseded?
    # Let's keep it simple: if any log is FAILED, game is ERROR. 
    # But if we retry and succeed, we update that log to SENT.
    
    failed_count = EmailLog.objects.filter(game=game, status=EmailLog.Status.FAILED).count()
    if failed_count == 0:
        game.status = Game.Status.EMAILS_SENT
        game.save()
