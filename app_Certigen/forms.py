from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Estudiante

class LoginEstudianteForm(forms.Form):
    dni = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su DNI',
            'autofocus': True
        }),
        label='DNI'
    )
    codigo = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su código'
        }),
        label='Código de Estudiante'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni')
        codigo = cleaned_data.get('codigo')
        
        if dni and codigo:
            try:
                estudiante = Estudiante.objects.get(dni=dni, codigo=codigo)
                cleaned_data['estudiante'] = estudiante
            except Estudiante.DoesNotExist:
                raise forms.ValidationError('DNI o código incorrectos')
        
        return cleaned_data


class CargarExcelForm(forms.Form):
    archivo_excel = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        }),
        label='Archivo Excel',
        help_text='Formato: Nombre, Código, DNI, Tipo Participante'
    )
    
    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        
        if archivo:
            # Valida extensión
            if not archivo.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError('Solo se permiten archivos Excel (.xlsx, .xls)')
            
            # Valida tamaño (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar 5MB')
        
        return archivo