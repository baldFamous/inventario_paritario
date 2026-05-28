from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario
import getpass

class Command(BaseCommand):
    help = 'Crea un superusuario saltándose las limitaciones del comando por defecto'

    def handle(self, *args, **kwargs):
        username = input("Username (ej: admin): ") or "admin"
        rut = input("RUT (ej: 11.111.111-1): ") or "11.111.111-1"
        password = getpass.getpass("Password: ")

        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'El usuario {username} ya existe. Actualizando contraseña...'))
            user = Usuario.objects.get(username=username)
        else:
            user = Usuario(username=username, rut=rut)

        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.rol = Usuario.Rol.GESTOR
        user.save()

        self.stdout.write(self.style.SUCCESS(f'¡Superusuario "{username}" configurado exitosamente!'))
