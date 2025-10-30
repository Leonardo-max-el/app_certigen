import os
import qrcode
import subprocess
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from django.conf import settings
import tempfile
from datetime import datetime
import platform
import time


def generar_certificado_pdf(estudiante):
    """
    Genera certificado PDF desde plantilla Word
    Retorna: bytes del documento PDF generado
    """
    from .models import Certificado
    
    # Verifica si ya existe certificado con PDF
    try:
        certificado = Certificado.objects.get(estudiante=estudiante)
        
        # Si existe Y tiene contenido, retornarlo
        if certificado.archivo_pdf:
            print(f"✓ Certificado existente encontrado para {estudiante.nombre_completo}")
            print(f"✓ Tamaño: {len(certificado.archivo_pdf)} bytes")
            return bytes(certificado.archivo_pdf)
        else:
            print(f"⚠ Certificado existe pero está vacío, regenerando...")
            
    except Certificado.DoesNotExist:
        print(f"→ Creando nuevo certificado para {estudiante.nombre_completo}")
        certificado = Certificado.objects.create(estudiante=estudiante)
    
    # Ruta de la plantilla Word
    template_path = os.path.join(
        settings.BASE_DIR, 
        'app_Certigen', 
        'plantillas', 
        'certificado_template.docx'
    )
    
    print(f"→ Template: {template_path}")
    print(f"→ ¿Existe?: {os.path.exists(template_path)}")
    
    if not os.path.exists(template_path):
        certificado.delete()
        raise FileNotFoundError(f"Plantilla no encontrada en: {template_path}")
    
    # URL pública del certificado para el QR
    url_certificado = certificado.url_publica
    print(f"→ URL para QR: {url_certificado}")
    
    # Genera código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_certificado)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Guarda QR temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as qr_file:
        qr_img.save(qr_file.name)
        qr_path = qr_file.name
    
    print(f"→ QR generado: {qr_path}")
    
    try:
        # Carga la plantilla Word
        print("→ Cargando plantilla Word...")
        doc = DocxTemplate(template_path)
        
        # Crea imagen inline para el QR
        print("→ Insertando QR en documento...")
        qr_inline = InlineImage(doc, qr_path, width=Mm(35))
        
        # Contexto con datos del certificado
        context = {
            'nombre_completo': estudiante.nombre_completo.upper(),
            'tipo_participante': estudiante.get_tipo_participante_display().upper(),
            'codigo': str(certificado.codigo_unico)[:8].upper(),
            'fecha': datetime.now().strftime('%d de %B de %Y'),
            'qr_code': qr_inline,
        }
        
        print(f"→ Datos: {estudiante.nombre_completo} - {estudiante.get_tipo_participante_display()}")
        
        # Renderiza la plantilla
        print("→ Renderizando documento...")
        doc.render(context)
        
        # Guarda Word temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as docx_file:
            doc.save(docx_file.name)
            docx_path = docx_file.name
        
        print(f"→ Word temporal guardado: {docx_path}")
        
        # Verifica que el archivo temporal se haya creado
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"No se pudo crear el archivo temporal: {docx_path}")
        
        file_size = os.path.getsize(docx_path)
        print(f"→ Tamaño del Word: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("El archivo Word generado está vacío")
        
        # === CONVERSIÓN A PDF ===
        print("→ Convirtiendo Word a PDF...")
        pdf_bytes = convertir_word_a_pdf_bytes(docx_path)
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            raise Exception("La conversión a PDF falló o está vacía")
        
        print(f"✓ PDF generado: {len(pdf_bytes)} bytes")
        
        # Guarda el PDF en el modelo
        print("→ Guardando PDF en base de datos...")
        certificado.archivo_pdf = memoryview(pdf_bytes).tobytes()
        certificado.save(update_fields=['archivo_pdf'])
        
        # Verifica que se guardó
        certificado.refresh_from_db()
        if not certificado.archivo_pdf:
            raise Exception("El PDF no se guardó correctamente en la BD")
        
        print(f"✓ PDF guardado en BD: {len(certificado.archivo_pdf)} bytes")
        
        # Limpia archivos temporales
        print("→ Limpiando archivos temporales...")
        os.remove(docx_path)
        os.remove(qr_path)
        
        print("✓ Certificado PDF generado exitosamente\n")
        return pdf_bytes
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}\n")
        
        # Limpia archivos temporales en caso de error
        if 'qr_path' in locals() and os.path.exists(qr_path):
            os.remove(qr_path)
        if 'docx_path' in locals() and os.path.exists(docx_path):
            os.remove(docx_path)
        
        # Si el certificado se creó pero falló, lo eliminamos
        if certificado and not certificado.archivo_pdf:
            certificado.delete()
            
        raise Exception(f"Error generando certificado: {str(e)}")


def convertir_word_a_pdf_bytes(docx_path):
    """
    Convierte Word a PDF usando LibreOffice
    Retorna: bytes del PDF
    """
    import shutil
    
    output_dir = os.path.dirname(docx_path)
    
    print(f"   → Iniciando conversión con LibreOffice...")
    print(f"   → Sistema operativo: {platform.system()}")
    print(f"   → Archivo de entrada: {docx_path}")
    print(f"   → Directorio de salida: {output_dir}")
    
    # En Windows, cierra cualquier instancia previa de LibreOffice
    if platform.system() == 'Windows':
        print(f"   → Cerrando instancias previas de LibreOffice...")
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'soffice.exe'], 
                          capture_output=True, timeout=3)
            subprocess.run(['taskkill', '/F', '/IM', 'soffice.bin'], 
                          capture_output=True, timeout=3)
            time.sleep(1)
        except:
            pass
    
    # Define el comando de LibreOffice según el sistema operativo
    if platform.system() == 'Windows':
        possible_paths = [
            r'C:\Program Files\LibreOffice\program\soffice.exe',
            r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        ]
        
        libreoffice_cmd = None
        for path in possible_paths:
            if os.path.exists(path):
                libreoffice_cmd = path
                break
        
        if not libreoffice_cmd:
            raise FileNotFoundError(
                "LibreOffice no encontrado en las ubicaciones estándar de Windows.\n"
                "Verifica que LibreOffice esté instalado correctamente."
            )
        
        print(f"   → Usando: {libreoffice_cmd}")
    else:
        # En Linux, busca en múltiples ubicaciones
        print(f"   → Buscando LibreOffice en el sistema...")
        
        # Intenta encontrar con shutil.which primero
        for cmd in ['soffice', 'libreoffice']:
            found = shutil.which(cmd)
            if found:
                libreoffice_cmd = found
                print(f"   → LibreOffice encontrado con which: {found}")
                break
        else:
            # Si no se encuentra con which, busca en rutas específicas
            possible_paths = [
                '/usr/bin/soffice',
                '/usr/bin/libreoffice',
                '/usr/local/bin/soffice',
                '/usr/local/bin/libreoffice',
                '/opt/libreoffice/program/soffice'
            ]
            
            libreoffice_cmd = None
            for path in possible_paths:
                print(f"   → Verificando: {path}")
                if os.path.exists(path):
                    libreoffice_cmd = path
                    print(f"   → ✓ LibreOffice encontrado en: {path}")
                    break
            
            if not libreoffice_cmd:
                # Intenta listar lo que hay en /usr/bin
                print(f"   → Listando archivos relacionados en /usr/bin:")
                try:
                    libre_files = [f for f in os.listdir('/usr/bin') if 'libre' in f.lower() or 'soffice' in f.lower()]
                    print(f"   → Archivos encontrados: {libre_files}")
                except Exception as e:
                    print(f"   → Error listando /usr/bin: {e}")
                
                raise FileNotFoundError(
                    "LibreOffice no encontrado en el sistema.\n"
                    f"Rutas verificadas: {possible_paths}\n"
                    "Verifica que LibreOffice esté instalado en Railway."
                )
    
    try:
        # Ejecuta LibreOffice en modo headless
        print(f"   → Ejecutando conversión con: {libreoffice_cmd}")
        
        result = subprocess.run([
            libreoffice_cmd,
            '--headless',
            '--convert-to',
            'pdf',
            '--outdir',
            output_dir,
            docx_path
        ], capture_output=True, text=True, timeout=60, check=True)
        
        print(f"   → Comando ejecutado correctamente")
        
        if result.stdout:
            print(f"   → Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"   → Stderr: {result.stderr.strip()}")
        
        # El PDF tiene el mismo nombre pero con extensión .pdf
        pdf_path = docx_path.replace('.docx', '.pdf')
        
        print(f"   → Buscando PDF en: {pdf_path}")
        
        # Espera a que el archivo esté disponible (máximo 10 segundos)
        for i in range(20):
            if os.path.exists(pdf_path):
                print(f"   → PDF encontrado en intento {i+1}")
                break
            time.sleep(0.5)
        else:
            raise Exception(
                f"PDF no fue generado después de 10 segundos.\n"
                f"Output: {result.stdout}\n"
                f"Error: {result.stderr}\n"
                f"Ruta esperada: {pdf_path}"
            )
        
        pdf_size = os.path.getsize(pdf_path)
        print(f"   → PDF encontrado, tamaño: {pdf_size} bytes")
        
        if pdf_size == 0:
            raise Exception("El PDF generado está vacío")
        
        # Lee el PDF
        print(f"   → Leyendo PDF...")
        with open(pdf_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
        
        # Limpia el PDF temporal
        os.remove(pdf_path)
        
        print(f"   ✓ Conversión exitosa: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except subprocess.TimeoutExpired:
        raise Exception(
            "La conversión a PDF excedió el tiempo límite (60s)."
        )
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Error ejecutando LibreOffice:\n"
            f"Código de salida: {e.returncode}\n"
            f"Stderr: {e.stderr}\n"
            f"Stdout: {e.stdout}"
        )
    except FileNotFoundError as e:
        raise Exception(str(e))

def cargar_estudiantes_desde_excel(archivo_excel):
    """
    Carga estudiantes desde archivo Excel
    Columnas esperadas: Nombre, Código, DNI, Tipo Participante
    Retorna: dict con resultados
    """
    import openpyxl
    from .models import Estudiante
    
    resultados = {
        'exitosos': 0,
        'errores': [],
        'duplicados': 0
    }
    
    try:
        # Carga el archivo Excel
        wb = openpyxl.load_workbook(archivo_excel)
        sheet = wb.active
        
        # Itera desde la fila 2 (asume que fila 1 son headers)
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):  # Salta filas vacías
                continue
            
            try:
                nombre, codigo, dni, tipo = row[:4]
                
                # Valida que no estén vacíos
                if not all([nombre, codigo, dni, tipo]):
                    resultados['errores'].append(f"Fila {row_idx}: Datos incompletos")
                    continue
                
                # Normaliza tipo de participante
                tipo_lower = str(tipo).lower().strip()
                tipo_map = {
                    'ponente': 'ponente',
                    'asistente': 'asistente',
                    'organizador': 'organizador',
                    'sponsor': 'sponsor'
                }
                tipo_normalizado = tipo_map.get(tipo_lower)
                
                if not tipo_normalizado:
                    resultados['errores'].append(f"Fila {row_idx}: Tipo de participante inválido '{tipo}'")
                    continue
                
                # Crea o actualiza estudiante
                estudiante, created = Estudiante.objects.get_or_create(
                    dni=str(dni).strip(),
                    defaults={
                        'nombre_completo': str(nombre).strip(),
                        'codigo': str(codigo).strip(),
                        'tipo_participante': tipo_normalizado
                    }
                )
                
                if created:
                    resultados['exitosos'] += 1
                else:
                    resultados['duplicados'] += 1
                    
            except Exception as e:
                resultados['errores'].append(f"Fila {row_idx}: {str(e)}")
        
        return resultados
        
    except Exception as e:
        raise Exception(f"Error procesando Excel: {str(e)}")