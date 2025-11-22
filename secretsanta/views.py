from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction

from .models import Game, Player, ForbiddenPair, Assignment, DependentProxy, EmailLog
from .services.draw import draw_names, assign_proxies, DrawError
from .forms import GameForm, PlayerForm, ForbiddenPairForm

# Placeholder for forms, need to create them
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.generic import FormView

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name', 'description']

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'email', 'is_dependent', 'note']

class ForbiddenPairForm(forms.ModelForm):
    class Meta:
        model = ForbiddenPair
        fields = ['giver', 'receiver']
    
    def __init__(self, *args, **kwargs):
        game = kwargs.pop('game', None)
        super().__init__(*args, **kwargs)
        if game:
            self.fields['giver'].queryset = Player.objects.filter(game=game)
            self.fields['receiver'].queryset = Player.objects.filter(game=game)

class GameListView(LoginRequiredMixin, ListView):
    model = Game
    template_name = 'secretsanta/game_list.html'
    context_object_name = 'games'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Game.objects.all().order_by('-created_at')
        return Game.objects.filter(owner=self.request.user).order_by('-created_at')

class GameCreateView(LoginRequiredMixin, CreateView):
    model = Game
    form_class = GameForm
    template_name = 'secretsanta/game_form.html'
    success_url = reverse_lazy('game_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    template_name = 'secretsanta/game_detail.html'
    context_object_name = 'game'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Game.objects.all()
        return Game.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.object
        context['players'] = game.players.all()
        context['forbidden_pairs'] = game.forbidden_pairs.all()
        
        # Solo mostrar resultados si es superusuario
        if self.request.user.is_superuser:
            context['assignments'] = game.assignments.all().select_related('giver', 'receiver')
            context['proxies'] = game.proxies.all().select_related('dependent', 'proxy')
            context['can_view_results'] = True
        else:
            context['assignments'] = []
            context['proxies'] = []
            context['can_view_results'] = False
            
        return context

class GameUpdateView(LoginRequiredMixin, UpdateView):
    model = Game
    form_class = GameForm
    template_name = 'secretsanta/game_form.html'
    
    def get_queryset(self):
        return Game.objects.filter(owner=self.request.user)
        
    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'pk': self.object.pk})

class PlayerCreateView(LoginRequiredMixin, CreateView):
    model = Player
    form_class = PlayerForm
    template_name = 'secretsanta/player_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.game = get_object_or_404(Game, pk=kwargs['game_pk'], owner=request.user)
        return super().dispatch(request, *args, **kwargs)



class PlayerUpdateView(LoginRequiredMixin, UpdateView):
    model = Player
    form_class = PlayerForm
    template_name = 'secretsanta/player_form.html'

    def get_queryset(self):
        return Player.objects.filter(game__owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'pk': self.object.game.pk})

class PlayerDeleteView(LoginRequiredMixin, DeleteView):
    model = Player
    template_name = 'secretsanta/player_confirm_delete.html'

    def get_queryset(self):
        return Player.objects.filter(game__owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'pk': self.object.game.pk})

def player_import(request, game_pk):
    """Vista para importar jugadores desde un archivo CSV"""
    game = get_object_or_404(Game, pk=game_pk, owner=request.user)
    
    if game.status != Game.Status.DRAFT:
        messages.error(request, "Solo puedes importar jugadores en juegos en estado borrador.")
        return redirect('game_detail', pk=game_pk)
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, "Por favor selecciona un archivo.")
            return redirect('player_import', game_pk=game_pk)
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "El archivo debe ser un CSV.")
            return redirect('player_import', game_pk=game_pk)
        
        try:
            import csv
            import io
            
            # Leer el archivo
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Validar columnas requeridas
            required_fields = ['nombre', 'email']
            if not all(field in reader.fieldnames for field in required_fields):
                messages.error(request, f"El archivo debe tener las columnas: {', '.join(required_fields)}")
                return redirect('player_import', game_pk=game_pk)
            
            # Procesar filas
            created_count = 0
            skipped_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # start=2 porque la fila 1 es el encabezado
                nombre = row.get('nombre', '').strip()
                email = row.get('email', '').strip()
                dependiente_str = row.get('dependiente', 'no').strip().lower()
                nota = row.get('nota', '').strip()
                
                # Validaciones
                if not nombre or not email:
                    errors.append(f"Fila {row_num}: Nombre y email son obligatorios")
                    continue
                
                # Verificar si ya existe
                if Player.objects.filter(game=game, email=email).exists():
                    skipped_count += 1
                    continue
                
                # Convertir dependiente
                is_dependent = dependiente_str in ['si', 'sí', 'yes', 'true', '1']
                
                # Crear jugador
                try:
                    Player.objects.create(
                        game=game,
                        name=nombre,
                        email=email,
                        is_dependent=is_dependent,
                        note=nota
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Fila {row_num}: Error al crear jugador - {str(e)}")
            
            # Mensajes de resultado
            if created_count > 0:
                messages.success(request, f"✅ {created_count} jugador(es) importado(s) correctamente.")
            if skipped_count > 0:
                messages.warning(request, f"⚠️ {skipped_count} jugador(es) omitido(s) (ya existían).")
            if errors:
                for error in errors[:5]:  # Mostrar solo los primeros 5 errores
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f"... y {len(errors) - 5} errores más.")
            
            return redirect('game_detail', pk=game_pk)
            
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            return redirect('player_import', game_pk=game_pk)
    
    return render(request, 'secretsanta/player_import.html', {'game': game})


class ForbiddenPairCreateView(LoginRequiredMixin, CreateView):
    model = ForbiddenPair
    form_class = ForbiddenPairForm
    template_name = 'secretsanta/forbidden_pair_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.game = get_object_or_404(Game, pk=kwargs['game_pk'], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['game'] = self.game
        return kwargs

    def form_valid(self, form):
        form.instance.game = self.game
        if 'is_reciprocal' in self.request.POST:
            form.instance.is_reciprocal = True
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'pk': self.game.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['game'] = self.game
        return context

class ForbiddenPairDeleteView(LoginRequiredMixin, DeleteView):
    model = ForbiddenPair
    template_name = 'secretsanta/forbidden_pair_confirm_delete.html'

    def get_queryset(self):
        return ForbiddenPair.objects.filter(game__owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('game_detail', kwargs={'pk': self.object.game.pk})

@transaction.atomic
def draw_game(request, pk):
    game = get_object_or_404(Game, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        try:
            # 1. Draw names
            draw_names(game)
            
            # 2. Assign proxies
            assign_proxies(game)
            
            # 3. Update status
            game.status = Game.Status.DRAWN
            game.save()
            
            messages.success(request, "Sorteo realizado con éxito!")
            
        except DrawError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")
            
    return redirect('game_detail', pk=pk)

def reset_draw(request, pk):
    game = get_object_or_404(Game, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        if game.status != Game.Status.DRAFT:
             # Allow reset if drawn or error?
             # Requirement: "Si se quiere rehacer, se debe borrar antes."
             # "El sorteo se realiza solo cuando el juego está en draft."
             # So we need a way to go back to draft.
             pass
        
        # Delete assignments and proxies
        game.assignments.all().delete()
        game.proxies.all().delete()
        game.email_logs.all().delete() # Also clear email logs? Maybe keep history? 
        # "Si se quiere repetir un sorteo: El organizador puede eliminar el sorteo"
        
        game.status = Game.Status.DRAFT
        game.save()
        messages.success(request, "Sorteo eliminado. El juego vuelve a borrador.")
        
    return redirect('game_detail', pk=pk)

def send_emails(request, pk):
    game = get_object_or_404(Game, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        if game.status not in [Game.Status.DRAWN, Game.Status.EMAILS_ERROR, Game.Status.EMAILS_SENT]:
            messages.error(request, "El juego no está listo para enviar correos.")
        else:
            from .services.email import send_game_emails
            send_game_emails(game)
            messages.success(request, "Proceso de envío de correos completado.")
            
    return redirect('game_detail', pk=pk)

class EmailErrorListView(LoginRequiredMixin, ListView):
    model = EmailLog
    template_name = 'secretsanta/email_error_list.html'
    context_object_name = 'logs'
    
    def dispatch(self, request, *args, **kwargs):
        self.game = get_object_or_404(Game, pk=kwargs['pk'], owner=request.user)
        return super().dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        return EmailLog.objects.filter(game=self.game, status=EmailLog.Status.FAILED)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['game'] = self.game
        return context

class PlayerEmailUpdateView(LoginRequiredMixin, UpdateView):
    model = Player
    fields = ['email']
    template_name = 'secretsanta/player_email_form.html'
    
    def get_queryset(self):
        return Player.objects.filter(game__owner=self.request.user)
        
    def get_success_url(self):
        return reverse_lazy('email_errors', kwargs={'pk': self.object.game.pk})

def retry_email_view(request, pk):
    log = get_object_or_404(EmailLog, pk=pk, game__owner=request.user)
    
    if request.method == 'POST':
        from .services.email import retry_email
        retry_email(log)
        if log.status == EmailLog.Status.SENT:
            messages.success(request, f"Email enviado a {log.player.name}")
        else:
            messages.error(request, f"Fallo al enviar: {log.error_message}")
            
    return redirect('email_errors', pk=log.game.pk)

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'Cuenta creada para {user.username}. Ya puedes iniciar sesión.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar clases de Bootstrap a los campos del formulario
        for field in context['form'].fields.values():
            field.widget.attrs['class'] = 'form-control'
        return context
