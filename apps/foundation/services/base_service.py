from django.utils import timezone
from datetime import timedelta
from ..models import Abonnement, TypeAbonnement

def create_abonnement(client, type_abonnement: TypeAbonnement, moyen_de_paiement):
    """Créer un abonnement pour un client avec calcul de la date de fin"""
    date_debut = timezone.now()
    date_fin = date_debut + timedelta(days=type_abonnement.duree_jours)

    abonnement = Abonnement.objects.create(
        client=client,
        type_abonnement=type_abonnement,
        moyen_de_paiement=moyen_de_paiement,
        date_debut=date_debut,
        date_fin=date_fin,
        statut="actif"
    )
    return abonnement


def verifier_abonnement_actif(client):
    now = timezone.now()
    return Abonnement.objects.filter(
        client=client,
        date_debut__lte=now,
        date_fin__gte=now,
        statut="actif"
    ).exists()
