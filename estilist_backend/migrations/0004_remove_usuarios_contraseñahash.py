# Generated by Django 5.1.2 on 2024-10-30 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0003_usuarios_idlogin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuarios',
            name='contraseñahash',
        ),
    ]
