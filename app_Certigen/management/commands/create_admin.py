from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea un superusuario automáticamente si no existe'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = 'admin'
        email = 'admin@upla.edu.pe'
        password = 'Upla2024!'  # CAMBIA ESTO por una contraseña segura
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Superusuario "{username}" creado exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ El superusuario "{username}" ya existe')
            )