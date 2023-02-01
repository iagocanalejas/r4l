# Generated by Django 4.1.5 on 2023-01-16 14:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('races', '0008_race_cancellation_reasons'),
    ]

    operations = [
        migrations.AlterField(
            model_name='race',
            name='modality',
            field=models.CharField(
                choices=[('TRAINERA', 'Trainera'), ('VETERAN', 'Veteranos'), ('TRAINERILLA', 'Trainerilla'), ('BATEL', 'Batel')],
                default='TRAINERA',
                max_length=15
            ),
        ),
    ]
