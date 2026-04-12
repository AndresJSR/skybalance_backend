# SkyBalance – Partición de Contenido: Videos Entregables

**Proyecto:** SkyBalance Backend + Frontend  
**Equipo:** Juan Jose · Andrés · Juan Felipe  
**Fecha:** Abril 2026

---

## ENTREGABLE 1 — Video explicativo de solución y arquitectura (segundo idioma)

> Todos en primer plano durante su sección. Duración sugerida: 9 minutos (3 min/persona). Idioma: inglés.

---

### Juan Jose — Núcleo AVL y Balanceo (0:00 – 3:00)

**Tema:** Core algorítmico del sistema.

**Qué cubrir:**
- Por qué AVL en lugar de un árbol no balanceado para este problema
- Estructura del nodo: valor (vuelo), padre, hijo izquierdo, hijo derecho
- Propiedad BST + invariante de balance AVL (factor ≤ 1)
- Inserciones y rebalanceo automático tras cada inserción
- Rotaciones LL, RR, LR y RL (cuándo aplica cada una)
- Eliminaciones: nodo hoja, un hijo y dos hijos (reemplazo por predecesor)
- Métricas expuestas: altura, hojas, nodos, factor de equilibrio, rotaciones acumuladas

**Frase de cierre (en inglés):**
> "Now that we covered the balancing core, Andrés will explain the persistence layer and system orchestration."

---

### Andrés — Persistencia, UNDO, Versiones y Cola de Concurrencia (3:00 – 6:00)

**Tema:** Arquitectura de soporte y robustez operativa.

**Qué cubrir:**
- Persistencia JSON: carga de archivos (modo Inserción y modo Topología) y serialización del árbol
- BST paralelo: propósito y cómo se mantiene sincronizado con el AVL
- Pila UNDO: cómo se guarda el estado anterior y se restaura
- Sistema de versiones: guardar, listar y restaurar snapshots con nombre
- Cola de concurrencia: procesamiento seguro de inserciones en paralelo
- Estructura de endpoints FastAPI y organización por módulos (blueprints)

**Frase de cierre (en inglés):**
> "With backend services and data integrity in place, Juan Felipe will show the user layer and front-end integration."

---

### Juan Felipe — Frontend React e Integración Full-Stack (6:00 – 9:00)

**Tema:** Experiencia de usuario e integración completa.

**Qué cubrir:**
- Arquitectura del frontend React y manejo de estados
- Visualización del árbol y operaciones desde la interfaz
- Consumo de endpoints CRUD, métricas, UNDO y versiones
- Validaciones y feedback visual al usuario
- Flujo completo: usuario → API → persistencia → actualización en UI

**Cierre final del video:**
> Resumen de arquitectura end-to-end y cómo cada capa contribuye al sistema completo.

---

### Guion base en inglés (por persona)

**Juan Jose:**
> "I developed the full AVL backend core. I implemented node insertion with self-balancing rotations — LL, RR, LR and RL — safe deletions for all three structural cases, and a complete set of tree metrics exposed through the API. This guarantees logarithmic performance at all times."

**Andrés:**
> "I implemented the reliability layer: JSON persistence with two loading modes, a BST for academic comparison, the undo stack, a named version system, and concurrent queue processing. I also designed the FastAPI endpoints to expose all operations in a clean, testable structure."

**Juan Felipe:**
> "I built the React frontend and integrated it with all backend endpoints. The interface allows users to execute operations and immediately see updated tree states and metrics, completing the end-to-end architecture from user interaction to balanced data structures."

---

## ENTREGABLE 2 — Videotutorial del sistema (código e interfaz en primer plano)

> Primer plano principal: código e interfaz. Duración sugerida: 12 minutos (4 min/persona). Idioma libre.

---

### Juan Jose — Demo técnica del backend AVL (0:00 – 4:00)

1. Insertar vuelos con códigos que provoquen rotaciones (mostrar caso LL y caso LR)
2. Mostrar eliminación en los 3 casos (hoja, un hijo, dos hijos)
3. Consultar `GET /api/metrics` y señalar cómo cambian los contadores de rotaciones
4. Explicar brevemente complejidad O(log n) y cómo el balance la garantiza
5. Mostrar modo estrés: activar `POST /api/trees/stress`, auditar con `GET /api/trees/audit`, rebalancear con `POST /api/trees/rebalance`

---

### Andrés — Demo técnica de persistencia y servicios (4:00 – 8:00)

1. Cargar un JSON inicial (modo Inserción y modo Topología)
2. Ejecutar operación, luego usar UNDO y mostrar que el árbol se revierte
3. Guardar una versión nombrada y restaurarla
4. Encolar vuelos y procesar la cola (simple y concurrente)
5. Mostrar respuesta JSON de los endpoints FastAPI relevantes

---

### Juan Felipe — Demo funcional desde la interfaz (8:00 – 12:00)

1. Flujo completo desde UI: crear, editar, eliminar y consultar un vuelo
2. Visualización del árbol y métricas actualizándose en pantalla
3. Acción de UNDO y restauración de versión desde el frontend
4. Confirmar sincronización con el backend en tiempo real

---

## Checklist de grabación

| Ítem | Entregable 1 | Entregable 2 |
|---|---|---|
| Todos en primer plano (sección propia) | ✅ Obligatorio | Opcional (recuadro) |
| Audio limpio, fondo estable | ✅ | ✅ |
| Código/interfaz visible | Puede ser pantalla compartida | ✅ Obligatorio |
| Cada persona habla su bloque completo | ✅ | ✅ |
| Segundo idioma (inglés) | ✅ Obligatorio | No requerido |

---

*Documento generado para coordinación interna del equipo SkyBalance.*
