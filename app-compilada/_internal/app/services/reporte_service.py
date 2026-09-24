# ============================================================
#  app/services/reporte_service.py
#  Generacion de reportes por periodo, productos, cajeros y mesas
#  Punto 8: Reportes y exportacion a Excel
# ============================================================
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class ReporteService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    # ---- Periodos ----
    def obtener_rango_periodo(self, periodo: str) -> Tuple[str, str]:
        """Retorna (desde, hasta) en formato YYYY-MM-DD segun el periodo."""
        hoy = datetime.now().date()
        if periodo == "hoy":
            return str(hoy), str(hoy)
        elif periodo == "ayer":
            ayer = hoy - timedelta(days=1)
            return str(ayer), str(ayer)
        elif periodo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            return str(inicio_semana), str(hoy)
        elif periodo == "mes":
            return str(hoy.replace(day=1)), str(hoy)
        else:
            # personalizado: se espera que sea "personalizado|YYYY-MM-DD|YYYY-MM-DD"
            return None, None

    # ---- Resumen general ----
    def resumen_ventas(self, desde: str, hasta: str) -> Dict:
        """
        Retorna diccionario con:
        - cantidad_ventas: total de transacciones
        - total_vendido: suma general
        - total_efectivo: efectivo_pago de todas las ventas
        - total_transferencia: transferencia_pago de todas las ventas
        
        Maneja correctamente pagos mixtos usando las columnas efectivo_pago y transferencia_pago.
        """
        self._requerir(Permisos.CONSULTAR_REPORTES)
        
        # Intentar usar las nuevas columnas (BD v8+)
        try:
            sql = """
                SELECT 
                    COUNT(*) AS cantidad_ventas,
                    COALESCE(SUM(total), 0) AS total_vendido,
                    COALESCE(SUM(efectivo_pago), 0) AS total_efectivo,
                    COALESCE(SUM(transferencia_pago), 0) AS total_transferencia
                FROM ventas
                WHERE estado='CERRADA'
                  AND date(fecha_hora) >= ?
                  AND date(fecha_hora) <= ?
            """
            row = self._db.fetchone(sql, (desde, hasta))
        except Exception:
            # Fallback para BD vieja sin efectivo_pago/transferencia_pago
            sql = """
                SELECT 
                    COUNT(*) AS cantidad_ventas,
                    COALESCE(SUM(total), 0) AS total_vendido,
                    COALESCE(SUM(CASE WHEN metodo_pago='EFECTIVO' THEN total ELSE 0 END), 0) AS total_efectivo,
                    COALESCE(SUM(CASE WHEN metodo_pago='TRANSFERENCIA' THEN total ELSE 0 END), 0) AS total_transferencia
                FROM ventas
                WHERE estado='CERRADA'
                  AND date(fecha_hora) >= ?
                  AND date(fecha_hora) <= ?
            """
            row = self._db.fetchone(sql, (desde, hasta))
        
        return {
            "cantidad_ventas": row["cantidad_ventas"] or 0,
            "total_vendido": round(row["total_vendido"] or 0, 2),
            "total_efectivo": round(row["total_efectivo"] or 0, 2),
            "total_transferencia": round(row["total_transferencia"] or 0, 2),
        }

    # ---- Productos vendidos ----
    def productos_vendidos(self, desde: str, hasta: str, limite: int = 100) -> List[Dict]:
        """
        Retorna lista de productos vendidos con:
        - nombre_producto
        - cantidad_total
        - total_vendido
        Ordenado por cantidad descendente.
        OPTIMIZADO: LIMIT para no cargar miles de filas innecesariamente.
        """
        self._requerir(Permisos.CONSULTAR_REPORTES)
        
        sql = """
            SELECT 
                dv.nombre_producto,
                SUM(dv.cantidad) AS cantidad_total,
                SUM(dv.subtotal) AS total_vendido
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            WHERE v.estado='CERRADA'
              AND date(v.fecha_hora) >= ?
              AND date(v.fecha_hora) <= ?
            GROUP BY dv.nombre_producto
            ORDER BY cantidad_total DESC
            LIMIT ?
        """
        rows = self._db.fetchall(sql, (desde, hasta, limite))
        return [
            {
                "nombre_producto": row["nombre_producto"],
                "cantidad_total": row["cantidad_total"],
                "total_vendido": round(row["total_vendido"], 2),
            }
            for row in rows
        ]

    # ---- Por cajero ----
    def ventas_por_cajero(self, desde: str, hasta: str, limite: int = 100) -> List[Dict]:
        """
        Retorna lista de cajeros con:
        - usuario_nombre
        - cantidad_ventas
        - total_vendido
        - total_efectivo
        - total_transferencia
        OPTIMIZADO: LIMIT para reportes grandes.
        """
        self._requerir(Permisos.CONSULTAR_REPORTES)
        
        sql = """
            SELECT 
                u.nombre AS usuario_nombre,
                COUNT(*) AS cantidad_ventas,
                SUM(v.total) AS total_vendido,
                SUM(CASE WHEN v.metodo_pago='EFECTIVO' THEN v.total ELSE 0 END) AS total_efectivo,
                SUM(CASE WHEN v.metodo_pago='TRANSFERENCIA' THEN v.total ELSE 0 END) AS total_transferencia
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.estado='CERRADA'
              AND date(v.fecha_hora) >= ?
              AND date(v.fecha_hora) <= ?
            GROUP BY u.id, u.nombre
            ORDER BY total_vendido DESC
            LIMIT ?
        """
        rows = self._db.fetchall(sql, (desde, hasta, limite))
        return [
            {
                "usuario_nombre": row["usuario_nombre"],
                "cantidad_ventas": row["cantidad_ventas"],
                "total_vendido": round(row["total_vendido"], 2),
                "total_efectivo": round(row["total_efectivo"], 2),
                "total_transferencia": round(row["total_transferencia"], 2),
            }
            for row in rows
        ]

    # ---- Por mesa ----
    def ventas_por_mesa(self, desde: str, hasta: str, limite: int = 100) -> List[Dict]:
        """
        Retorna lista de mesas con:
        - mesa_nombre
        - cantidad_ventas
        - total_vendido
        OPTIMIZADO: LIMIT para reportes grandes.
        """
        self._requerir(Permisos.CONSULTAR_REPORTES)
        
        sql = """
            SELECT 
                m.nombre AS mesa_nombre,
                COUNT(*) AS cantidad_ventas,
                SUM(v.total) AS total_vendido
            FROM ventas v
            JOIN mesas m ON v.mesa_id = m.id
            WHERE v.estado='CERRADA'
              AND date(v.fecha_hora) >= ?
              AND date(v.fecha_hora) <= ?
            GROUP BY m.id, m.nombre
            ORDER BY total_vendido DESC
            LIMIT ?
        """
        rows = self._db.fetchall(sql, (desde, hasta, limite))
        return [
            {
                "mesa_nombre": row["mesa_nombre"],
                "cantidad_ventas": row["cantidad_ventas"],
                "total_vendido": round(row["total_vendido"], 2),
            }
            for row in rows
        ]

    # ---- Exportacion a Excel ----
    def exportar_excel(self, desde: str, hasta: str, ruta_destino: str) -> Tuple[bool, str]:
        """
        Genera un archivo Excel con los reportes.
        Retorna (exito, mensaje).
        """
        self._requerir(Permisos.EXPORTAR_EXCEL)
        
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            return False, "openpyxl no esta instalado. Instale: pip install openpyxl"

        try:
            wb = Workbook()
            wb.remove(wb.active)  # eliminar hoja por defecto

            # Hoja 1: Resumen
            self._crear_hoja_resumen(wb, desde, hasta)

            # Hoja 2: Productos
            self._crear_hoja_productos(wb, desde, hasta)

            # Hoja 3: Cajeros
            self._crear_hoja_cajeros(wb, desde, hasta)

            # Hoja 4: Mesas
            self._crear_hoja_mesas(wb, desde, hasta)

            # Hoja 5: Detalle de ventas
            self._crear_hoja_detalle_ventas(wb, desde, hasta)

            wb.save(ruta_destino)
            return True, f"Reporte guardado en: {ruta_destino}"
        except Exception as e:
            return False, f"Error al generar Excel: {e}"

    def _crear_hoja_resumen(self, wb, desde: str, hasta: str):
        """Crea la hoja de resumen general."""
        from openpyxl.styles import Font, PatternFill
        
        ws = wb.create_sheet("Resumen", 0)
        
        # Estilos
        titulo_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        titulo_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        header_font = Font(bold=True, size=11)
        
        # Encabezado
        ws["A1"] = "REPORTE DE VENTAS"
        ws["A1"].font = titulo_font
        ws["A1"].fill = titulo_fill
        ws.merge_cells("A1:D1")
        
        ws["A2"] = f"Período: {desde} al {hasta}"
        ws.merge_cells("A2:D2")
        
        # Resumen
        resumen = self.resumen_ventas(desde, hasta)
        
        row = 4
        datos_resumen = [
            ("Cantidad de ventas", resumen["cantidad_ventas"]),
            ("Total vendido", f"${resumen['total_vendido']:,.2f}"),
            ("Total en efectivo", f"${resumen['total_efectivo']:,.2f}"),
            ("Total por transferencia", f"${resumen['total_transferencia']:,.2f}"),
        ]
        
        for label, valor in datos_resumen:
            ws[f"A{row}"] = label
            ws[f"A{row}"].font = header_font
            ws[f"A{row}"].fill = header_fill
            ws[f"B{row}"] = valor
            ws.column_dimensions["A"].width = 30
            ws.column_dimensions["B"].width = 20
            row += 1

    def _crear_hoja_productos(self, wb, desde: str, hasta: str):
        """Crea la hoja de productos vendidos."""
        from openpyxl.styles import Font, PatternFill
        
        ws = wb.create_sheet("Productos", 1)
        
        titulo_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        titulo_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        header_font = Font(bold=True, size=11)
        
        # Encabezado
        ws["A1"] = "PRODUCTOS VENDIDOS"
        ws["A1"].font = titulo_font
        ws["A1"].fill = titulo_fill
        ws.merge_cells("A1:C1")
        
        ws["A2"] = f"Período: {desde} al {hasta}"
        ws.merge_cells("A2:C2")
        
        # Encabezados de tabla
        headers = ["Producto", "Cantidad", "Total Vendido"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Datos
        productos = self.productos_vendidos(desde, hasta)
        for row, prod in enumerate(productos, 5):
            ws[f"A{row}"] = prod["nombre_producto"]
            ws[f"B{row}"] = prod["cantidad_total"]
            ws[f"C{row}"] = prod["total_vendido"]
            ws[f"C{row}"].number_format = "$#,##0.00"
        
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 18

    def _crear_hoja_cajeros(self, wb, desde: str, hasta: str):
        """Crea la hoja de ventas por cajero."""
        from openpyxl.styles import Font, PatternFill
        
        ws = wb.create_sheet("Cajeros", 2)
        
        titulo_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        titulo_font = Font(bold=True, color="000000", size=12)
        header_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        header_font = Font(bold=True, size=11)
        
        # Encabezado
        ws["A1"] = "VENTAS POR CAJERO"
        ws["A1"].font = titulo_font
        ws["A1"].fill = titulo_fill
        ws.merge_cells("A1:E1")
        
        ws["A2"] = f"Período: {desde} al {hasta}"
        ws.merge_cells("A2:E2")
        
        # Encabezados de tabla
        headers = ["Cajero", "Cantidad Ventas", "Total Vendido", "Total Efectivo", "Total Transferencia"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Datos
        cajeros = self.ventas_por_cajero(desde, hasta)
        for row, cajero in enumerate(cajeros, 5):
            ws[f"A{row}"] = cajero["usuario_nombre"]
            ws[f"B{row}"] = cajero["cantidad_ventas"]
            ws[f"C{row}"] = cajero["total_vendido"]
            ws[f"D{row}"] = cajero["total_efectivo"]
            ws[f"E{row}"] = cajero["total_transferencia"]
            for col in ["C", "D", "E"]:
                ws[f"{col}{row}"].number_format = "$#,##0.00"
        
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 18
        ws.column_dimensions["E"].width = 22

    def _crear_hoja_mesas(self, wb, desde: str, hasta: str):
        """Crea la hoja de ventas por mesa."""
        from openpyxl.styles import Font, PatternFill
        
        ws = wb.create_sheet("Mesas", 3)
        
        titulo_fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
        titulo_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="DEEAF6", end_color="DEEAF6", fill_type="solid")
        header_font = Font(bold=True, size=11)
        
        # Encabezado
        ws["A1"] = "VENTAS POR MESA"
        ws["A1"].font = titulo_font
        ws["A1"].fill = titulo_fill
        ws.merge_cells("A1:C1")
        
        ws["A2"] = f"Período: {desde} al {hasta}"
        ws.merge_cells("A2:C2")
        
        # Encabezados de tabla
        headers = ["Mesa", "Cantidad Ventas", "Total Vendido"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Datos
        mesas = self.ventas_por_mesa(desde, hasta)
        for row, mesa in enumerate(mesas, 5):
            ws[f"A{row}"] = mesa["mesa_nombre"]
            ws[f"B{row}"] = mesa["cantidad_ventas"]
            ws[f"C{row}"] = mesa["total_vendido"]
            ws[f"C{row}"].number_format = "$#,##0.00"
        
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 18

    def _crear_hoja_detalle_ventas(self, wb, desde: str, hasta: str, limite_filas: int = 5000):
        """
        Crea la hoja con el detalle de las ventas.
        OPTIMIZADO: LIMIT para evitar cargar millones de filas en memoria.
        """
        from openpyxl.styles import Font, PatternFill
        
        ws = wb.create_sheet("Detalle Ventas", 4)
        
        titulo_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        titulo_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        header_font = Font(bold=True, size=10)
        
        # Encabezado
        ws["A1"] = "DETALLE DE VENTAS"
        ws["A1"].font = titulo_font
        ws["A1"].fill = titulo_fill
        ws.merge_cells("A1:H1")
        
        ws["A2"] = f"Período: {desde} al {hasta}"
        ws.merge_cells("A2:H2")
        
        # Encabezados de tabla
        headers = ["Comprobante", "Fecha/Hora", "Mesa", "Cajero", "Producto", "Cantidad", "Precio Unitario", "Subtotal"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Datos: usar LIMIT para no cargar todo en memoria
        sql = """
            SELECT 
                v.consecutivo,
                v.fecha_hora,
                m.nombre AS mesa_nombre,
                u.nombre AS usuario_nombre,
                dv.nombre_producto,
                dv.cantidad,
                dv.precio_unitario,
                dv.subtotal
            FROM detalle_ventas dv
            JOIN ventas v ON dv.venta_id = v.id
            LEFT JOIN mesas m ON v.mesa_id = m.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.estado='CERRADA'
              AND date(v.fecha_hora) >= ?
              AND date(v.fecha_hora) <= ?
            ORDER BY v.fecha_hora DESC
            LIMIT ?
        """
        rows = self._db.fetchall(sql, (desde, hasta, limite_filas))
        
        for row_idx, row in enumerate(rows, 5):
            ws[f"A{row_idx}"] = row["consecutivo"]
            ws[f"B{row_idx}"] = row["fecha_hora"]
            ws[f"C{row_idx}"] = row["mesa_nombre"]
            ws[f"D{row_idx}"] = row["usuario_nombre"]
            ws[f"E{row_idx}"] = row["nombre_producto"]
            ws[f"F{row_idx}"] = row["cantidad"]
            ws[f"G{row_idx}"] = row["precio_unitario"]
            ws[f"H{row_idx}"] = row["subtotal"]
            
            ws[f"G{row_idx}"].number_format = "$#,##0.00"
            ws[f"H{row_idx}"].number_format = "$#,##0.00"
        
        ws.column_dimensions["A"].width = 14
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 25
        ws.column_dimensions["F"].width = 10
        ws.column_dimensions["G"].width = 16
        ws.column_dimensions["H"].width = 16
        
        # Si se alcanzó el límite, mostrar advertencia
        if len(rows) == limite_filas:
            ws["A4"] = ws["A4"].value + f" (primeras {limite_filas} filas)"
