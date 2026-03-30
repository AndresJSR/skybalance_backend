from services.tree_service import TreeService


def main():
    service = TreeService()

    # -----------------------------
    # Probar carga desde JSON
    # -----------------------------
    with open("ModoInserción.json", "rb") as file:
        raw_bytes = file.read()

    result = service.load_json(raw_bytes, critical_depth=2)

    print("=== CARGA JSON ===")
    print(result["mode"])
    print(result["avl"])
    print(result["bst"])

    # -----------------------------
    # Probar búsqueda
    # -----------------------------
    print("\n=== BÚSQUEDA ===")
    print(service.search_flight("SB400"))

    # -----------------------------
    # Probar inserción
    # -----------------------------
    print("\n=== INSERCIÓN ===")
    new_flight = {
        "codigo": "SB999",
        "origen": "Manizales",
        "destino": "Bogota",
        "horaSalida": "18:00",
        "precioBase": 550,
        "pasajeros": 60,
        "prioridad": 2,
        "promocion": False,
        "alerta": False
    }

    insert_result = service.insert_flight(new_flight)
    print(insert_result["properties"])

    # -----------------------------
    # Probar eliminación
    # -----------------------------
    print("\n=== ELIMINACIÓN ===")
    delete_result = service.delete_flight("SB999")
    print(delete_result["properties"])

    # -----------------------------
    # Probar cola
    # -----------------------------
    print("\n=== COLA ===")
    service.enqueue_flight({
        "codigo": "SB888",
        "origen": "Cali",
        "destino": "Medellin",
        "horaSalida": "19:00",
        "precioBase": 300,
        "pasajeros": 50,
        "prioridad": 1,
        "promocion": False,
        "alerta": False
    })
    print(service.list_queue())
    print(service.process_next_in_queue())

    # -----------------------------
    # Probar undo
    # -----------------------------
    print("\n=== UNDO ===")
    print(service.undo())

    # -----------------------------
    # Probar exportación
    # -----------------------------
    print("\n=== EXPORT JSON ===")
    json_text = service.export_json_text()
    print(json_text[:500])  # imprime solo un fragmento

    # -----------------------------
    # Probar métricas
    # -----------------------------
    print("\n=== MÉTRICAS ===")
    print(service.get_metrics())


if __name__ == "__main__":
    main()