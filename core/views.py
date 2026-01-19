from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Categoria, Producto, Pedido, DetallePedido, Usuario
from .forms import RegistroClienteForm, CrearStaffForm, ProductoForm
from .decorators import solo_admin, solo_bodeguero
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. VISTA PRINCIPAL (HOME) ---
def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home_publico.html')
    
    user = request.user
    if user.rol == 'admin' or user.is_superuser:
        return render(request, 'dashboard_admin.html')
    elif user.rol == 'cajero':
        return redirect('panel_cajero')
    elif user.rol == 'bodeguero':
        return redirect('panel_bodeguero')
    elif user.rol == 'cliente':
        return redirect('catalogo')
    else:
        return render(request, 'base.html', {'mensaje': 'Bienvenido Staff'})

# --- 2. AUTENTICACIÓN (LOGIN/REGISTRO) ---
def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            
    return render(request, 'login.html', {'form': form})

def registro_view(request):
    if request.user.is_authenticated: return redirect('home')

    form = RegistroClienteForm()
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Bienvenido a BitBites!")
            return redirect('home')
    
    return render(request, 'registro.html', {'form': form})

# --- 3. FUNCIONES DE ADMIN (STAFF E INVENTARIO) ---
@solo_admin
def crear_usuario_staff(request):
    form = CrearStaffForm()
    if request.method == 'POST':
        form = CrearStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado creado correctamente")
            return redirect('home')
    
    return render(request, 'crear_staff.html', {'form': form})

@solo_admin
def agregar_producto(request):
    form = ProductoForm()
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto añadido al inventario")
            return redirect('home')
    
    return render(request, 'agregar_producto.html', {'form': form})

@solo_bodeguero
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    nombre_p = producto.nombre
    producto.delete()
    messages.success(request, f"Producto '{nombre_p}' eliminado correctamente.")
    return redirect('panel_bodeguero')

# --- 4. REPORTES Y CONTROL ADMIN ---
@solo_admin
def historial_global(request):
    pedidos = Pedido.objects.exclude(estado='carrito').order_by('-fecha')
    return render(request, 'historial_global.html', {'pedidos': pedidos})

@solo_admin
def lista_clientes_admin(request):
    clientes = Usuario.objects.filter(rol='cliente')
    return render(request, 'admin_lista_clientes.html', {'clientes': clientes})

@solo_admin
def historial_detalle_cliente(request, user_id):
    cliente = get_object_or_404(Usuario, id=user_id)
    pedidos = Pedido.objects.filter(usuario=cliente).exclude(estado='carrito').order_by('-fecha')
    return render(request, 'admin_historial_cliente.html', {
        'cliente': cliente,
        'pedidos': pedidos
    })

# --- 5. BODEGUERO ---
@solo_bodeguero
def panel_bodeguero(request):
    productos = Producto.objects.all().order_by('stock')
    return render(request, 'panel_bodeguero.html', {'productos': productos})

@solo_bodeguero
def actualizar_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        nuevo_stock = request.POST.get('nuevo_stock')
        if nuevo_stock:
            producto.stock = int(nuevo_stock)
            producto.save()
            messages.success(request, f"Stock de {producto.nombre} actualizado a {producto.stock}")
    return redirect('panel_bodeguero')


# --- 6. CLIENTE ---
@login_required
def catalogo(request):
    categorias = Categoria.objects.prefetch_related('producto_set').all()
    return render(request, 'catalogo.html', {'categorias': categorias})

@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if producto.stock <= 0:
        messages.error(request, "Lo sentimos, este producto está agotado.")
        return redirect('catalogo')

    pedido, _ = Pedido.objects.get_or_create(usuario=request.user, estado='carrito')
    item, created = DetallePedido.objects.get_or_create(
        pedido=pedido, producto=producto,
        defaults={'precio_unitario': producto.precio}
    )
    
    # Restar stock inmediatamente
    producto.stock -= 1
    producto.save()
    
    if not created:
        item.cantidad += 1
    item.save()
    
    pedido.calcular_total()
    messages.success(request, f"{producto.nombre} añadido al carrito. Quedan {producto.stock} en stock.")
    return redirect('catalogo')

@login_required
def ver_carrito(request):
    pedido = Pedido.objects.filter(usuario=request.user, estado='carrito').first()
    return render(request, 'carrito.html', {'pedido': pedido})

@login_required
def eliminar_del_carrito(request, item_id):
    """Disminuye la cantidad de un producto en el carrito uno por uno y devuelve stock."""
    item = get_object_or_404(DetallePedido, id=item_id, pedido__usuario=request.user, pedido__estado='carrito')
    producto = item.producto
    
    # Devolver exactamente 1 unidad al stock del producto
    producto.stock += 1
    producto.save()
    
    if item.cantidad > 1:
        # Si hay más de uno, restamos solo uno a la cantidad en el carrito
        item.cantidad -= 1
        item.save()
        messages.success(request, f"Se quitó una unidad de {producto.nombre}.")
    else:
        # Si era el último, eliminamos el ítem por completo
        item.delete()
        messages.success(request, f"Se eliminó {producto.nombre} del carrito.")
    
    # Recalcular el total después de la modificación
    pedido = Pedido.objects.filter(usuario=request.user, estado='carrito').first()
    if pedido:
        pedido.calcular_total()
        # Borrar el pedido si ya no quedan ítems
        if not pedido.detallepedido_set.exists():
            pedido.delete()
            
    return redirect('ver_carrito')

@login_required
def confirmar_pedido(request):
    pedido = Pedido.objects.filter(usuario=request.user, estado='carrito').first()
    
    if pedido and pedido.detallepedido_set.exists():
        pedido.estado = 'pendiente'
        pedido.save()
        messages.success(request, "¡Pedido realizado! Retira tus snacks en caja.")
        return redirect('mis_pedidos')
    else:
        messages.warning(request, "Tu carrito está vacío.")
    
    return redirect('home')

@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).exclude(estado='carrito').order_by('-fecha')
    return render(request, 'mis_pedidos.html', {'pedidos': pedidos})

# --- 7. CAJERO ---
@login_required
def panel_cajero(request):
    if request.user.rol not in ['cajero', 'admin'] and not request.user.is_superuser:
        return redirect('home')
    pedidos = Pedido.objects.filter(estado='pendiente').order_by('-fecha')
    return render(request, 'panel_cajero.html', {'pedidos': pedidos})

@login_required
def despachar_pedido(request, pedido_id):
    if request.user.rol not in ['cajero', 'admin'] and not request.user.is_superuser:
        return redirect('home')
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.estado = 'entregado'
    pedido.cajero_encargado = request.user 
    pedido.save()
    
    messages.success(request, f"Pedido #{pedido.id} entregado.")
    return redirect('panel_cajero')

# --- 8. FACTURACIÓN PDF CON SEGURIDAD ---
@login_required
def descargar_factura(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    
    if pedido.estado != 'entregado':
        messages.error(request, "La factura solo se puede generar una vez que el pedido haya sido entregado.")
        return redirect('mis_pedidos')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Factura_BitBites_{pedido.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "BITBITES STORE 👾")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "RUC: 1790001234001")
    p.drawString(50, height - 85, "Dirección: Av. Principal, Quito - Ecuador")
    p.drawString(50, height - 100, "Teléfono: 099-BIT-SNACK")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, height - 50, f"FACTURA: #000-{pedido.id}")
    p.setFont("Helvetica", 10)
    p.drawString(400, height - 65, f"Fecha: {pedido.fecha.strftime('%d/%m/%Y %H:%M')}")

    p.rect(45, height - 170, 500, 50)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(55, height - 135, "CLIENTE:")
    p.setFont("Helvetica", 11)
    p.drawString(120, height - 135, f"{pedido.usuario.first_name} {pedido.usuario.last_name}")
    p.drawString(55, height - 155, f"Usuario: {pedido.usuario.username}")
    p.drawString(300, height - 155, f"Email: {pedido.usuario.email}")

    y = height - 210
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Cant.")
    p.drawString(100, y, "Producto")
    p.drawString(400, y, "P. Unit")
    p.drawString(480, y, "Subtotal")
    p.line(45, y - 5, 550, y - 5)

    y -= 25
    p.setFont("Helvetica", 11)
    for item in pedido.detallepedido_set.all():
        p.drawString(55, y, str(item.cantidad))
        p.drawString(100, y, item.producto.nombre)
        p.drawString(400, y, f"${item.precio_unitario}")
        p.drawString(480, y, f"${item.subtotal}")
        y -= 20

    p.line(45, y, 550, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(400, y - 30, "TOTAL:")
    p.drawString(480, y - 30, f"${pedido.total}")

    p.showPage()
    p.save()
    return response