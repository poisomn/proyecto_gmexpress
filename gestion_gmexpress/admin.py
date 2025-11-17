from django.contrib import admin
from .models import (
    Rol, PerfilUsuario, UsuarioRol, AuditoriaRol,
    EstadoVehiculo, EstadoViaje, EstadoPedido, EstadoEntrega, TipoRuta, TipoServicio,
    Conductor, Vehiculo, Cliente,
    Viaje, Pedido, HistorialEstadoPedido, Parada,
    Notificacion, ReporteViaje,
)


# ------------------------
# Usuarios, roles, perfiles
# ------------------------

class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    fk_name = 'usuario'   # indicamos cuál FK usar para el inline
    extra = 1


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'activo', 'telefono')
    list_filter = ('activo', 'roles')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'telefono')
    inlines = [UsuarioRolInline]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(AuditoriaRol)
class AuditoriaRolAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'accion', 'ejecutado_por', 'fecha_ejecucion')
    list_filter = ('accion', 'rol')
    search_fields = ('usuario__user__username', 'rol__nombre')


# ------------------------
# Catálogos simples
# ------------------------

@admin.register(EstadoVehiculo, EstadoEntrega, TipoRuta)
class CatalogoSimpleAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(EstadoViaje)
class EstadoViajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden')
    list_filter = ('orden',)
    search_fields = ('nombre',)


@admin.register(EstadoPedido)
class EstadoPedidoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden')
    list_filter = ('orden',)
    search_fields = ('nombre',)


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_por_racion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


# ------------------------
# Conductores, vehículos, clientes
# ------------------------

@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'numero_licencia', 'tipo_licencia', 'vencimiento_licencia')
    search_fields = ('usuario__user__username', 'numero_licencia')
    list_filter = ('tipo_licencia',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'anio', 'estado', 'conductor_asignado')
    list_filter = ('estado', 'marca')
    search_fields = ('placa', 'marca', 'modelo')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'comuna')
    search_fields = ('nombre', 'email', 'telefono', 'comuna')


# ------------------------
# Viajes, pedidos, paradas
# ------------------------

class ParadaInline(admin.TabularInline):
    model = Parada
    extra = 0


@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_ruta', 'fecha_programada', 'vehiculo', 'conductor', 'estado')
    list_filter = ('estado', 'fecha_programada', 'vehiculo')
    search_fields = ('nombre_ruta', 'vehiculo__placa', 'conductor__usuario__user__username')
    inlines = [ParadaInline]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_pedido', 'cliente', 'tipo_servicio',
        'cantidad_cajas', 'monto_total',
        'comuna', 'estado', 'viaje', 'fecha_entrega_solicitada'
    )
    list_filter = ('estado', 'comuna', 'fecha_entrega_solicitada', 'tipo_servicio')
    search_fields = ('numero_pedido', 'cliente__nombre', 'cliente__email')


@admin.register(HistorialEstadoPedido)
class HistorialEstadoPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'estado', 'fecha_cambio', 'cambiado_por')
    list_filter = ('estado', 'fecha_cambio')
    search_fields = ('pedido__numero_pedido',)


@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ('viaje', 'secuencia', 'pedido', 'estado_entrega', 'motivo_fallo')
    list_filter = ('estado_entrega', 'motivo_fallo')
    search_fields = ('viaje__nombre_ruta', 'pedido__numero_pedido')


# ------------------------
# Notificaciones y reportes
# ------------------------

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'titulo', 'usuario', 'pedido', 'viaje', 'leida', 'fecha_envio')
    list_filter = ('tipo', 'leida')
    search_fields = ('titulo', 'mensaje')


@admin.register(ReporteViaje)
class ReporteViajeAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'total_viajes', 'viajes_completados', 'entregas_exitosas', 'entregas_fallidas')
    list_filter = ('fecha',)
