import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('care', '0003_notificationdelivery_familyaccess'),
    ]

    operations = [
        migrations.CreateModel(
            name='CareProcedure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('instruction', models.TextField()),
                ('frequency', models.CharField(choices=[('ONCE', 'Uma vez'), ('DAILY', 'Diária'), ('WEEKLY', 'Semanal'), ('SELECTED_DAYS', 'Dias selecionados')], default='ONCE', max_length=20)),
                ('scheduled_times', models.JSONField(default=list)),
                ('weekdays', models.JSONField(blank=True, default=list)),
                ('starts_on', models.DateField()),
                ('ends_on', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Rascunho'), ('PUBLISHED', 'Publicado'), ('PAUSED', 'Pausado'), ('ENDED', 'Encerrado')], default='DRAFT', max_length=20)),
                ('version', models.PositiveIntegerField(default=1)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='approved_procedures', to='care.staffprofile')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_procedures', to='care.staffprofile')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procedures', to='care.careplan')),
                ('supersedes', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='next_versions', to='care.careprocedure')),
            ],
        ),
        migrations.AddField(
            model_name='caretask',
            name='procedure',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='occurrences', to='care.careprocedure'),
        ),
    ]
