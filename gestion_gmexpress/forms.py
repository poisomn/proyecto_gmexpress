from django import forms
from .models import (
    Vehiculo, Conductor, Cliente,
    Viaje, Pedido, Parada,
    EstadoViaje, EstadoPedido, HistorialEstadoPedido,
)


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'placa', 'marca', 'modelo', 'anio',
            'capacidad_cajas', 'kilometraje_actual',
            'fecha_ultimo_mantenimiento', 'estado',
            'conductor_asignado',
        ]


class ConductorForm(forms.ModelForm):
    class Meta:
        model = Conductor
        fields = [
            'usuario', 'numero_licencia', 'tipo_licencia',
            'vencimiento_licencia', 'experiencia_meses',
        ]


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'direccion', 'ciudad', 'comuna']


class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            'nombre_ruta', 'tipo_ruta', 'origen', 'destino',
            'fecha_programada', 'hora_salida', 'hora_llegada_estimada',
            'vehiculo', 'conductor', 'estado',
            'cantidad_cajas_total', 'observaciones',
        ]


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            'tipo_servicio',          # colación / almuerzo / coffee
            'cantidad_cajas',        # la usaremos como "cantidad de raciones"
            'direccion_entrega',
            'ciudad',
            'comuna',
            'fecha_entrega_solicitada',
            'instrucciones_especiales',
        ]
        labels = {
            'tipo_servicio': 'Tipo de servicio',
            'cantidad_cajas': 'Cantidad de raciones',
            'direccion_entrega': 'Dirección de entrega',
            'fecha_entrega_solicitada': 'Fecha del servicio',
        }
        widgets = {
            'fecha_entrega_solicitada': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'direccion_entrega': forms.Textarea(
                attrs={'rows': 3, 'style': 'resize:none;'}
            ),
            'instrucciones_especiales': forms.Textarea(
                attrs={'rows': 3, 'style': 'resize:none;'}
            ),
        }


class ParadaForm(forms.ModelForm):
    class Meta:
        model = Parada
        fields = [
            'pedido', 'secuencia', 'estado_entrega',
            'hora_llegada_estimada', 'hora_llegada_real',
            'fecha_entrega_real', 'atendido_por',
            'motivo_fallo', 'observaciones',
        ]


class CambiarEstadoViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = ['estado', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(
                attrs={
                    'rows': 6,
                    'style': 'resize:none;',  # <- aquí se mata el estiramiento
                }
            ),
        }


class CambiarEstadoPedidoForm(forms.Form):
    nuevo_estado = forms.ModelChoiceField(
        queryset=EstadoPedido.objects.all(),
        label="Nuevo estado",
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Comentario",
    )
