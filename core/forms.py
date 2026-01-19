from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Producto

# Registro Cliente
class RegistroClienteForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = 'cliente'
        if commit: user.save()
        return user

# Crear Staff
class CrearStaffForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol']

# --- NUEVO: FORMULARIO PARA AÑADIR PRODUCTO (ADMIN) ---
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'stock']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }