# Generated manually to remove Entreprise model and fix DocumentVerification

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foundation', '0001_initial'),
    ]

    operations = [
        # 1. Supprimer la référence entreprise dans DocumentVerification
        migrations.RemoveField(
            model_name='documentverification',
            name='entreprise',
        ),
        
        # 2. Ajouter la référence organization dans DocumentVerification
        migrations.AddField(
            model_name='documentverification',
            name='organization',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='verification',
                to='foundation.organization',
                verbose_name='Organisation',
                null=True  # Temporairement nullable pour la migration
            ),
        ),
        
        # 3. Supprimer le modèle Entreprise complètement
        migrations.DeleteModel(
            name='Entreprise',
        ),
        
        # 4. Rendre organization non-nullable après migration des données
        migrations.AlterField(
            model_name='documentverification',
            name='organization',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='verification',
                to='foundation.organization',
                verbose_name='Organisation'
            ),
        ),
    ]
