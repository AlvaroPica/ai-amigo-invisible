from django import forms
from .models import Game, Player, ForbiddenPair

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'email', 'is_dependent', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_dependent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ForbiddenPairForm(forms.ModelForm):
    is_reciprocal = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='¿Es recíproca? (ambos no se regalan entre sí)'
    )

    class Meta:
        model = ForbiddenPair
        fields = ['giver', 'receiver', 'is_reciprocal']
        widgets = {
            'giver': forms.Select(attrs={'class': 'form-select'}),
            'receiver': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'giver': 'Quien regala',
            'receiver': 'A quien regala',
        }
    
    def __init__(self, *args, **kwargs):
        game = kwargs.pop('game', None)
        super().__init__(*args, **kwargs)
        if game:
            self.fields['giver'].queryset = Player.objects.filter(game=game)
            self.fields['receiver'].queryset = Player.objects.filter(game=game)
            
    def clean(self):
        cleaned_data = super().clean()
        giver = cleaned_data.get("giver")
        receiver = cleaned_data.get("receiver")

        if giver and receiver and giver == receiver:
            raise forms.ValidationError("Giver and receiver cannot be the same person.")
