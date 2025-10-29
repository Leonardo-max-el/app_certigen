from django.contrib import admin
from .models import Estudiante, Certificado, LogDescarga

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni', 'codigo', 'tipo_participante', 'fecha_registro')
    list_filter = ('tipo_participante', 'fecha_registro')
    search_fields = ('nombre_completo', 'dni', 'codigo')
    ordering = ('-fecha_registro',)

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'codigo_unico', 'fecha_generacion', 'veces_descargado', 'ultima_descarga')
    list_filter = ('fecha_generacion',)
    search_fields = ('estudiante__nombre_completo', 'codigo_unico')
    readonly_fields = ('codigo_unico', 'fecha_generacion', 'veces_descargado', 'ultima_descarga')
    ordering = ('-fecha_generacion',)

@admin.register(LogDescarga)
class LogDescargaAdmin(admin.ModelAdmin):
    list_display = ('certificado', 'fecha_descarga', 'ip_address')
    list_filter = ('fecha_descarga',)
    search_fields = ('certificado__estudiante__nombre_completo',)
    readonly_fields = ('certificado', 'fecha_descarga', 'ip_address')
    ordering = ('-fecha_descarga',)