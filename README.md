# Proyecto GM Express

Sistema de gestión web desarrollado con Django para GM Express.

## Descripción

Este proyecto es una aplicación web diseñada para la administración y gestión de procesos internos de GM Express. Permite el manejo de usuarios, autenticación y diversas funcionalidades operativas.

## Tecnologías Utilizadas

*   **Python**
*   **Django 5.2**
*   **MySQL** (Base de datos)
*   **Bootstrap 5** (Frontend)
*   **Crispy Forms** (Gestión de formularios)

## Requisitos Previos

Asegúrate de tener instalado lo siguiente antes de comenzar:

*   Python 3.10 o superior
*   MySQL Server
*   Git

## Instalación y Configuración

Sigue estos pasos para configurar el proyecto en tu entorno local:

1.  **Clonar el repositorio**

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd proyecto_gmexpress
    ```

2.  **Crear y activar un entorno virtual**

    ```bash
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar dependencias**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar la base de datos**

    Asegúrate de tener una base de datos MySQL creada. Luego, configura las credenciales en el archivo `settings.py` o mediante variables de entorno si están configuradas.

5.  **Aplicar migraciones**

    ```bash
    python manage.py migrate
    ```

6.  **Crear un superusuario (Opcional)**

    Para acceder al panel de administración:

    ```bash
    python manage.py createsuperuser
    ```

7.  **Ejecutar el servidor de desarrollo**

    ```bash
    python manage.py runserver
    ```

    Accede al proyecto en `http://127.0.0.1:8000/`.

## Estructura del Proyecto

*   `config/`: Configuraciones principales del proyecto Django.
*   `gestion_gmexpress/`: Aplicación principal con la lógica de negocio, modelos, vistas y templates.
*   `templates/`: Plantillas HTML globales.
*   `static/`: Archivos estáticos (CSS, JS, imágenes).

## Contribución

1.  Haz un Fork del proyecto.
2.  Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`).
3.  Haz Commit de tus cambios (`git commit -m 'Agrega nueva funcionalidad'`).
4.  Haz Push a la rama (`git push origin feature/nueva-funcionalidad`).
5.  Abre un Pull Request.
