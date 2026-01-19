from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView
from core import views

urlpatterns = [
    path('admin-django/', admin.site.urls),
    path('', views.home, name='home'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Rutas Admin
    path('crear-staff/', views.crear_usuario_staff, name='crear_staff'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),
    path('eliminar-producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    
    # Rutas Reportes Admin
    path('historial-global/', views.historial_global, name='historial_global'),
    path('admin/clientes/', views.lista_clientes_admin, name='lista_clientes_admin'),
    path('admin/clientes/<int:user_id>/', views.historial_detalle_cliente, name='historial_detalle_cliente'),
    
    # Rutas Bodega
    path('bodega/', views.panel_bodeguero, name='panel_bodeguero'),
    path('actualizar-stock/<int:producto_id>/', views.actualizar_stock, name='actualizar_stock'),

    # Rutas Cliente
    path('catalogo/', views.catalogo, name='catalogo'),
    # CAMBIO: Nombre unificado para evitar el error NoReverseMatch
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'), 
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    # CAMBIO: Nueva ruta para eliminar y devolver stock
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),

    # Facturación
    path('pedido/factura/<int:pedido_id>/', views.descargar_factura, name='descargar_factura'),
    
    # Rutas Cajero
    path('caja/', views.panel_cajero, name='panel_cajero'),
    path('despachar/<int:pedido_id>/', views.despachar_pedido, name='despachar_pedido'),
]