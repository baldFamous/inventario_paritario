from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'rut', 'username', 'first_name', 'last_name',
                  'nombre_completo', 'email', 'rol', 'unidad', 'is_active']
        read_only_fields = ['id']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ['rut', 'username', 'first_name', 'last_name',
                  'email', 'rol', 'unidad', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user
