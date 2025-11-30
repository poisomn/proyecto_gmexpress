
import os

content = """{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold text-primary">Hoja de Ruta</h2>
        <a href="{% url 'mis-viajes' %}" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left"></i> Volver
        </a>
    </div>

    <!-- Info del Viaje -->
    <div class="card mb-4 shadow-sm border-0">
        <div class="card-body bg-light rounded">
            <h4 class="card-title text-dark mb-3">{{ viaje.nombre_ruta }}</h4>
            <div class="row">
                <div class="col-md-4">
                    <p class="mb-1 text-muted">Fecha</p>
                    <p class="fw-bold">{{ viaje.fecha_programada|date:"d/m/Y" }}</p>
                </div>
                <div class="col-md-4">
                    <p class="mb-1 text-muted">Vehículo</p>
                    <p class="fw-bold">{{ viaje.vehiculo.placa }}</p>
                </div>
                <div class="col-md-4">
                    <p class="mb-1 text-muted">Estado</p>
                    <span class="badge {% if viaje.estado.nombre == 'COMPLETADO' %}bg-success{% else %}bg-info{% endif %}">
                        {{ viaje.estado.nombre }}
                    </span>
                </div>
            </div>
        </div>
    </div>

    <h5 class="mb-3 text-secondary">Paradas ({{ paradas|length }})</h5>

    <div class="accordion" id="accordionParadas">
        {% for parada in paradas %}
        <div class="accordion-item mb-3 border shadow-sm rounded overflow-hidden">
            <h2 class="accordion-header" id="heading{{ parada.id }}">
                <button class="accordion-button {% if not forloop.first %}collapsed{% endif %} {% if parada.estado_entrega.nombre == 'ENTREGADO' %}bg-success-subtle text-success{% elif parada.estado_entrega.nombre == 'FALLIDO' %}bg-danger-subtle text-danger{% endif %}"
                    type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ parada.id }}"
                    aria-expanded="{% if forloop.first %}true{% else %}false{% endif %}"
                    aria-controls="collapse{{ parada.id }}">

                    <div class="d-flex align-items-center w-100 justify-content-between me-3">
                        <div>
                            <span class="fw-bold me-2">#{{ parada.secuencia }}</span>
                            <span class="fw-semibold">{{ parada.pedido.cliente.nombre }}</span>
                        </div>
                        <span class="badge {% if parada.estado_entrega.nombre == 'ENTREGADO' %}bg-success{% elif parada.estado_entrega.nombre == 'FALLIDO' %}bg-danger{% else %}bg-secondary{% endif %}">
                            {{ parada.estado_entrega.nombre }}
                        </span>
                    </div>
                </button>
            </h2>
            <div id="collapse{{ parada.id }}" class="accordion-collapse collapse {% if forloop.first %}show{% endif %}"
                aria-labelledby="heading{{ parada.id }}" data-bs-parent="#accordionParadas">
                <div class="accordion-body bg-white">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p class="mb-1"><small class="text-muted">Dirección</small></p>
                            <p class="fw-medium">{{ parada.pedido.direccion_entrega }}, {{ parada.pedido.comuna }}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><small class="text-muted">Contacto</small></p>
                            <p class="fw-medium">{{ parada.pedido.cliente.telefono }}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><small class="text-muted">Cajas/Raciones</small></p>
                            <p class="fw-medium">{{ parada.pedido.cantidad_cajas }}</p>
                        </div>
                        <div class="col-12">
                            <p class="mb-1"><small class="text-muted">Instrucciones</small></p>
                            <div class="alert alert-light border p-2">
                                {{ parada.pedido.instrucciones_especiales|default:"Sin instrucciones especiales." }}
                            </div>
                        </div>
                    </div>

                    <hr>

                    <form action="{% url 'entrega-update' parada.id %}" method="post">
                        {% csrf_token %}
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="estado_entrega_{{ parada.id }}" class="form-label fw-bold">Actualizar Estado</label>
                                <select name="estado_entrega" id="estado_entrega_{{ parada.id }}" class="form-select">
                                    {% for estado in estados_entrega %}
                                        <option value="{{ estado.id }}" {% if estado.id == parada.estado_entrega.id %}selected{% endif %}>{{ estado.nombre }}</option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="col-md-6 mb-3">
                                <label for="motivo_fallo_{{ parada.id }}" class="form-label">Motivo (si falló)</label>
                                <select name="motivo_fallo" id="motivo_fallo_{{ parada.id }}" class="form-select">
                                    <option value="">-- Seleccionar --</option>
                                    <option value="CLIENTE_AUSENTE" {% if parada.motivo_fallo == 'CLIENTE_AUSENTE' %}selected{% endif %}>Cliente ausente</option>
                                    <option value="DIRECCION_INCORRECTA" {% if parada.motivo_fallo == 'DIRECCION_INCORRECTA' %}selected{% endif %}>Dirección incorrecta</option>
                                    <option value="CLIENTE_RECHAZO" {% if parada.motivo_fallo == 'CLIENTE_RECHAZO' %}selected{% endif %}>Cliente rechazó</option>
                                    <option value="ACCESO_BLOQUEADO" {% if parada.motivo_fallo == 'ACCESO_BLOQUEADO' %}selected{% endif %}>Acceso bloqueado</option>
                                    <option value="OTRO" {% if parada.motivo_fallo == 'OTRO' %}selected{% endif %}>Otro</option>
                                </select>
                            </div>

                            <div class="col-12 mb-3">
                                <label for="observaciones_{{ parada.id }}" class="form-label">Observaciones</label>
                                <textarea name="observaciones" id="observaciones_{{ parada.id }}" class="form-control"
                                    rows="2"
                                    placeholder="Comentarios adicionales...">{{ parada.observaciones }}</textarea>
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary w-100 py-2 fw-bold">
                            Confirmar Actualización
                        </button>
                    </form>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

file_path = r'c:\Users\chris\proyecto_gmexpress\gestion_gmexpress\templates\gestion_gmexpress\hoja_ruta.html'
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully wrote to {file_path}")
