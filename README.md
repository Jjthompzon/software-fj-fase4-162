# Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas

**Universidad Nacional Abierta y a Distancia (UNAD)**  
**Escuela de Ciencias Básicas, Tecnología e Ingeniería (ECBTI)**  
**Curso:** Programación (Código: 213023)  
**Fase 4:** Componente práctico - Prácticas simuladas (Ejercicio 1)  
**Grupo:** 162  
**Estudiante:** Astrid Natalia Pineda Alvarez (C.C. 1036630806)  
**Tutor:** Johnny Alirio Blanquicett Cardona  
**Año:** 2026  

---

## 1. Descripción del Proyecto

**Software FJ** es una solución informática desarrollada en Python bajo el paradigma de **Programación Orientada a Objetos (POO)** y arquitectura en capas en memoria, diseñada para gestionar de manera integral el catálogo de servicios corporativos, el registro validado de clientes y el ciclo de vida de reservaciones comerciales.

El sistema da estricto cumplimiento a los lineamientos de la **Fase 4**, incorporando una arquitectura robusta de control de excepciones personalizadas, encadenamiento semántico (`raise ... from ...`), bloques canónicos de control `try/except/else/finally`, persistencia transaccional de eventos en disco mediante el módulo `logging` (`software_fj.log`) y una batería automatizada de 10+ simulaciones de validación defensiva.

---

## 2. Características y Arquitectura Técnica

- **Paradigma POO Avanzado:**
  - **Encapsulamiento estricto:** Atributos protegidos y privados gestionados mediante decoradores `@property` y `@setter` con validaciones de tipo, longitud y formato.
  - **Herencia y Polimorfismo:** Clase base abstracta `Servicio` (usando `abc.ABC` y `@abstractmethod`) con especializaciones concretas:
    - `ReservaSala`: Gestión de aforo físico máximo, videollamadas y sobrecarga de cálculo de tarifas con descuentos porcentuales e IVA (19%).
    - `AlquilerEquipo`: Control de inventario físico, disponibilidad de stock operativo, verificación de condición física y depósito de garantía.
    - `AsesoriaEspecializada`: Tarificación profesional diferenciada según nivel del consultor (Junior, Senior, Master) y recargos por urgencia operativa.
  - **Ciclo de Vida de Reservaciones:** Máquina de estados finitos (`PENDIENTE` $\rightarrow$ `CONFIRMADA` $\rightarrow$ `COMPLETADA` / `CANCELADA`) con verificación de precondiciones y transiciones seguras.

- **Jerarquía Canónica de Excepciones:**
  ```text
  Exception
     └── SoftwareFJError (Clase base del dominio)
           ├── ValidacionDatosError
           │     ├── CedulaInvalidaError
           │     ├── CorreoInvalidoError
           │     └── TarifaInvalidaError
           ├── ServicioNoDisponibleError
           │     ├── AforoExcedidoError
           │     └── StockAgotadoError
           ├── EstadoInvalidoReservaError
           └── CalculoTarifaError
  ```

- **Manejo Estructurado de Excepciones:**
  - Uso estricto de `try / except / else / finally` en puntos críticos de creación, transición y persistencia.
  - Encadenamiento contextual explícito (`from`) para preservar la causa raíz del error sin perder la trazabilidad de depuración.

- **Auditoría y Trazabilidad (Logging):**
  - Implementación con `logging.FileHandler` y `logging.StreamHandler`.
  - Registro sincronizado en tiempo de ejecución en consola y en el archivo de texto plano `software_fj.log` con marca temporal ISO, nivel de severidad (`INFO`, `WARNING`, `ERROR`, `CRITICAL`) e identificadores de transacción.

---

## 3. Estructura de Archivos del Repositorio

```text
├── Fase_4_162.py          # Código fuente principal en Python (POO + Excepciones + Menú + Simulaciones)
├── software_fj.log        # Registro cronológico y estructurado de eventos y excepciones auditadas
└── README.md              # Documentación técnica y académica del proyecto
```

---

## 4. Requisitos y Ejecución

### Prerrequisitos
- Python 3.10 o superior (no requiere librerías externas de terceros; emplea exclusivamente la biblioteca estándar de Python: `abc`, `re`, `enum`, `logging`, `datetime`, `typing`, `sys`, `os`).

### Modo de Simulación Automatizada (Revisión de Rúbrica)
Para ejecutar directamente la batería oficial de 11 simulaciones controladas (escenarios válidos e inválidos con captura de excepciones):
```bash
python Fase_4_162.py --simular
```

### Modo Interactivo de Consola
Para interactuar con el sistema a través del menú de usuario:
```bash
python Fase_4_162.py
```

---

## 5. Batería de Pruebas Simuladas Ejecutadas

| # | Escenario Operativo | Tipo de Caso | Excepción Controlada / Resultado |
|---|---------------------|--------------|-----------------------------------|
| 1 | Registro de clientes con datos y correos válidos | Válido | Clientes almacenados satisfactoriamente |
| 2 | Cédula alfanumérica o errónea | Inválido | `CedulaInvalidaError` [ERR-CLI-002] |
| 3 | Sintaxis de correo electrónico inválida | Inválido | `CorreoInvalidoError` [ERR-CLI-002] |
| 4 | Incorporación de 3 servicios al catálogo | Válido | Servicios SAL-01, EQP-01, ASE-01 creados |
| 5 | Asignación de tarifa horaria negativa | Inválido | `TarifaInvalidaError` [ERR-SRV-003] |
| 6 | Reserva de sala con descuento e IVA | Válido | Reserva RSV-1001 confirmada ($299,880.00) |
| 7 | Control de aforo máximo en sala (25 vs 12) | Inválido | `AforoExcedidoError` [ERR-CAP-006] |
| 8 | Alquiler con equipo fuera de servicio/stock | Inválido | `StockAgotadoError` [ERR-SRV-004] |
| 9 | Transición ilegal sobre reserva ya cancelada | Inválido | `EstadoInvalidoReservaError` [ERR-STA-007] |
| 10 | Encadenamiento de excepciones con `from` | Inválido | `CalculoTarifaError` encadenado desde `ValueError` |
| 11 | Asesoría especializada con urgencia (30%) e IVA | Válido | Reserva RSV-1005 confirmada ($696,150.00) |
