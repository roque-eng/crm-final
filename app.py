# ... (Configuración inicial y funciones de base de datos se mantienen igual)

# ---------------- PESTAÑA 3: RENOVACIONES (CON CASOS PENDIENTES) ----------------
with tab3:
    st.header("🔄 Centro de Renovaciones")
    
    # Filtros independientes para el equipo
    df_ren_raw = leer_datos('SELECT s.id, s.cliente_id, c.nombre_completo as "Cliente", s.aseguradora, s.ramo, s.detalle_riesgo as "Riesgo", s.ejecutivo, s.corredor, s.agente, s.vigencia_hasta as "Vence_Viejo", s."premio_UYU", s."premio_USD" FROM seguros s JOIN clientes c ON s.cliente_id = c.id')
    
    if not df_ren_raw.empty:
        col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
        with col_r1:
            ejecutivos_ren = sorted([str(x) for x in df_ren_raw['ejecutivo'].unique() if x])
            sel_eje_ren = st.selectbox("👤 Filtrar por Ejecutivo", ["Todos"] + ejecutivos_ren, key="ren_eje_v2")
        with col_r2:
            aseg_ren = sorted([str(x) for x in df_ren_raw['aseguradora'].unique() if x])
            sel_aseg_ren = st.selectbox("🏢 Filtrar por Aseguradora", ["Todos"] + aseg_ren, key="ren_aseg_v2")
        with col_r3:
            dias_v = st.slider("📅 Ventana de tiempo (días):", 15, 180, 60)

        # LÓGICA AMPLIADA: Muestra desde hace 90 días (pendientes) hasta 'dias_v' en el futuro
        today_date = date.today()
        df_ren_raw['Vence_Viejo_dt'] = pd.to_datetime(df_ren_raw['Vence_Viejo']).dt.date
        
        # Filtro de fecha: Pasados (90 días) y Futuros (dias_v)
        mask = (df_ren_raw['Vence_Viejo_dt'] >= today_date - timedelta(days=90)) & \
               (df_ren_raw['Vence_Viejo_dt'] <= today_date + timedelta(days=dias_v))
        
        if sel_eje_ren != "Todos": mask = mask & (df_ren_raw['ejecutivo'] == sel_eje_ren)
        if sel_aseg_ren != "Todos": mask = mask & (df_ren_raw['aseguradora'] == sel_aseg_ren)
        
        df_ren_f = df_ren_raw[mask].copy().sort_values("Vence_Viejo_dt")
        
        if not df_ren_f.empty:
            st.write(f"Mostrando {len(df_ren_f)} pólizas vencidas o por vencer:")
            df_ren_edit = st.data_editor(df_ren_f, use_container_width=True, hide_index=True,
                column_order=["Cliente", "aseguradora", "ramo", "Riesgo", "Vence_Viejo", "premio_UYU", "premio_USD"],
                column_config={"Vence_Viejo": st.column_config.DateColumn("Nueva Fecha de Vigencia")}, 
                disabled=["Cliente"])
            
            if st.button("🚀 Confirmar y Renovar Seleccionados"):
                for idx, row in df_ren_edit.iterrows():
                    # Al renovar, insertamos el nuevo registro con la nueva fecha
                    ejecutar_query('INSERT INTO seguros (cliente_id, aseguradora, ramo, detalle_riesgo, vigencia_hasta, "premio_UYU", "premio_USD", ejecutivo, corredor, agente) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (row['cliente_id'], row['aseguradora'], row['ramo'], row['Riesgo'], row['Vence_Viejo'], row['premio_UYU'], row['premio_USD'], row['ejecutivo'], row['corredor'], row['agente']))
                st.success("✅ Renovaciones procesadas correctamente.")
                st.rerun()
        else:
            st.info("No hay pólizas pendientes o próximas a vencer con estos filtros.")