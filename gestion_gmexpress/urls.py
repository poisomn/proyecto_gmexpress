from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Vehículos
    path('vehiculos/', views.VehiculoListView.as_view(), name='vehiculo-list'),
    path('vehiculos/nuevo/', views.VehiculoCreateView.as_view(), name='vehiculo-create'),
    path('vehiculos/<int:pk>/editar/', views.VehiculoUpdateView.as_view(), name='vehiculo-update'),

    # Conductores
    path('conductores/', views.ConductorListView.as_view(), name='conductor-list'),
    path('conductores/nuevo/', views.ConductorCreateView.as_view(), name='conductor-create'),
    path('conductores/<int:pk>/editar/', views.ConductorUpdateView.as_view(), name='conductor-update'),


    # Viajes
    path('viajes/', views.ViajeListView.as_view(), name='viaje-list'),
    path('viajes/nuevo/', views.ViajeCreateView.as_view(), name='viaje-create'),
    path('viajes/<int:pk>/', views.ViajeDetailView.as_view(), name='viaje-detail'),
    path('viajes/<int:pk>/editar/', views.ViajeUpdateView.as_view(), name='viaje-update'),
    path('viajes/<int:pk>/estado/', views.cambiar_estado_viaje, name='viaje-estado'),
    path('viajes/<int:viaje_id>/paradas/nueva/', views.crear_parada, name='parada-create'),

    # Tipos de servicio
    path('servicios/', views.TipoServicioListView.as_view(), name='tiposervicio-list'),


    # Pedidos (vista general – admin/logística)
    path('pedidos/', views.PedidoListView.as_view(), name='pedido-list'),
    path('pedidos/nuevo/', views.PedidoCreateView.as_view(), name='pedido-create'),
    path('pedidos/<int:pk>/', views.PedidoDetailView.as_view(), name='pedido-detail'),
    path('pedidos/<int:pk>/estado/', views.cambiar_estado_pedido, name='pedido-estado'),
    path('pedidos/<int:pk>/asignacion/', views.asignar_logistica_pedido, name='pedido-asignacion'),
    path('pedidos/<int:pk>/eliminar/', views.PedidoDeleteView.as_view(), name='pedido-delete'),
    # Mis pedidos (vista filtrada para cliente)
    path('mis-pedidos/', views.MisPedidosListView.as_view(), name='mis-pedidos'),

    # ------------------------
    # Vistas Conductor
    # ------------------------
    path('mis-viajes/', views.MisViajesListView.as_view(), name='mis-viajes'),
    path('mi-ruta/<int:pk>/', views.HojaRutaView.as_view(), name='hoja-ruta'),
    path('entrega/<int:pk>/actualizar/', views.actualizar_estado_entrega, name='entrega-update'),
]