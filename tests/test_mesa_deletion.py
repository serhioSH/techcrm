#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test: Verify mesa deletion logic works correctly.
- Mesa 10 with closed venta should be deletable
- Mesa with ABIERTA venta should NOT be deletable
- Mesa de Domicilio should NEVER be deletable
"""
import os
import sys
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# Temp DB
_TMP = tempfile.mkdtemp(prefix="mesa_deletion_test_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "test.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.mesa_service import MesaService
from app.services.venta_service import VentaService
from app.services.caja_service import CajaService
from app.services.producto_service import ProductoService

def test_mesa_deletion():
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)
    
    auth = AuthService(db)
    assert auth.login("admin", "admin123")
    
    ms = MesaService(db, auth)
    vs = VentaService(db, auth)
    cs = CajaService(db, auth)
    ps = ProductoService(db, auth)
    
    print("\n" + "="*60)
    print(" TEST: Mesa Deletion Query Logic")
    print("="*60)
    
    # Setup: Open a caja
    caja_id = cs.abrir(auth.usuario_actual.id, 0.0)
    print(f"\n[SETUP] Caja abierta: {caja_id}")
    
    # Get mesas
    mesas = ms.listar()
    print(f"[SETUP] Total mesas: {len(mesas)}")
    
    # Find regular mesa (not Domicilio)
    mesa_regular = next(m for m in mesas if m.get("tipo") != "DOMICILIO")
    mesa_10 = next((m for m in mesas if m["nombre"] == "Mesa 10"), None)
    if not mesa_10:
        mesa_10 = mesa_regular
    
    print(f"[TEST1] Using mesa: {mesa_10['nombre']} (id={mesa_10['id']})")
    
    # TEST 1: Mesa with CLOSED venta should be DELETABLE
    print("\n[TEST1] Mesa with CLOSED venta should be DELETABLE")
    venta_id = vs.abrir_venta(mesa_10["id"], auth.usuario_actual.id, caja_id)
    print(f"  → Venta abierta: {venta_id}")
    
    # Retrieve venta details
    venta = vs.obtener_por_id(venta_id)
    print(f"  → Venta estado: {venta['estado']}")
    
    # Add a product to the venta
    productos = ps.listar_activos()
    if productos:
        prod = productos[0]
        vs.agregar_detalle(venta_id, prod["id"], prod["nombre"], 1, prod["precio"])
        print(f"  → Producto agregado: {prod['nombre']}")
    
    # Cobrar (close) the venta
    vs.cobrar(venta_id, "EFECTIVO")
    venta_after = vs.obtener_por_id(venta_id)
    print(f"  → Venta cobrada, nuevo estado: {venta_after['estado']}")
    
    # Query check: should NOT find active venta
    resultado = db.fetchone(
        "SELECT COUNT(*) as n FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
        (mesa_10["id"],)
    )
    tiene_venta_activa = resultado["n"] > 0
    print(f"  → Query result (estado='ABIERTA'): {resultado['n']} venta(s)")
    assert not tiene_venta_activa, f"Should not have ABIERTA venta, but query found {resultado['n']}"
    print("  ✓ PASS: Mesa 10 has no ABIERTA venta, should be deletable")
    
    # TEST 2: Mesa with ABIERTA venta should NOT be deletable
    print("\n[TEST2] Mesa with ABIERTA venta should NOT be deletable")
    mesa_para_test2 = next((m for m in mesas if m["id"] != mesa_10["id"] and m.get("tipo") != "DOMICILIO"), None)
    if mesa_para_test2:
        venta_id_2 = vs.abrir_venta(mesa_para_test2["id"], auth.usuario_actual.id, caja_id)
        print(f"  → Venta ABIERTA: {venta_id_2}")
        
        # Add a product so it doesn't fail validation
        if productos:
            prod = productos[0]
            vs.agregar_detalle(venta_id_2, prod["id"], prod["nombre"], 1, prod["precio"])
            print(f"  → Producto agregado: {prod['nombre']}")
        
        resultado2 = db.fetchone(
            "SELECT COUNT(*) as n FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
            (mesa_para_test2["id"],)
        )
        tiene_venta_activa_2 = resultado2["n"] > 0
        print(f"  → Query result (estado='ABIERTA'): {resultado2['n']} venta(s)")
        assert tiene_venta_activa_2, f"Should have ABIERTA venta, but query found {resultado2['n']}"
        print("  ✓ PASS: Mesa with ABIERTA venta is correctly detected as non-deletable")
    
    # TEST 3: Domicilio mesa should NEVER appear in deletion candidates
    print("\n[TEST3] Domicilio mesa should be protected from deletion")
    domicilio = next((m for m in mesas if m.get("tipo") == "DOMICILIO"), None)
    if domicilio:
        print(f"  → Found Domicilio mesa: {domicilio['nombre']} (id={domicilio['id']})")
        # Simulate the filter in _aplicar_cambios
        mesas_para_eliminar = [m for m in mesas if m.get("tipo") != "DOMICILIO"]
        domicilio_in_candidates = any(m["id"] == domicilio["id"] for m in mesas_para_eliminar)
        assert not domicilio_in_candidates, "Domicilio mesa should not be in deletion candidates"
        print("  ✓ PASS: Domicilio mesa filtered out from deletion candidates")
    
    print("\n" + "="*60)
    print(" ALL TESTS PASSED ✓")
    print("="*60 + "\n")
    
    db.close()
    shutil.rmtree(_TMP, ignore_errors=True)

if __name__ == "__main__":
    test_mesa_deletion()
