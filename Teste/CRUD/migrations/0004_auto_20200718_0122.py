# Generated by Django 3.0.8 on 2020-07-18 04:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('CRUD', '0003_auto_20200718_0121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posicaoveiculo',
            name='VeiculoId',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='posicao_veiculo', serialize=False, to='CRUD.Veiculo'),
        ),
    ]
