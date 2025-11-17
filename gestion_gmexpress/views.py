from datetime import date
from django.utils import timezone

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Max
from .models import (
    Vehiculo, Conductor, Cliente,
    Viaje, Pedido, Parada,
    HistorialEstadoPedido, EstadoPedido
)
from .forms import (
    VehiculoForm, ConductorForm, ClienteForm,
    ViajeForm, PedidoForm, ParadaForm,
    CambiarEstadoViajeForm, CambiarEstadoPedidoForm,
)

# ------------------------
# Home / Dashboard
# ------------------------

@login_required
def home(request):
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
# Vehículos
# ------------------------

class VehiculoListView(LoginRequiredMixin, ListView):
    model = Vehiculo
    template_name = 'gestion_gmexpress/vehiculo_list.html'
    context_object_name = 'vehiculos'


class VehiculoCreateView(LoginRequiredMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_gmexpress/vehiculo_form.html'
    success_url = reverse_lazy('vehiculo-list')


class VehiculoUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_gmexpress/vehiculo_form.html'
    success_url = reverse_lazy('vehiculo-list')


# ------------------------
# Viajes
# ------------------------

class ViajeListView(LoginRequiredMixin, ListView):
    model = Viaje
    template_name = 'gestion_gmexpress/viaje_list.html'
    context_object_name = 'viajes'
    ordering = ['-fecha_programada']


class ViajeDetailView(LoginRequiredMixin, DetailView):
    model = Viaje
    template_name = 'gestion_gmexpress/viaje_detail.html'
    context_object_name = 'viaje'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viaje = self.object
        context['paradas'] = viaje.paradas.select_related('pedido', 'estado_entrega')
        context['form_estado_viaje'] = CambiarEstadoViajeForm(instance=viaje)
        context['parada_form'] = ParadaForm()
        return context


@login_required
def cambiar_estado_viaje(request, pk):
    viaje = get_object_or_404(Viaje, pk=pk)

    if request.method == 'POST':
        form = CambiarEstadoViajeForm(request.POST, instance=viaje)
        if form.is_valid():
            form.save()
            return redirect('viaje-detail', pk=viaje.pk)

    return redirect('viaje-detail', pk=viaje.pk)


@login_required
def crear_parada(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)

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
# Pedidos
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

class PedidoListView(ClienteRequiredMixin, ListView):
    """
    Lista de pedidos SOLO del cliente logeado.
    """
    model = Pedido
    template_name = 'gestion_gmexpress/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 20
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        perfil = getattr(self.request.user, 'perfil', None)
        if not perfil or not hasattr(perfil, 'cliente'):
            # Por si acaso, pero no debería ocurrir por ClienteRequiredMixin
            return Pedido.objects.none()
        return Pedido.objects.filter(cliente=perfil.cliente).select_related(
            'tipo_servicio', 'estado'
        )


class PedidoCreateView(ClienteRequiredMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'gestion_gmexpress/pedido_form.html'
    success_url = reverse_lazy('pedido-list')  # o 'mis-pedidos'

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
            raise PermissionDenied("Tu usuario no está configurado como cliente con ficha asociada.")
        pedido.cliente = perfil.cliente

        # 3) Estado inicial
        estado_inicial = EstadoPedido.objects.get(nombre='PENDIENTE_ASIGNACION')
        pedido.estado = estado_inicial
        pedido.viaje = None

        # 4) Cálculo del monto total:
        #    precio_por_racion del tipo_servicio * cantidad de raciones
        tipo_servicio = pedido.tipo_servicio
        pedido.monto_total = pedido.cantidad_cajas * tipo_servicio.precio_por_racion

        pedido.save()
        return redirect(self.get_success_url())




@login_required
def cambiar_estado_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

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
                cambiado_por=getattr(request.user, 'perfil', None)
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


