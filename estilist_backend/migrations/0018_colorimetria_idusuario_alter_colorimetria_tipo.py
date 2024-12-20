# Generated by Django 5.1.2 on 2024-11-11 21:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0017_alter_colorimetria_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='colorimetria',
            name='idusuario',
            field=models.ForeignKey(blank=True, db_column='IdUsuario', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='estilist_backend.usuarios'),
        ),
        migrations.AlterField(
            model_name='colorimetria',
            name='tipo',
            field=models.CharField(blank=True, db_column='Tipo', db_comment='Ropa, Cabello, Joyeria, Tono', max_length=50, null=True),
        ),
    ]
