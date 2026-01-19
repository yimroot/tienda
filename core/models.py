from django.db import models
from django.contrib.auth.models import AbstractUser

ROLES = (
    ('cliente', 'Cliente'),
    ('cajero', 'Cajero'),
    ('bodeguero', 'Bodeguero'),
    ('admin', 'Administrador'),
)

class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    email = models.EmailField(unique=True)

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self): return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self): return self.nombre

# --- NUEVOS MODELOS PARA EL CARRITO Y PEDIDOS ---

class Pedido(models.Model):
    ESTADOS = (
        ('carrito', 'En Carrito'),    
        ('pendiente', 'Pendiente'),   
        ('entregado', 'Entregado'),   
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='carrito')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # --- CAMBIO SOLICITADO: Rastreo del cajero que aprobó el pedido ---
    cajero_encargado = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pedidos_aprobados'
    )

    def calcular_total(self):
        total = sum([item.subtotal for item in self.detallepedido_set.all()])
        self.total = total
        self.save()

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario