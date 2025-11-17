# gestion_gmexpress/urls.py

from django.urls import path
from . import views


urlpatterns = [
    # Home / dashboard
    path("", views.home, name="home"),

    # =========================
    # PEDIDOS (CLIENTE)
    # =========================
    # El cliente ve solo sus pedidos y puede crear nuevos
    path("mis-pedidos/", views.PedidoListView.as_view(), name="pedido-list"),
    path("mis-pedidos/nuevo/", views.PedidoCreateView.as_view(), name="pedido-create"),

    # Cambiar estado de pedido (uso interno / admin)
    path(
        "pedidos/<int:pk>/cambiar-estado/",
        views.cambiar_estado_pedido,
        name="pedido-estado",
    ),

    # =========================
    # VIAJES (COORDINADOR / ADMIN)
    # =========================
    path("viajes/", views.ViajeListView.as_view(), name="viaje-list"),
    path("viajes/<int:pk>/", views.ViajeDetailView.as_view(), name="viaje-detail"),
    path("viajes/<int:pk>/estado/", views.cambiar_estado_viaje, name="viaje-estado"),
    path(
        "viajes/<int:viaje_id>/paradas/nueva/",
        views.crear_parada,
        name="parada-create",
    ),

    # =========================
    # VEHÍCULOS
    # =========================
    path("vehiculos/", views.VehiculoListView.as_view(), name="vehiculo-list"),
    path("vehiculos/nuevo/", views.VehiculoCreateView.as_view(), name="vehiculo-create"),
    path(
        "vehiculos/<int:pk>/editar/",
        views.VehiculoUpdateView.as_view(),
        name="vehiculo-update",
    ),
]
