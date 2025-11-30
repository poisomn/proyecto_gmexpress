from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from gestion_gmexpress.models import (
    PerfilUsuario, Rol, Conductor, Vehiculo, EstadoVehiculo,
    Viaje, TipoRuta, EstadoViaje, Pedido, Cliente, EstadoPedido,
    TipoServicio, Parada, EstadoEntrega
)
from datetime import timedelta

class Command(BaseCommand):
    help = 'Crea datos de prueba para verificar la vista del conductor'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creando datos de prueba...")

        # 1. Crear Roles si no existen
        rol_conductor, _ = Rol.objects.get_or_create(nombre='CONDUCTOR')
        rol_cliente, _ = Rol.objects.get_or_create(nombre='CLIENTE')

        # 2. Crear Usuario Conductor
        username = 'chofer_prueba'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password='password123')
            user.first_name = 'Juan'
            user.last_name = 'Pérez'
            user.save()
            
            perfil = PerfilUsuario.objects.create(user=user)
            # Asignar rol a través de UsuarioRol (many-to-many)
            # perfil.roles.add(rol_conductor) # Si fuera directo, pero es through
            from gestion_gmexpress.models import UsuarioRol
            UsuarioRol.objects.create(usuario=perfil, rol=rol_conductor)
            
            Conductor.objects.create(
                usuario=perfil,
                numero_licencia='LIC-12345',
                tipo_licencia='A2',
                vencimiento_licencia=timezone.now().date() + timedelta(days=365)
            )
            self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username} / password123"))
        else:
            user = User.objects.get(username=username)
            perfil = user.perfil
            self.stdout.write(f"Usuario {username} ya existe")

        conductor = perfil.conductor

        # 3. Crear Vehículo
        estado_vehiculo, _ = EstadoVehiculo.objects.get_or_create(nombre='OPERATIVO')
        vehiculo, created = Vehiculo.objects.get_or_create(
            placa='TEST-99',
            defaults={
                'marca': 'Toyota',
                'modelo': 'Hiace',
                'anio': 2023,
                'capacidad_cajas': 100,
                'estado': estado_vehiculo,
                'conductor_asignado': conductor
            }
        )

        # 4. Crear Viaje
        tipo_ruta, _ = TipoRuta.objects.get_or_create(nombre='URBANA')
        estado_viaje, _ = EstadoViaje.objects.get_or_create(nombre='PROGRAMADO', defaults={'orden': 1})
        
        viaje = Viaje.objects.create(
            nombre_ruta='Ruta Prueba Centro',
            tipo_ruta=tipo_ruta,
            origen='Bodega Central',
            destino='Centro Ciudad',
            fecha_programada=timezone.now().date(),
            hora_salida=timezone.now().time(),
            vehiculo=vehiculo,
            conductor=conductor,
            estado=estado_viaje,
            creado_por=perfil # Auto-asignado para prueba
        )

        # 5. Crear Cliente y Pedido
        if not User.objects.filter(username='cliente_prueba').exists():
            u_cli = User.objects.create_user(username='cliente_prueba', password='password123')
            p_cli = PerfilUsuario.objects.create(user=u_cli)
            from gestion_gmexpress.models import UsuarioRol
            UsuarioRol.objects.create(usuario=p_cli, rol=rol_cliente)
            cliente = Cliente.objects.create(
                perfil=p_cli,
                nombre='Empresa Test Ltda',
                email='test@cliente.com',
                telefono='+56911112222',
                direccion='Av. Siempre Viva 742',
                comuna='Santiago'
            )
        else:
            cliente = Cliente.objects.get(perfil__user__username='cliente_prueba')

        estado_pedido, _ = EstadoPedido.objects.get_or_create(nombre='ASIGNADO', defaults={'orden': 2})
        tipo_servicio, _ = TipoServicio.objects.get_or_create(nombre='Almuerzo Ejecutivo', defaults={'precio_por_racion': 5000})

        pedido = Pedido.objects.create(
            numero_pedido=f'PED-TEST-{timezone.now().strftime("%H%M%S")}',
            cliente=cliente,
            direccion_entrega=cliente.direccion,
            ciudad='Santiago',
            comuna=cliente.comuna,
            tipo_servicio=tipo_servicio,
            cantidad_cajas=10,
            estado=estado_pedido,
            viaje=viaje
        )

        # 6. Crear Parada
        estado_entrega, _ = EstadoEntrega.objects.get_or_create(nombre='PENDIENTE')
        Parada.objects.create(
            viaje=viaje,
            pedido=pedido,
            secuencia=1,
            estado_entrega=estado_entrega
        )

        self.stdout.write(self.style.SUCCESS(f"Datos de prueba creados exitosamente. Viaje ID: {viaje.id}"))
