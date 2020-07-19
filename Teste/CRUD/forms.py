from django import forms
from .models import Parada, Linha, Veiculo, PosicaoVeiculo

class ParadaForm(forms.ModelForm):
    class Meta:
        model = Parada
        fields = ['Id', 'Name', 'Latitude', 'Longitude']

class LinhaForm(forms.ModelForm):
    class Meta:
        model = Linha
        fields = ['Id', 'Name', 'Paradas']

class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ['Id','Name','Modelo','LinhaId']

class PosicaoForm(forms.ModelForm):
    class Meta:
        model = PosicaoVeiculo
        fields = ['Latitude','Longitude','VeiculoId']