# Generated by Django 5.1.2 on 2024-10-31 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estilist_backend', '0007_remove_usuarios_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarios',
            name='pais',
            field=models.CharField(blank=True, db_column='Pais', max_length=50, null=True),
        ),
    ]
