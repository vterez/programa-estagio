from django.contrib import admin
from .models import Parada, Linha, Veiculo, PosicaoVeiculo, Chave

admin.site.register(Parada)
admin.site.register(Linha)
admin.site.register(Veiculo)
admin.site.register(PosicaoVeiculo)
admin.site.register(Chave)

