# Generated by Django 4.1.5 on 2023-01-30 12:24

from django.db import migrations, models

from apps.participants.models import NO_LINE_START


def penalty_reason(apps, schema):
    Penalty = apps.get_model('participants', 'Penalty')

    penalties = Penalty.objects.filter(penalty=10)
    for penalty in penalties:
        penalty.reason = NO_LINE_START
        penalty.save()


class Migration(migrations.Migration):
    dependencies = [
        ('participants', '0003_penalty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='penalty',
            name='reason',
            field=models.CharField(
                blank=True,
                choices=[('NO_LINE_START', 'Salida sin estacha'), ('NULL_START', 'Salida nula'), ('BLADE_TOUCH', 'Toque de palas')],
                default=None,
                max_length=500,
                null=True
            ),
        ),
        migrations.RunPython(penalty_reason, reverse_code=migrations.RunPython.noop),
    ]
