from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Modelo de usuario custom con roles RBAC."""

    class Rol(models.TextChoices):
        SOLICITANTE = 'SOLICITANTE', 'Solicitante'
        GESTOR = 'GESTOR', 'Gestor Paritario'

    rut = models.CharField(max_length=12, unique=True, help_text='RUT del funcionario (ej: 12.345.678-9)')
    rol = models.CharField(max_length=15, choices=Rol.choices, default=Rol.SOLICITANTE)
    unidad = models.CharField(max_length=100, blank=True, help_text='Departamento o unidad')

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.rut})'

    @property
    def es_gestor(self):
        return self.rol == self.Rol.GESTOR

    @property
    def es_solicitante(self):
        return self.rol == self.Rol.SOLICITANTE
