from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Parada(models.Model):
    """Classe para as paradas"""
    Id = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=100)
    Latitude = models.DecimalField(max_digits=8, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    Longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    

    def __str__(self):
        return self.Name

class Linha(models.Model):
    """Classe para as linhas"""
    Id = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=100)
    Paradas = models.ManyToManyField(Parada, related_name='parada_linha',blank=True)

    def __str__(self):
        return self.Name

class Veiculo(models.Model):
    """Classe para os veiculos"""
    Id = models.BigIntegerField(primary_key=True)
    Name = models.CharField(max_length=100)
    Modelo = models.CharField(max_length=50)
    LinhaId = models.ForeignKey(Linha, on_delete=models.CASCADE, related_name='linha_veiculo')

    def __str__(self):
        return self.Name

class PosicaoVeiculo(models.Model):
    """Classe para as posicoes"""
    Latitude = models.DecimalField(max_digits=8, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    Longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    VeiculoId = models.OneToOneField(Veiculo, on_delete=models.CASCADE, primary_key=True, related_name='posicao_veiculo')

    def __str__(self):
        return 'Posição do veículo '+str(self.VeiculoId.Id)

class Chave(models.Model):
    """Classe para salvar as chaves (tokens) de verificação"""
    Token = models.BigIntegerField()

    def __str__(self):
        return str(self.id)