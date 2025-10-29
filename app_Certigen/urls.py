from django.urls import path
from . import views

urlpatterns = [
    # Públicas
    path('', views.home, name='home'),
    
    # Estudiante
    path('estudiante/login/', views.login_estudiante_view, name='login_estudiante'),
    path('estudiante/panel/', views.panel_estudiante_view, name='panel_estudiante'),
    path('estudiante/descargar/', views.descargar_certificado_view, name='descargar_certificado'),
    path('estudiante/logout/', views.logout_estudiante_view, name='logout_estudiante'),
    
    # Certificado público (QR)
    path('certificado/<uuid:codigo_unico>/', views.descargar_certificado_publico, name='ver_certificado_publico'),
    path('certificado/<uuid:codigo_unico>/descargar/', views.descargar_certificado_publico, name='descargar_certificado_publico'),
    
    # Admin
    path('admin-upla/login/', views.login_admin_view, name='login_admin'),
    path('admin-upla/panel/', views.panel_admin_view, name='panel_admin'),
    path('admin-upla/cargar-excel/', views.cargar_excel_view, name='cargar_excel'),
    path('admin-upla/logout/', views.logout_admin_view, name='logout_admin'),
]