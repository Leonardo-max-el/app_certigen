from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import uuid

class Estudiante(models.Model):
    TIPOS_PARTICIPANTE = [
        ('ponente', 'Ponente'),
        ('asistente', 'Asistente'),
        ('organizador', 'Organizador'),
        ('sponsor', 'Sponsor'),
    ]
    
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de Estudiante")
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    tipo_participante = models.CharField(max_length=20, choices=TIPOS_PARTICIPANTE, verbose_name="Tipo de Participante")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['nombre_completo']
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.dni}"


class Certificado(models.Model):
    estudiante = models.OneToOneField(
        Estudiante, 
        on_delete=models.CASCADE, 
        related_name='certificado'
    )
    codigo_unico = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        verbose_name="Código Único"
    )
    archivo_pdf = models.BinaryField(
        verbose_name="Archivo PDF",
        help_text="Certificado en formato PDF",
        null=True,
        blank=True
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Generación")
    veces_descargado = models.IntegerField(default=0, verbose_name="Veces Descargado")
    ultima_descarga = models.DateTimeField(null=True, blank=True, verbose_name="Última Descarga")
    
    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Certificado - {self.estudiante.nombre_completo}"
    
    @property
    def url_publica(self):
        """URL pública para ver el certificado (para el QR)"""
        from django.conf import settings
        return f"{settings.SITE_URL}/certificado/{self.codigo_unico}/"


class LogDescarga(models.Model):
    """Registro de cada descarga de certificado"""
    certificado = models.ForeignKey(
        Certificado, 
        on_delete=models.CASCADE, 
        related_name='descargas'
    )
    fecha_descarga = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log de Descarga"
        verbose_name_plural = "Logs de Descargas"
        ordering = ['-fecha_descarga']
    
    def __str__(self):
        return f"{self.certificado.estudiante.nombre_completo} - {self.fecha_descarga}"