from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'rut', 'first_name', 'last_name', 'rol', 'unidad', 'is_active']
    list_filter = ['rol', 'unidad', 'is_active']
    search_fields = ['rut', 'username', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Institucionales', {'fields': ('rut', 'rol', 'unidad')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos Institucionales', {'fields': ('rut', 'rol', 'unidad')}),
    )
