from django.db import models

class Test_Products_1764197753(models.Model):
    """
    Table générée automatiquement par NoCode
    Projet: Projet Test NoCode
    Créée le: 2025-11-26 22:55:53
    """
    

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_2_test_products_1764197753'
        verbose_name = 'Test Products'
        verbose_name_plural = 'Test Productss'
        ordering = ['-created_at']
    
    def __str__(self):
        return str(self.id)
