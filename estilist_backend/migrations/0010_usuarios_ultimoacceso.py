# Generated by Django 5.1.2 on 2024-11-02 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0009_remove_usuarios_idlogin_usuarios_contrasena'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarios',
            name='ultimoacceso',
            field=models.DateTimeField(blank=True, db_column='UltimoAcceso', null=True),
        ),
    ]
