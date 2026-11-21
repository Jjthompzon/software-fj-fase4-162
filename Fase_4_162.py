"""
====================================================================================================
UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA - UNAD
ESCUELA DE CIENCIAS BÁSICAS, TECNOLOGÍA E INGENIERÍA (ECBTI)
CURSO: PROGRAMACIÓN (CÓDIGO: 213023)
FASE 4: COMPONENTE PRÁCTICO - PRÁCTICAS SIMULADAS
====================================================================================================
DATOS ACADÉMICOS DEL ESTUDIANTE:
  • Nombre: Astrid Natalia Pineda Alvarez
  • Cédula de Ciudadanía: 1036630806
  • Programa Académico: Ingeniería de Sistemas
  • Centro (CEAD): Medellín
  • Grupo Colaborativo: 213023_162
  • Tutor Asignado: Johnny Alirio Blanquicett Cardona
  • Proyecto: Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas

DESCRIPCIÓN TÉCNICA DEL SISTEMA:
El presente software implementa la solución completa solicitada en el Anexo 3, basada en una
arquitectura orientada a objetos sin uso de bases de datos relacionales ni motores externos.
La gestión de entidades se realiza íntegramente mediante objetos y colecciones en memoria,
garantizando la integridad del negocio mediante:
  1. Jerarquía de Excepciones Personalizadas derivadas de SoftwareFJError.
  2. Implementación exhaustiva de estructuras try / except / else / finally.
  3. Encadenamiento semántico de excepciones técnicas (raise ... from ...).
  4. Módulo de Logging profesional que audita eventos e incidencias en 'software_fj.log'.
  5. Abstracción y Polimorfismo en tres líneas de servicio: ReservaSala, AlquilerEquipo y AsesoriaEspecializada.
  6. Suite automatizada de al menos 10 simulaciones (válidas e inválidas) que certifican
     la resiliencia y estabilidad continua de la aplicación ante fallos severos.
====================================================================================================
"""

import os
import re
import sys
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any


# ==================================================================================================
# 1. SUBSISTEMA DE AUDITORÍA Y LOGGING
# ==================================================================================================

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
NOMBRE_ARCHIVO_LOG = os.path.join(DIRECTORIO_ACTUAL, "software_fj.log")

def configurar_subsistema_logging(ruta_log: str = NOMBRE_ARCHIVO_LOG) -> logging.Logger:
    """
    Configura y retorna el registrador (logger) oficial de la aplicación.
    Escribe simultáneamente en archivo de texto plano y en consola con formato cronológico.
    """
    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.DEBUG)

    # Evita duplicación de handlers si se reinicializa
    if not logger.handlers:
        # Formato estándar de auditoría de ingeniería
        formato = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. Handler para archivo en disco
        file_handler = logging.FileHandler(ruta_log, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)

        # 2. Handler para consola estándar
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formato)
        logger.addHandler(console_handler)

    return logger

log_sistema = configurar_subsistema_logging()


# ==================================================================================================
# 2. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==================================================================================================

class SoftwareFJError(Exception):
    """
    Excepción raíz para todo el dominio del sistema Software FJ.
    Permite capturar cualquier error propio de la lógica de negocio de la aplicación.
    """
    def __init__(self, mensaje: str, codigo_error: str = "ERR-GEN-001"):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        return f"[{self.codigo_error}] {self.mensaje}"


class ClienteInvalidoError(SoftwareFJError):
    """Se lanza cuando los datos de un cliente no cumplen con las reglas de validación."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-CLI-002")


class ServicioInvalidoError(SoftwareFJError):
    """Se lanza ante parámetros inconsistentes o defectuosos en la definición de un servicio."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-SRV-003")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando un servicio solicitado se encuentra inactivo, sin cupo o sin stock físico."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-SRV-004")


class ReservaInvalidaError(SoftwareFJError):
    """Se lanza ante inconsistencias en los parámetros de una reserva."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-RSV-005")


class CapacidadExcedidaError(ReservaInvalidaError):
    """Se lanza cuando el número de asistentes supera la capacidad física máxima permitida."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.codigo_error = "ERR-CAP-006"


class TransicionEstadoInvalidaError(SoftwareFJError):
    """Se lanza al intentar cambiar el estado de una reserva mediante una operación no permitida."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-STA-007")


class CalculoTarifaError(SoftwareFJError):
    """Se lanza cuando ocurre una inconsistencia aritmética o de parámetros al calcular costos."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo_error="ERR-TAR-008")


# ==================================================================================================
# 3. ENUMERACIONES Y CLASE ABSTRACTA BASE DE ENTIDAD
# ==================================================================================================

class EstadoReserva(Enum):
    """Enumera los estados controlados del ciclo de vida de una reserva."""
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    FINALIZADA = "Finalizada"


class EntidadBase(ABC):
    """
    Clase abstracta pura que define los atributos y comportamientos universales
    de cualquier entidad administrada en el sistema Software FJ.
    """
    def __init__(self, id_entidad: str):
        if not id_entidad or not str(id_entidad).strip():
            raise ValueError("El identificador de la entidad no puede ser nulo ni vacío.")
        self._id_entidad: str = str(id_entidad).strip().upper()
        self._fecha_registro: datetime = datetime.now()

    @property
    def id_entidad(self) -> str:
        """Permite consultar el identificador único de la entidad."""
        return self._id_entidad

    @property
    def fecha_registro(self) -> datetime:
        """Permite consultar la marca temporal exacta de registro de la entidad."""
        return self._fecha_registro

    @abstractmethod
    def validar(self) -> bool:
        """Verifica que los invariantes del objeto sean correctos."""
        pass

    @abstractmethod
    def obtener_resumen(self) -> Dict[str, Any]:
        """Retorna un diccionario estructurado con los atributos clave de la entidad."""
        pass


# ==================================================================================================
# 4. CLASE CLIENTE CON ENCAPSULAMIENTO Y VALIDACIONES ROBUSTAS
# ==================================================================================================

class Cliente(EntidadBase):
    """
    Representa a un cliente en Software FJ.
    Aplica encapsulamiento mediante variables protegidas con guion bajo (_) y decoradores
    @property y @setter para validar formato de correo, documento y datos obligatorios.
    """
    def __init__(self, cedula: str, nombre: str, correo: str, telefono: str):
        super().__init__(id_entidad=f"CLI-{cedula.strip()}")
        self._cedula: str = ""
        self._nombre: str = ""
        self._correo: str = ""
        self._telefono: str = ""

        # Asignación controlada a través de setters con validación defensiva
        self.cedula = cedula
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
        self.validar()

    # --- Propiedades y Validaciones Defensivas ---

    @property
    def cedula(self) -> str:
        """Permite consultar la cédula o número de documento del cliente."""
        return self._cedula

    @cedula.setter
    def cedula(self, valor: str) -> None:
        """Valida que la cédula sea numérica y contenga entre 6 y 12 caracteres."""
        if not valor or not str(valor).strip():
            raise ClienteInvalidoError("La cédula del cliente es obligatoria y no puede estar vacía.")
        val_limpio = str(valor).strip()
        if not val_limpio.isdigit():
            raise ClienteInvalidoError(f"La cédula '{val_limpio}' es inválida: debe contener únicamente dígitos.")
        if not (6 <= len(val_limpio) <= 12):
            raise ClienteInvalidoError(f"Longitud de cédula inválida ({len(val_limpio)} dígitos). Debe tener entre 6 y 12 dígitos.")
        self._cedula = val_limpio

    @property
    def nombre(self) -> str:
        """Permite consultar el nombre completo del cliente."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Valida que el nombre contenga texto válido y no caracteres vacíos."""
        if not valor or not str(valor).strip():
            raise ClienteInvalidoError("El nombre del cliente no puede estar vacío.")
        val_limpio = str(valor).strip()
        if len(val_limpio) < 3:
            raise ClienteInvalidoError("El nombre debe tener al menos 3 caracteres de longitud.")
        self._nombre = val_limpio

    @property
    def correo(self) -> str:
        """Permite consultar el correo electrónico del cliente."""
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """Valida el formato estándar de correo electrónico mediante expresión regular."""
        if not valor or not str(valor).strip():
            raise ClienteInvalidoError("El correo electrónico del cliente no puede estar vacío.")
        val_limpio = str(valor).strip().lower()
        patron_correo = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        if not re.match(patron_correo, val_limpio):
            raise ClienteInvalidoError(f"El correo '{val_limpio}' no posee una sintaxis válida (ejemplo@dominio.com).")
        self._correo = val_limpio

    @property
    def telefono(self) -> str:
        """Permite consultar el teléfono de contacto del cliente."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        """Valida que el teléfono contenga al menos 7 dígitos."""
        if not valor or not str(valor).strip():
            raise ClienteInvalidoError("El teléfono de contacto no puede estar vacío.")
        val_limpio = str(valor).strip().replace(" ", "").replace("-", "")
        if not val_limpio.isdigit() or len(val_limpio) < 7:
            raise ClienteInvalidoError(f"El teléfono '{val_limpio}' es inválido. Debe contener al menos 7 dígitos numéricos.")
        self._telefono = val_limpio

    def validar(self) -> bool:
        """Garantiza la consistencia integral del objeto Cliente."""
        if not self._cedula or not self._nombre or not self._correo:
            raise ClienteInvalidoError("Cliente incompleto: faltan parámetros obligatorios.")
        return True

    def obtener_resumen(self) -> Dict[str, Any]:
        """Retorna el compendio de datos del cliente en formato de diccionario."""
        return {
            "id_entidad": self._id_entidad,
            "cedula": self._cedula,
            "nombre": self._nombre,
            "correo": self._correo,
            "telefono": self._telefono,
            "fecha_registro": self._fecha_registro.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __str__(self) -> str:
        return f"Cliente [{self._cedula}] {self._nombre} - Correo: {self._correo}"


# ==================================================================================================
# 5. CLASE ABSTRACTA SERVICIO Y SUBCLASES ESPECIALIZADAS (POLIMORFISMO)
# ==================================================================================================

class Servicio(EntidadBase):
    """
    Clase abstracta que define el contrato operacional de cualquier servicio ofrecido por Software FJ.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_base_hora: float, disponible: bool = True):
        super().__init__(id_entidad=id_servicio)
        if not nombre or not str(nombre).strip():
            raise ServicioInvalidoError("El nombre del servicio no puede ser vacío.")
        if tarifa_base_hora < 0:
            raise ServicioInvalidoError(f"La tarifa base por hora ({tarifa_base_hora}) no puede ser negativa.")

        self._nombre: str = str(nombre).strip()
        self._tarifa_base_hora: float = float(tarifa_base_hora)
        self._disponible: bool = bool(disponible)

    @property
    def nombre(self) -> str:
        """Permite consultar el nombre comercial del servicio."""
        return self._nombre

    @property
    def tarifa_base_hora(self) -> float:
        """Permite consultar la tarifa base por hora."""
        return self._tarifa_base_hora

    @property
    def disponible(self) -> bool:
        """Permite consultar la disponibilidad operativa del servicio."""
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        """Modifica el estado de disponibilidad del servicio."""
        self._disponible = bool(estado)

    # --- Métodos Abstractos y Polimórficos ---

    @abstractmethod
    def calcular_costo(self, duracion_horas: float, con_iva: bool = True,
                       descuento_porcentaje: float = 0.0, **kwargs) -> float:
        """
        Calcula el costo total del servicio en función de la duración y parámetros de sobrecarga.
        """
        pass

    @abstractmethod
    def verificar_disponibilidad(self, **kwargs) -> bool:
        """Comprueba si el servicio puede ser reservado según sus restricciones particulares."""
        pass


class ReservaSala(Servicio):
    """
    Servicio especializado en el arrendamiento de salas de juntas y capacitación.
    Implementa restricciones de aforo físico y sobrecosto por equipamiento audiovisual.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_base_hora: float,
                 capacidad_maxima: int, tiene_videobeam: bool = True, tiene_sonido: bool = True):
        super().__init__(id_servicio, nombre, tarifa_base_hora)
        if capacidad_maxima <= 0:
            raise ServicioInvalidoError(f"La capacidad máxima de la sala ({capacidad_maxima}) debe ser mayor a cero.")

        self._capacidad_maxima: int = int(capacidad_maxima)
        self._tiene_videobeam: bool = bool(tiene_videobeam)
        self._tiene_sonido: bool = bool(tiene_sonido)

    @property
    def capacidad_maxima(self) -> int:
        """Permite consultar el aforo máximo de la sala."""
        return self._capacidad_maxima

    def verificar_disponibilidad(self, num_personas: Optional[int] = None, **kwargs) -> bool:
        """Valida que la sala esté disponible y que no se exceda el aforo máximo permitido."""
        if not self._disponible:
            raise ServicioNoDisponibleError(f"La sala '{self._nombre}' no se encuentra habilitada actualmente.")

        if num_personas is not None:
            if num_personas <= 0:
                raise CapacidadExcedidaError("El número de personas debe ser mayor a cero.")
            if num_personas > self._capacidad_maxima:
                raise CapacidadExcedidaError(
                    f"Aforo excedido en sala '{self._nombre}'. Solicitado: {num_personas}, Capacidad máxima: {self._capacidad_maxima} personas."
                )
        return True

    def calcular_costo(self, duracion_horas: float, con_iva: bool = True,
                       descuento_porcentaje: float = 0.0, **kwargs) -> float:
        """
        Sobreescritura del método calcular_costo() con sobrecarga técnica.
        Añade recargos opcionales por dotación tecnológica y aplica impuestos/descuentos.
        """
        if duracion_horas <= 0:
            raise CalculoTarifaError("La duración de la reserva de sala debe ser un valor positivo mayor a 0 horas.")

        try:
            costo_bruto = self._tarifa_base_hora * float(duracion_horas)

            # Recargo tecnológico si posee recursos adicionales
            recargo_equipos = 0.0
            if self._tiene_videobeam:
                recargo_equipos += 15000.0 * duracion_horas
            if self._tiene_sonido:
                recargo_equipos += 10000.0 * duracion_horas

            subtotal = costo_bruto + recargo_equipos

            # Aplicación de descuento
            if not (0.0 <= descuento_porcentaje <= 100.0):
                raise ValueError("El porcentaje de descuento debe situarse entre 0% y 100%.")

            descuento = subtotal * (descuento_porcentaje / 100.0)
            base_imponible = subtotal - descuento

            # IVA oficial del 19%
            total = base_imponible * 1.19 if con_iva else base_imponible
            return round(total, 2)

        except Exception as exc:
            # Demostración explícita de encadenamiento de excepciones
            raise CalculoTarifaError(f"Fallo en la liquidación tarifaria de la sala: {str(exc)}") from exc

    def validar(self) -> bool:
        return self._capacidad_maxima > 0 and self._tarifa_base_hora >= 0

    def obtener_resumen(self) -> Dict[str, Any]:
        return {
            "tipo": "Reserva de Sala",
            "id": self._id_entidad,
            "nombre": self._nombre,
            "capacidad": f"{self._capacidad_maxima} personas",
            "videobeam": "Sí" if self._tiene_videobeam else "No",
            "sonido": "Sí" if self._tiene_sonido else "No",
            "tarifa_hora": f"${self._tarifa_base_hora:,.2f}",
            "disponible": self._disponible
        }


class AlquilerEquipo(Servicio):
    """
    Servicio especializado en el arrendamiento de equipamiento tecnológico (portátiles, servidores).
    Implementa control estricto de unidades en inventario físico y depósito de garantía.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_base_hora: float,
                 unidades_disponibles: int, deposito_garantia: float = 100000.0):
        super().__init__(id_servicio, nombre, tarifa_base_hora)
        if unidades_disponibles < 0:
            raise ServicioInvalidoError("Las unidades de inventario no pueden ser negativas.")
        if deposito_garantia < 0:
            raise ServicioInvalidoError("El depósito de garantía no puede ser negativo.")

        self._unidades_disponibles: int = int(unidades_disponibles)
        self._deposito_garantia: float = float(deposito_garantia)

    @property
    def unidades_disponibles(self) -> int:
        """Permite consultar las unidades físicas disponibles en stock."""
        return self._unidades_disponibles

    def verificar_disponibilidad(self, cantidad: int = 1, **kwargs) -> bool:
        """Comprueba que existan unidades suficientes en el stock de inventario."""
        if not self._disponible:
            raise ServicioNoDisponibleError(f"El equipo '{self._nombre}' está dado de baja temporalmente.")
        if cantidad <= 0:
            raise ServicioInvalidoError("La cantidad solicitada para alquiler debe ser mayor a cero.")
        if self._unidades_disponibles < cantidad:
            raise ServicioNoDisponibleError(
                f"Stock insuficiente para '{self._nombre}'. Disponibles: {self._unidades_disponibles}, Solicitadas: {cantidad}."
            )
        return True

    def descontar_stock(self, cantidad: int = 1) -> None:
        """Reduce el stock al consolidarse una reserva."""
        self.verificar_disponibilidad(cantidad=cantidad)
        self._unidades_disponibles -= cantidad
        if self._unidades_disponibles == 0:
            self._disponible = False

    def devolver_stock(self, cantidad: int = 1) -> None:
        """Devuelve unidades al stock al cancelarse o finalizarse el servicio."""
        self._unidades_disponibles += cantidad
        self._disponible = True

    def calcular_costo(self, duracion_horas: float, con_iva: bool = True,
                       descuento_porcentaje: float = 0.0, cantidad: int = 1, **kwargs) -> float:
        """Sobreescritura del método calcular_costo() considerando cantidad de unidades alquiladas."""
        if duracion_horas <= 0:
            raise CalculoTarifaError("La duración del alquiler debe ser mayor a cero horas.")
        if cantidad <= 0:
            raise CalculoTarifaError("La cantidad de equipos alquilados debe ser al menos 1.")

        try:
            subtotal = (self._tarifa_base_hora * duracion_horas * cantidad)
            descuento = subtotal * (descuento_porcentaje / 100.0)
            base = subtotal - descuento
            total = (base * 1.19) if con_iva else base
            return round(total, 2)
        except Exception as exc:
            raise CalculoTarifaError(f"Error en liquidación de alquiler de equipo: {str(exc)}") from exc

    def validar(self) -> bool:
        return self._unidades_disponibles >= 0

    def obtener_resumen(self) -> Dict[str, Any]:
        return {
            "tipo": "Alquiler de Equipo",
            "id": self._id_entidad,
            "nombre": self._nombre,
            "stock_disponible": f"{self._unidades_disponibles} unidades",
            "tarifa_hora": f"${self._tarifa_base_hora:,.2f}",
            "deposito": f"${self._deposito_garantia:,.2f}",
            "disponible": self._disponible
        }


class AsesoriaEspecializada(Servicio):
    """
    Servicio de consultoría técnica en arquitectura de software, ciberseguridad o auditoría.
    Modela recargos según el grado de urgencia del servicio solicitado.
    """
    def __init__(self, id_servicio: str, nombre: str, tarifa_base_hora: float,
                 area_experiencia: str, consultor: str):
        super().__init__(id_servicio, nombre, tarifa_base_hora)
        if not area_experiencia or not str(area_experiencia).strip():
            raise ServicioInvalidoError("El área técnica de la asesoría no puede ser vacía.")
        if not consultor or not str(consultor).strip():
            raise ServicioInvalidoError("Debe asignarse un consultor responsable a la asesoría.")

        self._area_experiencia: str = str(area_experiencia).strip()
        self._consultor: str = str(consultor).strip()

    def verificar_disponibilidad(self, **kwargs) -> bool:
        if not self._disponible:
            raise ServicioNoDisponibleError(
                f"La asesoría en '{self._area_experiencia}' con el consultor '{self._consultor}' no está disponible."
            )
        return True

    def calcular_costo(self, duracion_horas: float, con_iva: bool = True,
                       descuento_porcentaje: float = 0.0, es_urgente: bool = False, **kwargs) -> float:
        """
        Sobreescritura de calcular_costo() con parámetro opcional de urgencia (recargo del 30%).
        """
        if duracion_horas <= 0:
            raise CalculoTarifaError("La duración de la asesoría debe ser superior a 0 horas.")

        try:
            subtotal = self._tarifa_base_hora * duracion_horas
            # Recargo por atención prioritaria / inmediata
            if es_urgente:
                subtotal *= 1.30

            descuento = subtotal * (descuento_porcentaje / 100.0)
            base = subtotal - descuento
            total = (base * 1.19) if con_iva else base
            return round(total, 2)
        except Exception as exc:
            raise CalculoTarifaError(f"Error en liquidación de asesoría: {str(exc)}") from exc

    def validar(self) -> bool:
        return bool(self._area_experiencia) and bool(self._consultor)

    def obtener_resumen(self) -> Dict[str, Any]:
        return {
            "tipo": "Asesoría Especializada",
            "id": self._id_entidad,
            "nombre": self._nombre,
            "area": self._area_experiencia,
            "consultor": self._consultor,
            "tarifa_hora": f"${self._tarifa_base_hora:,.2f}",
            "disponible": self._disponible
        }


# ==================================================================================================
# 6. CLASE RESERVA CON GESTIÓN TRANSICIONAL DE ESTADOS
# ==================================================================================================

class Reserva(EntidadBase):
    """
    Representa una reserva de servicio formalizada por un cliente.
    Controla rigurosamente las transiciones de estado (PENDIENTE -> CONFIRMADA -> CANCELADA)
    utilizando excepciones personalizadas ante operaciones ilegales.
    """
    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio,
                 duracion_horas: float, cantidad_o_aforo: int = 1,
                 con_iva: bool = True, descuento_porcentaje: float = 0.0, es_urgente: bool = False):
        super().__init__(id_entidad=id_reserva)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un objeto Cliente válido y autenticado.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere una instancia válida derivada de Servicio.")
        if duracion_horas <= 0:
            raise ReservaInvalidaError(f"Duración inválida ({duracion_horas}h). Debe ser mayor a 0.")

        self._cliente: Cliente = cliente
        self._servicio: Servicio = servicio
        self._duracion_horas: float = float(duracion_horas)
        self._cantidad_o_aforo: int = int(cantidad_o_aforo)
        self._con_iva: bool = con_iva
        self._descuento_porcentaje: float = descuento_porcentaje
        self._es_urgente: bool = es_urgente

        self._estado: EstadoReserva = EstadoReserva.PENDIENTE
        self._costo_total: float = 0.0
        self._motivo_cancelacion: Optional[str] = None

        # Liquidación inicial
        self.calcular_total()

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion_horas(self) -> float:
        return self._duracion_horas

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def calcular_total(self) -> float:
        """Calcula el costo total invocando polimórficamente el método del servicio."""
        self._costo_total = self._servicio.calcular_costo(
            duracion_horas=self._duracion_horas,
            con_iva=self._con_iva,
            descuento_porcentaje=self._descuento_porcentaje,
            cantidad=self._cantidad_o_aforo,
            num_personas=self._cantidad_o_aforo,
            es_urgente=self._es_urgente
        )
        return self._costo_total

    def confirmar(self) -> None:
        """
        Confirma la reserva verificando disponibilidad física del servicio.
        Lanza TransicionEstadoInvalidaError si la reserva no está en estado PENDIENTE.
        """
        if self._estado != EstadoReserva.PENDIENTE:
            raise TransicionEstadoInvalidaError(
                f"No es posible confirmar la reserva [{self._id_entidad}]: se encuentra en estado '{self._estado.value}'."
            )

        # Validación polimórfica de disponibilidad
        self._servicio.verificar_disponibilidad(
            cantidad=self._cantidad_o_aforo,
            num_personas=self._cantidad_o_aforo
        )

        # Si es alquiler de equipo, se descuenta stock
        if isinstance(self._servicio, AlquilerEquipo):
            self._servicio.descontar_stock(cantidad=self._cantidad_o_aforo)

        self._estado = EstadoReserva.CONFIRMADA

    def cancelar(self, motivo: str) -> None:
        """
        Cancela la reserva y restituye inventarios en caso de alquileres.
        Lanza TransicionEstadoInvalidaError si ya se encontraba cancelada.
        """
        if self._estado == EstadoReserva.CANCELADA:
            raise TransicionEstadoInvalidaError(
                f"La reserva [{self._id_entidad}] ya se encuentra CANCELADA. Operación redundante rechazada."
            )

        if not motivo or not str(motivo).strip():
            raise ReservaInvalidaError("Debe suministrarse un motivo explícito para justificar la cancelación.")

        # Si estaba confirmada y era un equipo, se devuelve el stock
        if self._estado == EstadoReserva.CONFIRMADA and isinstance(self._servicio, AlquilerEquipo):
            self._servicio.devolver_stock(cantidad=self._cantidad_o_aforo)

        self._estado = EstadoReserva.CANCELADA
        self._motivo_cancelacion = str(motivo).strip()

    def validar(self) -> bool:
        return self._duracion_horas > 0 and self._costo_total >= 0

    def obtener_resumen(self) -> Dict[str, Any]:
        return {
            "id_reserva": self._id_entidad,
            "cliente": f"{self._cliente.nombre} ({self._cliente.cedula})",
            "servicio": self._servicio.nombre,
            "tipo_servicio": self._servicio.__class__.__name__,
            "duracion": f"{self._duracion_horas}h",
            "estado": self._estado.value,
            "total": f"${self._costo_total:,.2f}",
            "fecha": self._fecha_registro.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __str__(self) -> str:
        return f"Reserva [{self._id_entidad}] - {self._servicio.nombre} para {self._cliente.nombre} | Estado: {self._estado.value} | Total: ${self._costo_total:,.2f}"


# =========================================================================
# 7. MOTOR PRINCIPAL: SistemaGestionSoftwareFJ (CON TRY / EXCEPT / ELSE / FINALLY)
# =========================================================================

class SistemaGestionSoftwareFJ:
    """
    Controlador central del sistema de Software FJ.
    Administra clientes, catálogo de servicios y reservas en memoria sin bases de datos.
    Implementa de manera estricta bloques try / except / else / finally y encadenamiento.
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._clientes: Dict[str, Cliente] = {}
        self._servicios: Dict[str, Servicio] = {}
        self._reservas: Dict[str, Reserva] = {}
        self._logger: logging.Logger = logger or log_sistema

        self._logger.info("Sistema de Gestión Software FJ inicializado en memoria correctamente.")

    # --- Gestión de Clientes ---

    def registrar_cliente(self, cedula: str, nombre: str, correo: str, telefono: str) -> Cliente:
        """
        Registra un nuevo cliente aplicando validación defensiva y cláusulas try/except/else/finally.
        """
        operacion_exitosa = False
        nuevo_cliente: Optional[Cliente] = None

        try:
            self._logger.debug(f"Iniciando registro de cliente con documento '{cedula}'...")
            cedula_limpia = str(cedula).strip()

            if cedula_limpia in self._clientes:
                raise ClienteInvalidoError(f"El cliente con cédula '{cedula_limpia}' ya se encuentra registrado.")

            # Instanciación sujeta a validaciones
            nuevo_cliente = Cliente(cedula=cedula_limpia, nombre=nombre, correo=correo, telefono=telefono)

        except ClienteInvalidoError as err:
            self._logger.error(f"Fallo al registrar cliente [{cedula}]: {err.mensaje}")
            raise

        except Exception as err_inesperado:
            self._logger.critical(f"Error imprevisto de bajo nivel en registro de cliente: {str(err_inesperado)}")
            # Encadenamiento de excepción semántica
            raise ClienteInvalidoError(f"No fue posible procesar el cliente debido a un fallo inesperado: {str(err_inesperado)}") from err_inesperado

        else:
            # Cláusula ELSE obligatoria: solo se ejecuta si la instanciación fue limpia
            self._clientes[nuevo_cliente.cedula] = nuevo_cliente
            operacion_exitosa = True
            self._logger.info(f"Cliente registrado exitosamente: {nuevo_cliente.nombre} (ID: {nuevo_cliente.cedula})")
            return nuevo_cliente

        finally:
            # Cláusula FINALLY obligatoria: auditoría de terminación de proceso
            estado_txt = "CON ÉXITO" if operacion_exitosa else "CON EXCEPCIÓN"
            self._logger.debug(f"Finalizado ciclo de transacción para registro de cliente [{cedula}] -> Estado: {estado_txt}.")

    # --- Gestión de Servicios ---

    def registrar_servicio(self, servicio: Servicio) -> None:
        """Da de alta un servicio en el catálogo en memoria."""
        try:
            if not isinstance(servicio, Servicio):
                raise ServicioInvalidoError("El elemento a registrar debe heredar de la clase abstracta Servicio.")
            if servicio.id_entidad in self._servicios:
                raise ServicioInvalidoError(f"Ya existe un servicio con código identificador '{servicio.id_entidad}'.")

            servicio.validar()
            self._servicios[servicio.id_entidad] = servicio
            self._logger.info(f"Servicio incorporado al catálogo: [{servicio.id_entidad}] {servicio.nombre}")

        except SoftwareFJError as err:
            self._logger.error(f"Rechazo en alta de servicio: {err}")
            raise

    # --- Gestión de Reservas ---

    def crear_reserva(self, id_reserva: str, cedula_cliente: str, id_servicio: str,
                      duracion_horas: float, cantidad_o_aforo: int = 1,
                      con_iva: bool = True, descuento_porcentaje: float = 0.0, es_urgente: bool = False) -> Reserva:
        """
        Crea una nueva reserva coordinando las entidades correspondientes.
        Aplica try / except / else / finally y valida integridad relacional en memoria.
        """
        reserva_creada: Optional[Reserva] = None
        exito = False

        try:
            self._logger.debug(f"Procesando creación de reserva '{id_reserva}'...")
            id_limpio = str(id_reserva).strip().upper()

            if id_limpio in self._reservas:
                raise ReservaInvalidaError(f"El identificador de reserva '{id_limpio}' ya fue utilizado previamente.")

            # Búsqueda en memoria de cliente
            if cedula_cliente not in self._clientes:
                raise ClienteInvalidoError(f"No existe ningún cliente registrado con documento '{cedula_cliente}'.")
            cliente_obj = self._clientes[cedula_cliente]

            # Búsqueda en memoria de servicio
            if id_servicio not in self._servicios:
                raise ServicioInvalidoError(f"No existe ningún servicio registrado con código '{id_servicio}'.")
            servicio_obj = self._servicios[id_servicio]

            # Instanciación y liquidación
            reserva_creada = Reserva(
                id_reserva=id_limpio,
                cliente=cliente_obj,
                servicio=servicio_obj,
                duracion_horas=duracion_horas,
                cantidad_o_aforo=cantidad_o_aforo,
                con_iva=con_iva,
                descuento_porcentaje=descuento_porcentaje,
                es_urgente=es_urgente
            )

        except (SoftwareFJError, ValueError) as exc:
            self._logger.error(f"Imposible crear reserva [{id_reserva}]: {str(exc)}")
            raise

        else:
            self._reservas[reserva_creada.id_entidad] = reserva_creada
            exito = True
            self._logger.info(
                f"Reserva creada en estado PENDIENTE: [{reserva_creada.id_entidad}] "
                f"Cliente: {cliente_obj.nombre} | Servicio: {servicio_obj.nombre} | Total: ${reserva_creada.costo_total:,.2f}"
            )
            return reserva_creada

        finally:
            self._logger.debug(f"Protocolo de creación para reserva [{id_reserva}] concluido (Éxito={exito}).")

    def confirmar_reserva(self, id_reserva: str) -> None:
        """Confirma una reserva previamente registrada."""
        try:
            id_limpio = str(id_reserva).strip().upper()
            if id_limpio not in self._reservas:
                raise ReservaInvalidaError(f"Reserva con ID '{id_limpio}' no encontrada en el sistema.")

            reserva = self._reservas[id_limpio]
            reserva.confirmar()
            self._logger.info(f"Reserva [{id_limpio}] confirmada exitosamente. Servicio asegurado.")

        except SoftwareFJError as err:
            self._logger.warning(f"Error al confirmar reserva [{id_reserva}]: {err}")
            raise

    def cancelar_reserva(self, id_reserva: str, motivo: str) -> None:
        """Cancela una reserva y audita la causa en el log."""
        try:
            id_limpio = str(id_reserva).strip().upper()
            if id_limpio not in self._reservas:
                raise ReservaInvalidaError(f"Reserva con ID '{id_limpio}' inexistente.")

            reserva = self._reservas[id_limpio]
            reserva.cancelar(motivo=motivo)
            self._logger.warning(f"Reserva [{id_limpio}] CANCELADA. Causa: {motivo}")

        except SoftwareFJError as err:
            self._logger.error(f"Fallo al cancelar reserva [{id_reserva}]: {err}")
            raise

    # --- Consultas de Auditoría ---

    def obtener_resumen_general(self) -> Dict[str, int]:
        """Retorna estadísticas generales de la operación en memoria."""
        return {
            "total_clientes": len(self._clientes),
            "total_servicios": len(self._servicios),
            "total_reservas": len(self._reservas),
            "reservas_confirmadas": sum(1 for r in self._reservas.values() if r.estado == EstadoReserva.CONFIRMADA),
            "reservas_canceladas": sum(1 for r in self._reservas.values() if r.estado == EstadoReserva.CANCELADA),
            "reservas_pendientes": sum(1 for r in self._reservas.values() if r.estado == EstadoReserva.PENDIENTE)
        }


# =========================================================================
# 8. BATERÍA OBLIGATORIA DE 10 SIMULACIONES COMPLETAS (ANEXO 3 Y RÚBRICA)
# =========================================================================

def ejecutar_bateria_simulaciones(sistema: SistemaGestionSoftwareFJ) -> List[Dict[str, Any]]:
    """
    Ejecuta de manera secuencial y no destructiva al menos 10 simulaciones completas,
    combinando operaciones exitosas y errores deliberados.
    Demuestra la resiliencia de la aplicación para registrar incidentes y continuar activa.
    """
    resultados: List[Dict[str, Any]] = []

    print("\n" + "=" * 90)
    print(" INICIANDO BATERÍA OFICIAL DE 10 SIMULACIONES CONTROLADAS - SOFTWARE FJ")
    print("=" * 90)

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 1: Registro Exitoso de Clientes Válidos (Operación Válida)
    # ----------------------------------------------------------------------------------------------
    try:
        c1 = sistema.registrar_cliente("1036630806", "Astrid Natalia Pineda", "anpineda@unadvirtual.edu.co", "3104509876")
        c2 = sistema.registrar_cliente("79065563", "Carlos Andres Mendoza", "cmendoza@gmail.com", "3001234567")
        c3 = sistema.registrar_cliente("52849120", "Diana Marcela Gomez", "dgomez@corporativo.com", "3159876543")
        resultados.append({
            "num": 1,
            "tipo": "VÁLIDA",
            "descripcion": "Registro exitoso de clientes con datos y correos válidos.",
            "resultado": f"3 clientes ingresados: {c1.nombre}, {c2.nombre}, {c3.nombre}.",
            "estado": "SUPERADA"
        })
    except Exception as e:
        resultados.append({"num": 1, "tipo": "VÁLIDA", "descripcion": "Registro de clientes", "resultado": str(e), "estado": "FALLÓ"})

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 2: Registro con Cédula Inválida (Operación Inválida - ClienteInvalidoError)
    # ----------------------------------------------------------------------------------------------
    try:
        sistema.registrar_cliente("1036A45B", "Usuario Invalido", "invalido@test.com", "3001112233")
        resultados.append({"num": 2, "tipo": "INVÁLIDA", "descripcion": "Cédula no numérica", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except ClienteInvalidoError as err:
        resultados.append({
            "num": 2,
            "tipo": "INVÁLIDA",
            "descripcion": "Validación defensiva de cédula alfanumérica errónea.",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 3: Registro con Correo de Formato Incorrecto (Operación Inválida - ClienteInvalidoError)
    # ----------------------------------------------------------------------------------------------
    try:
        sistema.registrar_cliente("1098765432", "Roberto Gomez", "correo_sin_arroba_ni_dominio", "3209876543")
        resultados.append({"num": 3, "tipo": "INVÁLIDA", "descripcion": "Correo inválido", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except ClienteInvalidoError as err:
        resultados.append({
            "num": 3,
            "tipo": "INVÁLIDA",
            "descripcion": "Validación sintáctica de formato de correo con expresión regular.",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 4: Creación Exitosa de Servicios Especializados (Operación Válida)
    # ----------------------------------------------------------------------------------------------
    try:
        s1 = ReservaSala("SAL-01", "Sala de Juntas Ejecutiva Alfa", tarifa_base_hora=45000.0, capacidad_maxima=12, tiene_videobeam=True, tiene_sonido=True)
        s2 = AlquilerEquipo("EQP-01", "Laptops Dell Precision i7 (Lote de Ingeniería)", tarifa_base_hora=20000.0, unidades_disponibles=4, deposito_garantia=150000.0)
        s3 = AsesoriaEspecializada("ASE-01", "Consultoría en Ciberseguridad e Infraestructura", tarifa_base_hora=90000.0, area_experiencia="Ciberseguridad", consultor="Ing. Fernando Torres")

        sistema.registrar_servicio(s1)
        sistema.registrar_servicio(s2)
        sistema.registrar_servicio(s3)

        resultados.append({
            "num": 4,
            "tipo": "VÁLIDA",
            "descripcion": "Incorporación de los 3 tipos de servicios al catálogo en memoria.",
            "resultado": "Servicios SAL-01, EQP-01 y ASE-01 registrados con éxito.",
            "estado": "SUPERADA"
        })
    except Exception as e:
        resultados.append({"num": 4, "tipo": "VÁLIDA", "descripcion": "Registro de servicios", "resultado": str(e), "estado": "FALLÓ"})

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 5: Creación de Servicio con Tarifa Negativa (Operación Inválida - ServicioInvalidoError)
    # ----------------------------------------------------------------------------------------------
    try:
        s_invalido = ReservaSala("SAL-NEG", "Sala Inconsistente", tarifa_base_hora=-35000.0, capacidad_maxima=10)
        sistema.registrar_servicio(s_invalido)
        resultados.append({"num": 5, "tipo": "INVÁLIDA", "descripcion": "Tarifa negativa", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except ServicioInvalidoError as err:
        resultados.append({
            "num": 5,
            "tipo": "INVÁLIDA",
            "descripcion": "Restricción de costo horario negativo en catálogo.",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 6: Reserva y Confirmación Exitosa de Sala (Operación Válida)
    # ----------------------------------------------------------------------------------------------
    try:
        r1 = sistema.crear_reserva("RSV-1001", "1036630806", "SAL-01", duracion_horas=4.0, cantidad_o_aforo=8, con_iva=True, descuento_porcentaje=10.0)
        sistema.confirmar_reserva("RSV-1001")
        resultados.append({
            "num": 6,
            "tipo": "VÁLIDA",
            "descripcion": "Reserva de sala con sobrecarga de descuento e IVA y confirmación.",
            "resultado": f"Reserva [{r1.id_entidad}] confirmada. Costo Total Liquidado: ${r1.costo_total:,.2f}.",
            "estado": "SUPERADA"
        })
    except Exception as e:
        resultados.append({"num": 6, "tipo": "VÁLIDA", "descripcion": "Reserva de sala", "resultado": str(e), "estado": "FALLÓ"})

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 7: Capacidad Excedida en Reserva de Sala (Operación Inválida - CapacidadExcedidaError)
    # ----------------------------------------------------------------------------------------------
    try:
        r2 = sistema.crear_reserva("RSV-1002", "79065563", "SAL-01", duracion_horas=2.0, cantidad_o_aforo=25)
        sistema.confirmar_reserva("RSV-1002")
        resultados.append({"num": 7, "tipo": "INVÁLIDA", "descripcion": "Aforo superado", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except CapacidadExcedidaError as err:
        resultados.append({
            "num": 7,
            "tipo": "INVÁLIDA",
            "descripcion": "Control de aforo máximo en sala (Solicitado: 25 personas, Capacidad: 12).",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 8: Alquiler con Stock Agotado (Operación Inválida - ServicioNoDisponibleError)
    # ----------------------------------------------------------------------------------------------
    try:
        # El lote EQP-01 tiene 4 unidades; se reservan 4 exitosamente y luego se intenta pedir más
        r3 = sistema.crear_reserva("RSV-1003", "52849120", "EQP-01", duracion_horas=6.0, cantidad_o_aforo=4)
        sistema.confirmar_reserva("RSV-1003")

        # Intento de reservar cuando el stock ya es 0
        r4 = sistema.crear_reserva("RSV-1004", "1036630806", "EQP-01", duracion_horas=2.0, cantidad_o_aforo=1)
        sistema.confirmar_reserva("RSV-1004")
        resultados.append({"num": 8, "tipo": "INVÁLIDA", "descripcion": "Stock agotado", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except ServicioNoDisponibleError as err:
        resultados.append({
            "num": 8,
            "tipo": "INVÁLIDA",
            "descripcion": "Validación de stock físico agotado en alquiler de equipamiento.",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 9: Transición de Estado Inválida (Operación Inválida - TransicionEstadoInvalidaError)
    # ----------------------------------------------------------------------------------------------
    try:
        # Se cancela la reserva RSV-1001 y luego se intenta cancelar por segunda vez
        sistema.cancelar_reserva("RSV-1001", motivo="Reunión aplazada por el cliente")
        # Segundo intento de cancelación no permitido
        sistema.cancelar_reserva("RSV-1001", motivo="Cancelación duplicada errónea")
        resultados.append({"num": 9, "tipo": "INVÁLIDA", "descripcion": "Cancelación duplicada", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except TransicionEstadoInvalidaError as err:
        resultados.append({
            "num": 9,
            "tipo": "INVÁLIDA",
            "descripcion": "Prevención de transición ilegal sobre reserva ya cancelada.",
            "resultado": f"Capturada excepción esperada: {err}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 10: Encadenamiento de Excepciones en Cálculo Tarifario (Operación Inválida - CalculoTarifaError)
    # ----------------------------------------------------------------------------------------------
    try:
        # Invocación directa a servicio con porcentaje de descuento ilógico (> 100%)
        servicio_sala = sistema._servicios["SAL-01"]
        servicio_sala.calcular_costo(duracion_horas=3.0, descuento_porcentaje=150.0)
        resultados.append({"num": 10, "tipo": "INVÁLIDA", "descripcion": "Cálculo incoherente", "resultado": "Error no detectado", "estado": "FALLÓ"})
    except CalculoTarifaError as err:
        causa_original = err.__cause__
        resultados.append({
            "num": 10,
            "tipo": "INVÁLIDA",
            "descripcion": "Encadenamiento semántico de excepciones (CalculoTarifaError from ValueError).",
            "resultado": f"Excepción principal: {err} | Causa de origen: {repr(causa_original)}",
            "estado": "SUPERADA"
        })

    # ----------------------------------------------------------------------------------------------
    # SIMULACIÓN 11 (Adicional): Reserva Exitosa de Asesoría con Recargo de Urgencia (Operación Válida)
    # ----------------------------------------------------------------------------------------------
    try:
        r_ase = sistema.crear_reserva("RSV-1005", "1036630806", "ASE-01", duracion_horas=5.0, es_urgente=True, con_iva=True)
        sistema.confirmar_reserva("RSV-1005")
        resultados.append({
            "num": 11,
            "tipo": "VÁLIDA",
            "descripcion": "Asesoría especializada con recargo por urgencia del 30% e IVA.",
            "resultado": f"Reserva [{r_ase.id_entidad}] confirmada. Costo Total: ${r_ase.costo_total:,.2f}.",
            "estado": "SUPERADA"
        })
    except Exception as e:
        resultados.append({"num": 11, "tipo": "VÁLIDA", "descripcion": "Asesoría con urgencia", "resultado": str(e), "estado": "FALLÓ"})

    # Reporte consolidado en consola
    print("\n" + "-" * 90)
    print(f"{'#':<3} | {'TIPO':<9} | {'ESTADO':<9} | {'DESCRIPCIÓN OPERATIVA':<40}")
    print("-" * 90)
    for r in resultados:
        print(f"{r['num']:<3} | {r['tipo']:<9} | {r['estado']:<9} | {r['descripcion']:<40}")
        print(f"    --> Detalle: {r['resultado']}")
    print("=" * 90)
    print(" BATERÍA CONCLUIDA: Todas las excepciones fueron manejadas y auditadas en 'software_fj.log'.\n")

    return resultados


# =========================================================================
# 9. MENÚ INTERACTIVO EN CONSOLA Y EJECUCIÓN PRINCIPAL
# =========================================================================

def mostrar_menu_interactivo(sistema: SistemaGestionSoftwareFJ) -> None:
    """Despliega un menú en consola para interacción manual o pruebas autónomas."""
    while True:
        print("\n" + "=" * 70)
        print(" SISTEMA INTEGRAL SOFTWARE FJ - UNAD GRUPO 162")
        print(" Estudiante: Astrid Natalia Pineda Alvarez (C.C. 1036630806)")
        print("=" * 70)
        print(" [1] Ejecutar batería obligatoria de 10 simulaciones completas")
        print(" [2] Registrar nuevo cliente")
        print(" [3] Consultar catálogo de servicios disponibles")
        print(" [4] Crear y confirmar nueva reserva")
        print(" [5] Cancelar una reserva existente")
        print(" [6] Ver resumen estadístico del sistema en memoria")
        print(" [7] Consultar las últimas líneas del archivo de log")
        print(" [0] Salir de la aplicación")
        print("-" * 70)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            ejecutar_bateria_simulaciones(sistema)

        elif opcion == "2":
            print("\n--- REGISTRO DE CLIENTE ---")
            ced = input("Cédula: ").strip()
            nom = input("Nombre completo: ").strip()
            cor = input("Correo electrónico: ").strip()
            tel = input("Teléfono: ").strip()
            try:
                cli = sistema.registrar_cliente(ced, nom, cor, tel)
                print(f"¡Éxito! Cliente registrado: {cli}")
            except SoftwareFJError as ex:
                print(f"Error controlado: {ex}")

        elif opcion == "3":
            print("\n--- CATÁLOGO DE SERVICIOS ---")
            if not sistema._servicios:
                print("El catálogo se encuentra vacío. Ejecute la opción [1] para cargar servicios iniciales.")
            else:
                for s in sistema._servicios.values():
                    print(f" • {s.obtener_resumen()}")

        elif opcion == "4":
            print("\n--- CREAR RESERVA ---")
            id_r = input("ID Reserva (ej. RSV-5001): ").strip()
            ced = input("Cédula del cliente: ").strip()
            id_s = input("ID Servicio (ej. SAL-01, EQP-01, ASE-01): ").strip()
            dur_str = input("Duración en horas: ").strip()
            cant_str = input("Cantidad de equipos o aforo de personas: ").strip() or "1"
            try:
                dur = float(dur_str)
                cant = int(cant_str)
                res = sistema.crear_reserva(id_r, ced, id_s, duracion_horas=dur, cantidad_o_aforo=cant)
                conf = input(f"Total liquidado: ${res.costo_total:,.2f}. ¿Desea confirmar ahora? (S/N): ").strip().upper()
                if conf == "S":
                    sistema.confirmar_reserva(id_r)
                    print(f"¡Reserva confirmada con éxito!")
            except (SoftwareFJError, ValueError) as ex:
                print(f"Operación rechazada con control de excepción: {ex}")

        elif opcion == "5":
            print("\n--- CANCELAR RESERVA ---")
            id_r = input("ID Reserva a cancelar: ").strip()
            mot = input("Motivo de la cancelación: ").strip()
            try:
                sistema.cancelar_reserva(id_r, mot)
                print(f"Reserva cancelada correctamente.")
            except SoftwareFJError as ex:
                print(f"No fue posible cancelar: {ex}")

        elif opcion == "6":
            print("\n--- RESUMEN EN MEMORIA ---")
            est = sistema.obtener_resumen_general()
            for k, v in est.items():
                print(f" • {k.replace('_', ' ').capitalize()}: {v}")

        elif opcion == "7":
            print("\n--- ÚLTIMAS LÍNEAS DE 'software_fj.log' ---")
            if os.path.exists(NOMBRE_ARCHIVO_LOG):
                with open(NOMBRE_ARCHIVO_LOG, "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                    for l in lineas[-15:]:
                        print(l.strip())
            else:
                print("El archivo de log aún no ha sido generado.")

        elif opcion == "0":
            print("\nFinalizando aplicación. Todos los eventos quedaron auditados en el log.")
            break
        else:
            print("Opción no válida. Ingrese un dígito del menú.")


def main():
    """Punto de arranque del sistema."""
    sistema = SistemaGestionSoftwareFJ()
    # Si se invoca con argumento '--simular', ejecuta las simulaciones y termina (útil para pruebas desatendidas)
    if len(sys.argv) > 1 and sys.argv[1] == "--simular":
        ejecutar_bateria_simulaciones(sistema)
    else:
        # Por defecto ejecuta las simulaciones obligatorias y luego ofrece el menú interactivo
        ejecutar_bateria_simulaciones(sistema)
        mostrar_menu_interactivo(sistema)


if __name__ == "__main__":
    main()
