# gestion_gmexpress/views.py

from datetime import date
from django.utils import timezone

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Max, Count

from .models import (
    Vehiculo, Conductor, Cliente,
    Viaje, Pedido, Parada,
    HistorialEstadoPedido, EstadoPedido, EstadoEntrega, TipoServicio,
)
from .forms import (
    VehiculoForm, ConductorForm, ClienteForm,
    ViajeForm, PedidoForm, ParadaForm,
    CambiarEstadoViajeForm, CambiarEstadoPedidoForm, AsignarLogisticaPedidoForm,
)

# ------------------------
# Home / Dashboard
# ------------------------

@login_required
def home(request):
    perfil = getattr(request.user, 'perfil', None)

    # Si es cliente -> mostramos la home de cliente
    if perfil and getattr(perfil, 'es_cliente', False):
        return render(request, 'gestion_gmexpress/cliente_home.html')

    # Si es conductor -> lo mando directo a "mis viajes"
    if perfil and hasattr(perfil, 'conductor'):
        return redirect('mis-viajes')

    # Si es admin / logística -> ve el dashboard con métricas
    total_vehiculos = Vehiculo.objects.count()
    total_conductores = Conductor.objects.count()
    total_pedidos = Pedido.objects.count()
    total_viajes = Viaje.objects.count()

    viajes_hoy = Viaje.objects.filter(fecha_programada=date.today()).count()
    pedidos_pendientes = Pedido.objects.filter(viaje__isnull=True).count()

    context = {
        'total_vehiculos': total_vehiculos,
        'total_conductores': total_conductores,
        'total_pedidos': total_pedidos,
        'total_viajes': total_viajes,
        'viajes_hoy': viajes_hoy,
        'pedidos_pendientes': pedidos_pendientes,
    }
    return render(request, 'gestion_gmexpress/home.html', context)


# ------------------------
# Mixins de permisos
# ------------------------

class ClienteRequiredMixin(LoginRequiredMixin):
    """
    Solo permite acceso a usuarios con rol CLIENTE.
    """
    def dispatch(self, request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or not perfil.roles.filter(nombre='CLIENTE', activo=True).exists():
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Solo permite acceso a usuarios de administración / logística
    (o superuser / staff de Django).
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        perfil = getattr(user, 'perfil', None)

        es_admin = (
            user.is_staff
            or user.is_superuser
            or (
                perfil and (
                    getattr(perfil, 'es_admin', False)
                    or perfil.roles.filter(
                        nombre__in=['ADMIN', 'LOGISTICA'],
                        activo=True
                    ).exists()
                )
            )
        )

        if not es_admin:
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


# ------------------------
# Vehículos
# ------------------------

class VehiculoListView(AdminRequiredMixin, ListView):
    model = Vehiculo
    template_name = 'gestion_gmexpress/vehiculo_list.html'
    context_object_name = 'vehiculos'


class VehiculoCreateView(AdminRequiredMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_gmexpress/vehiculo_form.html'
    success_url = reverse_lazy('vehiculo-list')


class VehiculoUpdateView(AdminRequiredMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_gmexpress/vehiculo_form.html'
    success_url = reverse_lazy('vehiculo-list')


# ------------------------
# Viajes
# ------------------------

class ViajeListView(AdminRequiredMixin, ListView):
    model = Viaje
    template_name = 'gestion_gmexpress/viaje_list.html'
    context_object_name = 'viajes'
    ordering = ['-fecha_programada']


class ViajeDetailView(AdminRequiredMixin, DetailView):
    model = Viaje
    template_name = 'gestion_gmexpress/viaje_detail.html'
    context_object_name = 'viaje'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viaje = self.object
        context['paradas'] = viaje.paradas.select_related('pedido', 'estado_entrega')
        context['form_estado_viaje'] = CambiarEstadoViajeForm(instance=viaje)
        context['parada_form'] = ParadaForm()

        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        es_admin = (
            user.is_staff
            or user.is_superuser
            or (perfil and getattr(perfil, 'es_admin', False))
        )
        context['es_admin'] = es_admin
        return context


class ViajeCreateView(AdminRequiredMixin, CreateView):
    model = Viaje
    form_class = ViajeForm
    template_name = 'gestion_gmexpress/viaje_form.html'
    success_url = reverse_lazy('viaje-list')

    def form_valid(self, form):
        viaje = form.save(commit=False)

        # quien creó el viaje
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil is None:
            raise PermissionDenied("Tu usuario no tiene perfil asociado.")
        viaje.creado_por = perfil

        viaje.save()
        return redirect(self.success_url)


class ViajeUpdateView(AdminRequiredMixin, UpdateView):
    model = Viaje
    form_class = ViajeForm
    template_name = 'gestion_gmexpress/viaje_form.html'
    success_url = reverse_lazy('viaje-list')


@login_required
def cambiar_estado_viaje(request, pk):
    viaje = get_object_or_404(Viaje, pk=pk)

    # Reforzamos que solo admin/logística puedan cambiar estado
    user = request.user
    perfil = getattr(user, 'perfil', None)
    es_admin = (
        user.is_staff
        or user.is_superuser
        or (
            perfil and (
                getattr(perfil, 'es_admin', False)
                or perfil.roles.filter(nombre__in=['ADMIN', 'LOGISTICA'], activo=True).exists()
            )
        )
    )
    if not es_admin:
        raise PermissionDenied("No tienes permisos para cambiar el estado de los viajes.")

    if request.method == 'POST':
        form = CambiarEstadoViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            form.save()
            return redirect('viaje-detail', pk=viaje.pk)

    return redirect('viaje-detail', pk=viaje.pk)


@login_required
def crear_parada(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)

    # Solo admin/logística pueden crear paradas
    user = request.user
    perfil = getattr(user, 'perfil', None)
    es_admin = (
        user.is_staff
        or user.is_superuser
        or (
            perfil and (
                getattr(perfil, 'es_admin', False)
                or perfil.roles.filter(nombre__in=['ADMIN', 'LOGISTICA'], activo=True).exists()
            )
        )
    )
    if not es_admin:
        raise PermissionDenied("No tienes permisos para gestionar las paradas de los viajes.")

    if request.method == 'POST':
        form = ParadaForm(request.POST)
        if form.is_valid():
            parada = form.save(commit=False)
            parada.viaje = viaje
            parada.save()

            # --- actualizar pedido asociado ---
            pedido = parada.pedido

            # asignar viaje si no tiene
            if pedido.viaje is None:
                pedido.viaje = viaje

            # cambiar estado a ASIGNADO si estaba pendiente
            try:
                estado_asignado = EstadoPedido.objects.get(nombre='ASIGNADO')
                if pedido.estado.nombre == 'PENDIENTE_ASIGNACION':
                    pedido.estado = estado_asignado
            except EstadoPedido.DoesNotExist:
                pass

            pedido.save()

            # recalcular cajas totales del viaje
            viaje.cantidad_cajas_total = sum(
                p.pedido.cantidad_cajas for p in viaje.paradas.all()
            )
            viaje.save()

            return redirect('viaje-detail', pk=viaje.pk)

    return redirect('viaje-detail', pk=viaje.pk)


# ------------------------
# Pedidos - Listas
# ------------------------

class PedidoListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = 'gestion_gmexpress/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20

    def get_queryset(self):
        """
        - Si es CLIENTE: ve solo sus pedidos.
        - Si es admin/logística: ve todos.
        - Además: aplica filtro por estado con ?estado=<id> o ?estado=todos
        """
        user = self.request.user
        perfil = getattr(user, 'perfil', None)

        # Base según rol
        qs = Pedido.objects.select_related('cliente', 'estado', 'viaje')

        if perfil and getattr(perfil, 'es_cliente', False):
            cliente = getattr(perfil, 'cliente', None)
            if cliente:
                qs = qs.filter(cliente=cliente)
            else:
                qs = qs.none()

        # Guardamos esta base para construir las pestañas (counts, etc.)
        self.qs_base_for_tabs = qs

        # Filtro por estado (GET ?estado=ID o ?estado=todos)
        self.estado_filtro = self.request.GET.get('estado', 'todos')

        if self.estado_filtro and self.estado_filtro != 'todos':
            try:
                estado_id = int(self.estado_filtro)
                qs = qs.filter(estado_id=estado_id)
            except ValueError:
                # Si viene algo raro en el parámetro, ignoramos el filtro
                pass

        return qs.order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        base = getattr(self, 'qs_base_for_tabs', Pedido.objects.none())

        # Estados que realmente aparecen en la lista (según rol)
        estados = (
            EstadoPedido.objects
            .filter(pedidos__in=base)
            .distinct()
            .order_by('orden', 'nombre')
        )

        # Conteo de pedidos por estado (sobre la base sin filtro de estado)
        conteos = base.values('estado_id').annotate(cantidad=Count('id'))
        map_counts = {c['estado_id']: c['cantidad'] for c in conteos}

        ctx['estados_tab'] = [
            {
                'id': e.id,
                'nombre': e.nombre,
                'count': map_counts.get(e.id, 0),
            }
            for e in estados
        ]

        ctx['estado_selected'] = self.estado_filtro or 'todos'
        ctx['total_pedidos'] = base.count()

        return ctx


class MisPedidosListView(ClienteRequiredMixin, ListView):
    """
    Versión explícita de "mis pedidos" solo para clientes.
    Usa la misma plantilla que PedidoListView.
    """
    model = Pedido
    template_name = 'gestion_gmexpress/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        perfil = getattr(self.request.user, 'perfil', None)
        cliente = getattr(perfil, 'cliente', None) if perfil else None

        if cliente:
            return (
                Pedido.objects
                .filter(cliente=cliente)
                .select_related('cliente', 'estado', 'viaje')
                .order_by('-fecha_creacion')
            )
        return Pedido.objects.none()


# ------------------------
# Pedidos - Detail / Create / Delete
# ------------------------

class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = 'gestion_gmexpress/pedido_detail.html'
    context_object_name = 'pedido'

    def get_queryset(self):
        """
        - Si el usuario es CLIENTE: solo puede ver SUS pedidos.
        - Si es admin/logística: puede ver todos.
        """
        qs = (
            super()
            .get_queryset()
            .select_related(
                'cliente',
                'estado',
                'tipo_servicio',
                'viaje__vehiculo',
                'viaje__conductor__usuario__user',
            )
            .prefetch_related(
                'historial_estados__estado',
                'historial_estados__cambiado_por__user',
                'paradas__estado_entrega',
                'paradas__viaje',
            )
        )

        user = self.request.user
        perfil = getattr(user, 'perfil', None)

        # Si es cliente: solo sus pedidos
        if perfil and getattr(perfil, 'es_cliente', False):
            cliente = getattr(perfil, 'cliente', None)
            if cliente:
                return qs.filter(cliente=cliente)
            return qs.none()

        # Admin / logística ven todo
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pedido = self.object

        ctx['historial'] = pedido.historial_estados.all()
        ctx['paradas'] = pedido.paradas.all()

        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        es_admin = (
            user.is_staff
            or user.is_superuser
            or (perfil and getattr(perfil, 'es_admin', False))
        )
        ctx['es_admin'] = es_admin
        return ctx


class PedidoCreateView(ClienteRequiredMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'gestion_gmexpress/pedido_form.html'
    success_url = reverse_lazy('mis-pedidos')

    def generar_numero_pedido(self):
        hoy = timezone.localdate()
        base = hoy.strftime("PED-%Y%m%d-")
        cantidad_hoy = Pedido.objects.filter(
            fecha_creacion__date=hoy
        ).count() + 1
        return f"{base}{cantidad_hoy:04d}"

    def form_valid(self, form):
        pedido = form.save(commit=False)

        # 1) Número de pedido
        pedido.numero_pedido = self.generar_numero_pedido()

        # 2) Cliente desde usuario logeado
        perfil = getattr(self.request.user, 'perfil', None)
        if not perfil or not hasattr(perfil, 'cliente'):
            raise PermissionDenied(
                "Tu usuario no está configurado como cliente con ficha asociada."
            )
        pedido.cliente = perfil.cliente

        # 3) Estado inicial
        estado_inicial = EstadoPedido.objects.get(nombre='PENDIENTE_ASIGNACION')
        pedido.estado = estado_inicial
        pedido.viaje = None

        # 4) Cálculo del monto total
        tipo_servicio = pedido.tipo_servicio
        pedido.monto_total = pedido.cantidad_cajas * tipo_servicio.precio_por_racion

        # Guardar y setear self.object para que CreateView quede contento
        pedido.save()
        self.object = pedido

        return redirect(self.get_success_url())


class PedidoDeleteView(AdminRequiredMixin, DeleteView):
    model = Pedido
    template_name = 'gestion_gmexpress/pedido_confirm_delete.html'
    success_url = reverse_lazy('pedido-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pedido'] = self.object
        return ctx


class TipoServicioListView(LoginRequiredMixin, ListView):
    model = TipoServicio
    template_name = 'gestion_gmexpress/tiposervicio_list.html'
    context_object_name = 'tipos_servicio'

    def get_queryset(self):
        # Solo mostrar los activos
        return TipoServicio.objects.filter(activo=True).order_by('nombre')


# ------------------------
# Pedidos - Cambio de estado / Asignación logística
# ------------------------

@login_required
def cambiar_estado_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    user = request.user
    perfil = getattr(user, 'perfil', None)

    # --- SOLO ADMIN / LOGÍSTICA ---
    es_admin = (
        user.is_staff or
        user.is_superuser or
        (perfil and hasattr(perfil, 'es_admin') and perfil.es_admin)
    )
    if not es_admin:
        raise PermissionDenied("No tienes permisos para cambiar el estado de los pedidos.")

    if request.method == 'POST':
        form = CambiarEstadoPedidoForm(request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            comentario = form.cleaned_data['comentario']

            # Registrar historial
            HistorialEstadoPedido.objects.create(
                pedido=pedido,
                estado=nuevo_estado,
                comentario=comentario,
                cambiado_por=perfil,
            )

            # Actualizar estado actual
            pedido.estado = nuevo_estado
            pedido.save()

            return redirect('pedido-list')
    else:
        form = CambiarEstadoPedidoForm(initial={'nuevo_estado': pedido.estado})

    context = {
        'pedido': pedido,
        'form': form,
    }
    return render(request, 'gestion_gmexpress/pedido_estado_form.html', context)


@login_required
def asignar_logistica_pedido(request, pk):
    """
    Admin/logística: asignar un pedido a un viaje.
    El viaje ya tiene vehículo y conductor.
    """
    pedido = get_object_or_404(Pedido, pk=pk)

    perfil = getattr(request.user, 'perfil', None)
    es_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or (perfil and perfil.roles.filter(nombre__in=['ADMIN', 'LOGISTICA'], activo=True).exists())
    )
    if not es_admin:
        raise PermissionDenied("No tienes permisos para asignar logística a pedidos.")

    if request.method == 'POST':
        form = AsignarLogisticaPedidoForm(request.POST)
        if form.is_valid():
            viaje = form.cleaned_data['viaje']

            # Asignar viaje al pedido
            pedido.viaje = viaje
            try:
                estado_asignado = EstadoPedido.objects.get(nombre='ASIGNADO')
                pedido.estado = estado_asignado
            except EstadoPedido.DoesNotExist:
                # Si aún no creas el estado ASIGNADO, dejamos el actual
                pass
            pedido.save()

            # Crear parada para este pedido dentro del viaje (si no existe)
            ultima = viaje.paradas.aggregate(Max('secuencia'))['secuencia__max'] or 0
            estado_entrega = EstadoEntrega.objects.get(nombre='PENDIENTE')

            Parada.objects.create(
                viaje=viaje,
                pedido=pedido,
                secuencia=ultima + 1,
                estado_entrega=estado_entrega,
                atendido_por=viaje.conductor,
            )

            messages.success(
                request,
                f"Pedido {pedido.numero_pedido} asignado al viaje #{viaje.id} "
                f"({viaje.vehiculo} / {viaje.conductor})."
            )
            return redirect('pedido-detail', pk=pedido.pk)
    else:
        form = AsignarLogisticaPedidoForm()

    context = {
        'pedido': pedido,
        'form': form,
    }
    return render(request, 'gestion_gmexpress/pedido_asignacion_form.html', context)


# ------------------------
# Conductores (Choferes)
# ------------------------

class ConductorListView(AdminRequiredMixin, ListView):
    model = Conductor
    template_name = 'gestion_gmexpress/conductor_list.html'
    context_object_name = 'conductores'
    ordering = ['usuario__user__first_name', 'usuario__user__last_name']


class ConductorCreateView(AdminRequiredMixin, CreateView):
    model = Conductor
    form_class = ConductorForm
    template_name = 'gestion_gmexpress/conductor_form.html'
    success_url = reverse_lazy('conductor-list')


class ConductorUpdateView(AdminRequiredMixin, UpdateView):
    model = Conductor
    form_class = ConductorForm
    template_name = 'gestion_gmexpress/conductor_form.html'
    success_url = reverse_lazy('conductor-list')

class ConductorRequiredMixin(LoginRequiredMixin):
    """
    Solo permite acceso a usuarios con rol CONDUCTOR (o que tengan un Conductor asociado).
    """
    def dispatch(self, request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil', None)
        # Verificamos si tiene perfil y si tiene un conductor asociado
        if not perfil or not hasattr(perfil, 'conductor'):
             raise PermissionDenied("No tienes permisos de conductor para acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)


# ------------------------
# Vistas para el Conductor
# ------------------------

class MisViajesListView(ConductorRequiredMixin, ListView):
    model = Viaje
    template_name = 'gestion_gmexpress/conductor_viaje_list.html'
    context_object_name = 'viajes'
    ordering = ['-fecha_programada']

    def get_queryset(self):
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        
        # El conductor solo ve sus viajes
        perfil = self.request.user.perfil
        conductor = perfil.conductor
        return Viaje.objects.filter(conductor=conductor).annotate(
            total_cajas_real=Coalesce(Sum('paradas__pedido__cantidad_cajas'), 0)
        ).order_by('-fecha_programada')


class HojaRutaView(ConductorRequiredMixin, DetailView):
    model = Viaje
    template_name = 'gestion_gmexpress/hoja_ruta.html'
    context_object_name = 'viaje'

    def get_queryset(self):
        # Asegurar que el viaje pertenece al conductor
        perfil = self.request.user.perfil
        conductor = perfil.conductor
        return Viaje.objects.filter(conductor=conductor)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viaje = self.object
        # Paradas ordenadas por secuencia
        context['paradas'] = viaje.paradas.select_related('pedido', 'pedido__cliente', 'estado_entrega').order_by('secuencia')
        # Estados de entrega para el modal/formulario
        context['estados_entrega'] = EstadoEntrega.objects.all()
        return context


@login_required
def actualizar_estado_entrega(request, pk):
    """
    Actualiza el estado de una Parada (y opcionalmente del Pedido).
    Solo para el conductor asignado al viaje de esa parada.
    """
    parada = get_object_or_404(Parada, pk=pk)
    viaje = parada.viaje
    
    # Verificar que el usuario sea el conductor del viaje
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or not hasattr(perfil, 'conductor') or viaje.conductor != perfil.conductor:
        raise PermissionDenied("No tienes permiso para actualizar esta entrega.")

    if request.method == 'POST':
        nuevo_estado_id = request.POST.get('estado_entrega')
        motivo_fallo = request.POST.get('motivo_fallo')
        observaciones = request.POST.get('observaciones')

        if nuevo_estado_id:
            nuevo_estado = get_object_or_404(EstadoEntrega, pk=nuevo_estado_id)
            parada.estado_entrega = nuevo_estado
            
            # Lógica de sincronización con Pedido
            # Si la parada es ENTREGADO -> Pedido ENTREGADO
            # Si la parada es FALLIDO -> Pedido NO_ENTREGADO (o similar)
            pedido = parada.pedido
            
            if nuevo_estado.nombre == 'ENTREGADO':
                try:
                    estado_entregado = EstadoPedido.objects.get(nombre='ENTREGADO')
                    pedido.estado = estado_entregado
                    pedido.save()
                    
                    # Registrar historial
                    HistorialEstadoPedido.objects.create(
                        pedido=pedido,
                        estado=estado_entregado,
                        comentario=f"Entregado por conductor {viaje.conductor}",
                        cambiado_por=perfil
                    )
                except EstadoPedido.DoesNotExist:
                    pass
            
            elif nuevo_estado.nombre == 'FALLIDO':
                 # Podríamos tener un estado 'NO_ENTREGADO' o 'REPROGRAMAR'
                 pass

        if motivo_fallo:
            parada.motivo_fallo = motivo_fallo
        
        if observaciones:
            parada.observaciones = observaciones
            
        parada.atendido_por = perfil.conductor
        parada.fecha_entrega_real = timezone.localdate()
        parada.hora_llegada_real = timezone.now()
        parada.save()
        
        messages.success(request, f"Entrega de pedido {parada.pedido.numero_pedido} actualizada.")

    return redirect('hoja-ruta', pk=viaje.pk)
