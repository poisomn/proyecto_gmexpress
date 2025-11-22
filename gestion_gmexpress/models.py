# gestion_gmexpress/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ------------------------
# Usuarios, roles y auditoría
# ------------------------

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)
    intentos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    roles = models.ManyToManyField(
        Rol,
        through='UsuarioRol',
        through_fields=('usuario', 'rol'),
        related_name='usuarios',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def es_cliente(self) -> bool:
        return self.roles.filter(nombre='CLIENTE', activo=True).exists()

    @property
    def es_admin(self) -> bool:
        
        if self.user.is_superuser or self.user.is_staff:
            return True
        return self.roles.filter(nombre='ADMIN', activo=True).exists()

class UsuarioRol(models.Model):
    usuario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='roles_usuario'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='roles_asignados'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        PerfilUsuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='roles_asignados_por'
    )

    class Meta:
        unique_together = ('usuario', 'rol')

    def __str__(self):
        return f"{self.usuario} -> {self.rol}"


class AuditoriaRol(models.Model):
    class Accion(models.TextChoices):
        ASIGNAR = 'ASIGNAR', 'Asignar'
        REMOVER = 'REMOVER', 'Remover'

    usuario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='auditorias_roles'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='auditorias_roles'
    )
    accion = models.CharField(max_length=10, choices=Accion.choices)
    ejecutado_por = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='auditorias_ejecutadas'
    )
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} {self.rol} a {self.usuario}"


# ------------------------
# Catálogos de estados y tipos
# ------------------------

class EstadoVehiculo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class EstadoViaje(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField()

    def __str__(self):
        return self.nombre


class EstadoPedido(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField()

    def __str__(self):
        return self.nombre


class EstadoEntrega(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class TipoRuta(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class TipoServicio(models.Model):
    """
    Tipo de servicio de alimentación que GM Express ofrece
    para efectos de distribución: colación, almuerzo, coffee, etc.
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    precio_por_racion = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio_por_racion} por ración)"


# ------------------------
# Conductores y vehículos
# ------------------------

class Conductor(models.Model):
    usuario = models.OneToOneField(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='conductor'
    )
    numero_licencia = models.CharField(max_length=50, unique=True)
    tipo_licencia = models.CharField(max_length=20)
    vencimiento_licencia = models.DateField()
    experiencia_meses = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.usuario} ({self.numero_licencia})"


class Vehiculo(models.Model):
    placa = models.CharField(max_length=20, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveSmallIntegerField()
    capacidad_cajas = models.IntegerField()
    kilometraje_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    fecha_ultimo_mantenimiento = models.DateField(null=True, blank=True)

    estado = models.ForeignKey(
        EstadoVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculos'
    )
    conductor_asignado = models.ForeignKey(
        Conductor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='vehiculos_asignados'
    )
    fecha_asignacion_conductor = models.DateTimeField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"


# ------------------------
# Clientes
# ------------------------

class Cliente(models.Model):
    perfil = models.OneToOneField(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='cliente',
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    comuna = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nombre


# ------------------------
# Viajes y pedidos
# ------------------------

class Viaje(models.Model):
    nombre_ruta = models.CharField(max_length=100)
    tipo_ruta = models.ForeignKey(
        TipoRuta,
        on_delete=models.PROTECT,
        related_name='viajes'
    )
    origen = models.CharField(max_length=200)
    destino = models.CharField(max_length=200)

    fecha_programada = models.DateField()
    hora_salida = models.TimeField()
    hora_salida_real = models.DateTimeField(null=True, blank=True)
    hora_llegada_estimada = models.TimeField(null=True, blank=True)
    hora_llegada_real = models.DateTimeField(null=True, blank=True)

    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name='viajes'
    )
    conductor = models.ForeignKey(
        Conductor,
        on_delete=models.PROTECT,
        related_name='viajes'
    )
    estado = models.ForeignKey(
        EstadoViaje,
        on_delete=models.PROTECT,
        related_name='viajes'
    )

    cantidad_cajas_total = models.IntegerField(default=0)
    observaciones = models.TextField(blank=True)

    creado_por = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT,
        related_name='viajes_creados'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Viaje #{self.id} - {self.nombre_ruta} ({self.fecha_programada})"


class Pedido(models.Model):
    numero_pedido = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )

    direccion_entrega = models.TextField()
    ciudad = models.CharField(max_length=100)
    comuna = models.CharField(max_length=100)

    tipo_servicio = models.ForeignKey(
        'TipoServicio',
        on_delete=models.PROTECT,
        related_name='pedidos',
        null=True,
        blank=True,   
    )

    # La tratamos como "cantidad de raciones"
    cantidad_cajas = models.PositiveIntegerField()
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    fecha_entrega_solicitada = models.DateField(null=True, blank=True)

    estado = models.ForeignKey(
        EstadoPedido,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )
    viaje = models.ForeignKey(
        Viaje,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pedidos'
    )

    instrucciones_especiales = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido {self.numero_pedido}"


class HistorialEstadoPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    estado = models.ForeignKey(
        EstadoPedido,
        on_delete=models.PROTECT,
        related_name='historial_pedidos'
    )
    comentario = models.TextField(blank=True)
    fecha_cambio = models.DateTimeField(default=timezone.now)
    cambiado_por = models.ForeignKey(
        PerfilUsuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cambios_estado_pedido'
    )

    class Meta:
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.pedido} -> {self.estado} ({self.fecha_cambio})"


# ------------------------
# Paradas en la ruta
# ------------------------

class Parada(models.Model):
    class MotivoFallo(models.TextChoices):
        CLIENTE_AUSENTE = 'CLIENTE_AUSENTE', 'Cliente ausente'
        DIRECCION_INCORRECTA = 'DIRECCION_INCORRECTA', 'Dirección incorrecta'
        CLIENTE_RECHAZO = 'CLIENTE_RECHAZO', 'Cliente rechazó'
        ACCESO_BLOQUEADO = 'ACCESO_BLOQUEADO', 'Acceso bloqueado'
        OTRO = 'OTRO', 'Otro'

    viaje = models.ForeignKey(
        Viaje,
        on_delete=models.CASCADE,
        related_name='paradas'
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name='paradas'
    )

    secuencia = models.IntegerField()
    estado_entrega = models.ForeignKey(
        EstadoEntrega,
        on_delete=models.PROTECT,
        related_name='paradas'
    )

    hora_llegada_estimada = models.TimeField(null=True, blank=True)
    hora_llegada_real = models.DateTimeField(null=True, blank=True)
    fecha_entrega_real = models.DateField(null=True, blank=True)

    atendido_por = models.ForeignKey(
        Conductor,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='paradas_atendidas'
    )
    motivo_fallo = models.CharField(
        max_length=30,
        choices=MotivoFallo.choices,
        null=True,
        blank=True
    )
    observaciones = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ('viaje', 'secuencia'),
            ('viaje', 'pedido'),
        )
   
        ordering = ['secuencia']

    def __str__(self):
        return f"Parada {self.secuencia} - {self.pedido}"


# ------------------------
# Notificaciones y reportes
# ------------------------

class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        SISTEMA = 'SISTEMA', 'Sistema'

    usuario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    pedido = models.ForeignKey(
        Pedido,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notificaciones'
    )
    viaje = models.ForeignKey(
        Viaje,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notificaciones'
    )

    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tipo}] {self.titulo}"


class ReporteViaje(models.Model):
    fecha = models.DateField()
    total_viajes = models.IntegerField()
    viajes_completados = models.IntegerField()
    viajes_en_curso = models.IntegerField()
    total_entregas = models.IntegerField()
    entregas_exitosas = models.IntegerField()
    entregas_fallidas = models.IntegerField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte {self.fecha}"
