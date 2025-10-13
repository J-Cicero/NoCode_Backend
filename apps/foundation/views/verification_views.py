"""
Vues pour la vérification des entreprises.
Expose les APIs pour la vérification KYB, upload de documents, etc.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from ..services.verification_service import VerificationService
from ..serializers import (
    DocumentVerificationSerializer, DocumentUploadCreateSerializer
)
from ..models import DocumentVerification, DocumentUpload, Organization


User = get_user_model()


class StartVerificationView(APIView):
    """Vue pour démarrer le processus de vérification."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, entreprise_id):
        """Démarre la vérification pour une entreprise."""
        verification_service = VerificationService(user=request.user)
        result = verification_service.start_verification_process(entreprise_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class VerificationStatusView(APIView):
    """Vue pour consulter le statut de vérification."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, entreprise_id):
        """Récupère le statut de vérification d'une entreprise."""
        verification_service = VerificationService(user=request.user)
        result = verification_service.get_verification_status(entreprise_id)
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class DocumentUploadView(APIView):
    """Vue pour l'upload de documents."""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, verification_id):
        """Upload un document pour la vérification."""
        serializer = DocumentUploadCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            verification_service = VerificationService(user=request.user)
            result = verification_service.upload_document(
                verification_id=verification_id,
                document_type=serializer.validated_data['document_type'],
                file=serializer.validated_data['file'],
                description=serializer.validated_data.get('description', '')
            )
            
            if result.success:
                return Response(result.data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result.error_message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentReviewView(APIView):
    """Vue pour la révision de documents (admin seulement)."""
    
    permission_classes = [IsAdminUser]
    
    def put(self, request, document_id):
        """Révise un document uploadé."""
        status_value = request.data.get('status')
        reviewer_comments = request.data.get('reviewer_comments', '')
        
        if not status_value:
            return Response({
                'error': 'Statut requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        verification_service = VerificationService(user=request.user)
        result = verification_service.review_document(
            document_id=document_id,
            status=status_value,
            reviewer_comments=reviewer_comments
        )
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


class CompleteVerificationView(APIView):
    """Vue pour finaliser une vérification (admin seulement)."""
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, verification_id):
        """Finalise une vérification."""
        final_status = request.data.get('final_status')
        admin_comments = request.data.get('admin_comments', '')
        
        if not final_status:
            return Response({
                'error': 'Statut final requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        verification_service = VerificationService(user=request.user)
        result = verification_service.complete_verification(
            verification_id=verification_id,
            final_status=final_status,
            admin_comments=admin_comments
        )
        
        if result.success:
            return Response(result.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result.error_message
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_verifications(request):
    """Liste les vérifications en attente (admin seulement)."""
    verifications = DocumentVerification.objects.filter(
        status__in=['EN_COURS', 'PRET_POUR_VALIDATION']
    ).select_related('entreprise', 'submitted_by').order_by('-created_at')
    
    verifications_data = []
    for verification in verifications:
        verifications_data.append({
            'id': verification.id,
            'status': verification.status,
            'entreprise': {
                'id': verification.entreprise.id,
                'nom': verification.entreprise.nom,
                'siret': verification.entreprise.siret,
            },
            'submitted_by': {
                'id': verification.submitted_by.id,
                'full_name': verification.submitted_by.full_name,
                'email': verification.submitted_by.email,
            },
            'documents_count': verification.documents.count(),
            'created_at': verification.created_at.isoformat(),
        })
    
    return Response({
        'verifications': verifications_data,
        'total_count': len(verifications_data)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def verification_stats(request):
    """Récupère les statistiques de vérification (admin seulement)."""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats_data = {
        'total_verifications': DocumentVerification.objects.count(),
        'pending_verifications': DocumentVerification.objects.filter(
            status__in=['EN_ATTENTE', 'EN_COURS', 'PRET_POUR_VALIDATION']
        ).count(),
        'approved_verifications': DocumentVerification.objects.filter(
            status='APPROUVE'
        ).count(),
        'rejected_verifications': DocumentVerification.objects.filter(
            status='REJETE'
        ).count(),
        'verifications_this_month': DocumentVerification.objects.filter(
            created_at__gte=current_month
        ).count(),
        'average_processing_time_days': 0,  # À calculer
        'verifications_by_status': {},
    }
    
    # Répartition par statut
    status_counts = DocumentVerification.objects.values('status').annotate(
        count=Count('id')
    )
    
    for status_data in status_counts:
        stats_data['verifications_by_status'][status_data['status']] = status_data['count']
    
    return Response(stats_data, status=status.HTTP_200_OK)
