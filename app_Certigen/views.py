from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Estudiante, Certificado, LogDescarga
from .forms import LoginEstudianteForm, CargarExcelForm
from .utils import cargar_estudiantes_desde_excel,generar_certificado_pdf


# ============= VISTAS PÚBLICAS =============

def home(request):
    """Página de inicio con opciones de login"""
    return render(request, 'certigen/home.html')


def login_estudiante_view(request):
    """Login para estudiantes"""
    if request.method == 'POST':
        form = LoginEstudianteForm(request.POST)
        if form.is_valid():
            estudiante = form.cleaned_data['estudiante']
            # Guarda el ID del estudiante en la sesión
            request.session['estudiante_id'] = estudiante.id
            return redirect('panel_estudiante')
    else:
        form = LoginEstudianteForm()
    
    return render(request, 'certigen/login_estudiante.html', {'form': form})


def panel_estudiante_view(request):
    """Panel del estudiante después de login"""
    estudiante_id = request.session.get('estudiante_id')
    
    if not estudiante_id:
        return redirect('login_estudiante')
    
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    # Verifica si ya tiene certificado generado
    tiene_certificado = hasattr(estudiante, 'certificado')
    
    context = {
        'estudiante': estudiante,
        'tiene_certificado': tiene_certificado
    }
    
    return render(request, 'certigen/panel_estudiante.html', context)

def descargar_certificado_view(request):
    """Descarga el certificado del estudiante en formato PDF"""
    estudiante_id = request.session.get('estudiante_id')
    
    if not estudiante_id:
        return redirect('login_estudiante')
    
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    
    print(f"\n{'='*60}")
    print(f"DESCARGA DE CERTIFICADO PDF")
    print(f"Estudiante: {estudiante.nombre_completo}")
    print(f"{'='*60}\n")
    
    try:
        # Genera o recupera el certificado PDF
        print("→ Llamando a generar_certificado_pdf...")
        pdf_bytes = generar_certificado_pdf(estudiante)
        
        print(f"→ Bytes recibidos: {len(pdf_bytes) if pdf_bytes else 0}")
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            raise Exception("El PDF generado está vacío")
        
        # Registra la descarga
        certificado = estudiante.certificado
        certificado.veces_descargado += 1
        certificado.ultima_descarga = timezone.now()
        certificado.save(update_fields=['veces_descargado', 'ultima_descarga'])
        
        print(f"✓ Descarga #{certificado.veces_descargado} registrada")
        
        # Crea log de descarga
        ip = request.META.get('REMOTE_ADDR')
        LogDescarga.objects.create(certificado=certificado, ip_address=ip)
        
        # Retorna el PDF
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'certificado_{estudiante.nombre_completo.replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_bytes)
        
        print(f"✓ PDF preparado para descarga: {filename}")
        print(f"✓ Tamaño: {len(pdf_bytes)} bytes")
        print(f"{'='*60}\n")
        
        return response
        
    except Exception as e:
        print(f"✗ ERROR en descarga: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        messages.error(request, f'Error al generar certificado: {str(e)}')
        return redirect('panel_estudiante')
        
    except Exception as e:
        print(f"ERROR en vista de descarga: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error al generar certificado: {str(e)}')
        return redirect('panel_estudiante')


def logout_estudiante_view(request):
    """Cierra sesión del estudiante"""
    request.session.flush()
    return redirect('home')




def descargar_certificado_publico(request, codigo_unico):
    """Descarga pública del certificado en PDF (desde QR)"""
    certificado = get_object_or_404(Certificado, codigo_unico=codigo_unico)
    
    print(f"\n→ Descarga pública del certificado: {certificado.estudiante.nombre_completo}")
    
    # Incrementa contador
    certificado.veces_descargado += 1
    certificado.save(update_fields=['veces_descargado'])
    
    # Registra descarga
    ip = request.META.get('REMOTE_ADDR')
    LogDescarga.objects.create(certificado=certificado, ip_address=ip)
    
    print(f"✓ Descarga pública #{certificado.veces_descargado} registrada\n")
    
    # Retorna PDF
    pdf_bytes = bytes(certificado.archivo_pdf)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f'certificado_{certificado.estudiante.nombre_completo.replace(" ", "_")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(pdf_bytes)
    
    return response

# ============= VISTAS ADMIN =============

def es_admin(user):
    """Verifica si el usuario es admin"""
    return user.is_authenticated and user.is_staff


def login_admin_view(request):
    """Login para administrador"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel_admin')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('panel_admin')
        else:
            messages.error(request, 'Credenciales inválidas o no tiene permisos de administrador')
    
    return render(request, 'certigen/login_admin.html')


@login_required
@user_passes_test(es_admin)
def panel_admin_view(request):
    """Panel de administración"""
    certificados = Certificado.objects.select_related('estudiante').all()
    total_estudiantes = Estudiante.objects.count()
    total_certificados = certificados.count()
    total_descargas = sum(c.veces_descargado for c in certificados)
    
    context = {
        'certificados': certificados,
        'total_estudiantes': total_estudiantes,
        'total_certificados': total_certificados,
        'total_descargas': total_descargas
    }
    
    return render(request, 'certigen/panel_admin.html', context)


@login_required
@user_passes_test(es_admin)
def cargar_excel_view(request):
    """Carga masiva de estudiantes desde Excel"""
    if request.method == 'POST':
        form = CargarExcelForm(request.POST, request.FILES)
        
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            
            try:
                resultados = cargar_estudiantes_desde_excel(archivo)
                
                messages.success(
                    request,
                    f'Carga completada: {resultados["exitosos"]} estudiantes agregados, '
                    f'{resultados["duplicados"]} duplicados'
                )
                
                if resultados['errores']:
                    for error in resultados['errores'][:10]:  # Muestra máximo 10 errores
                        messages.warning(request, error)
                
                return redirect('panel_admin')
                
            except Exception as e:
                messages.error(request, f'Error procesando archivo: {str(e)}')
    else:
        form = CargarExcelForm()
    
    return render(request, 'certigen/cargar_excel.html', {'form': form})


@login_required
@user_passes_test(es_admin)
def logout_admin_view(request):
    """Cierra sesión del admin"""
    logout(request)
    return redirect('home')