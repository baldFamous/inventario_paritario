'use client';
import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import { Producto, Solicitud, Lote, PaginatedResponse } from '@/types';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ productos: 0, lotesActivos: 0, pendientes: 0, criticos: 0 });
  const [solicitudesRecientes, setSolicitudesRecientes] = useState<Solicitud[]>([]);
  const [selected, setSelected] = useState<Solicitud | null>(null);
  const [viewingDetalle, setViewingDetalle] = useState<Solicitud | null>(null);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [asignaciones, setAsignaciones] = useState<Record<number, { lote_id: string; cantidad: string }>>({});

  const load = () => {
    apiFetch<PaginatedResponse<Producto>>('/productos/?page_size=100').then(r => {
      const criticos = r.results.filter(p => p.stock_disponible <= p.stock_minimo).length;
      setStats(s => ({ ...s, productos: r.count, criticos }));
    });
    if (user?.rol === 'GESTOR') {
      apiFetch<PaginatedResponse<Lote>>('/lotes/?estado=ACTIVO&page_size=1').then(r =>
        setStats(s => ({ ...s, lotesActivos: r.count })));
    }
    apiFetch<PaginatedResponse<Solicitud>>('/solicitudes/?page_size=5').then(r => {
      setSolicitudesRecientes(r.results);
      const pendientes = r.results.filter(s => s.estado === 'PENDIENTE').length;
      setStats(s => ({ ...s, pendientes }));
    });
  };

  useEffect(() => {
    if (!user) return;
    load();
  }, [user]);

  const openAprobar = async (sol: Solicitud) => {
    setSelected(sol);
    const r = await apiFetch<PaginatedResponse<Lote>>('/lotes/?estado=ACTIVO&page_size=200');
    setLotes(r.results);
    const init: Record<number, { lote_id: string; cantidad: string }> = {};
    sol.detalles.forEach(d => { init[d.id] = { lote_id: '', cantidad: String(d.cantidad_solicitada) }; });
    setAsignaciones(init);
  };

  const handleAprobar = async () => {
    const data = Object.entries(asignaciones).map(([did, v]) => ({
      detalle_id: parseInt(did), lote_id: parseInt(v.lote_id), cantidad_aprobada: parseInt(v.cantidad),
    }));
    await apiFetch(`/solicitudes/${selected!.id}/aprobar/`, { method: 'POST', body: JSON.stringify({ asignaciones: data }) });
    setSelected(null);
    load();
  };

  return (
    <AppShell title="Dashboard">
      <div className="stats-grid">
        <div className="stat-card accent">
          <div className="stat-label">Productos</div>
          <div className="stat-value">{stats.productos}</div>
          <div className="stat-sub">En catálogo</div>
        </div>
        {user?.rol === 'GESTOR' && (
          <div className="stat-card info">
            <div className="stat-label">Lotes Activos</div>
            <div className="stat-value">{stats.lotesActivos}</div>
            <div className="stat-sub">Con stock disponible</div>
          </div>
        )}
        <div className="stat-card warning">
          <div className="stat-label">Solicitudes Pendientes</div>
          <div className="stat-value">{stats.pendientes}</div>
          <div className="stat-sub">Por gestionar</div>
        </div>
        <div className="stat-card error">
          <div className="stat-label">Stock Crítico</div>
          <div className="stat-value">{stats.criticos}</div>
          <div className="stat-sub">Bajo mínimo</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Solicitudes Recientes</h3>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>ID</th><th>Fecha</th><th>Solicitante</th><th>Estado</th><th>Acción</th></tr>
            </thead>
            <tbody>
              {solicitudesRecientes.length === 0 ? (
                <tr><td colSpan={5} className="table-empty">Sin solicitudes</td></tr>
              ) : solicitudesRecientes.map(s => (
                <tr key={s.id}>
                  <td>#{s.id}</td>
                  <td>{new Date(s.created_at).toLocaleDateString('es-CL')}</td>
                  <td>{s.solicitante_nombre}</td>
                  <td><span className={`badge badge-${s.estado.toLowerCase()}`}>{s.estado_display}</span></td>
                  <td>
                    {s.estado === 'PENDIENTE' && (
                      <button className="btn btn-sm btn-primary" onClick={() => openAprobar(s)}>Aprobar</button>
                    )}
                    {s.estado !== 'PENDIENTE' && (
                      <button className="btn btn-sm btn-secondary" onClick={() => setViewingDetalle(s)}>Ver Detalles</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h3>Aprobar Solicitud #{selected.id}</h3><button className="modal-close" onClick={() => setSelected(null)}>×</button></div>
            <div className="modal-body">
              <p className="text-muted mb-4">Asigne un lote y cantidad para cada producto:</p>
              {selected.detalles.map(d => (
                <div key={d.id} style={{ marginBottom: 16, padding: 12, background: '#FAFAFA', borderRadius: 6 }}>
                  <strong>{d.producto_nombre}</strong> — Solicitado: {d.cantidad_solicitada}
                  <div className="form-row" style={{ marginTop: 8 }}>
                    <div className="form-group" style={{ margin: 0 }}>
                      <select className="form-select" value={asignaciones[d.id]?.lote_id || ''} onChange={e => setAsignaciones({ ...asignaciones, [d.id]: { ...asignaciones[d.id], lote_id: e.target.value } })}>
                        <option value="">Seleccionar lote...</option>
                        {lotes.filter(l => l.producto_nombre === d.producto_nombre).map(l => (
                          <option key={l.id} value={l.id}>Lote #{l.id} - OC:{l.orden_compra} (Disp: {l.cantidad_disponible})</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                      <input className="form-input" type="number" min="1" max={d.cantidad_solicitada} placeholder="Cantidad" value={asignaciones[d.id]?.cantidad || ''} onChange={e => setAsignaciones({ ...asignaciones, [d.id]: { ...asignaciones[d.id], cantidad: e.target.value } })} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="modal-footer"><button className="btn btn-secondary" onClick={() => setSelected(null)}>Cancelar</button><button className="btn btn-primary" onClick={handleAprobar}>Confirmar Aprobación</button></div>
          </div>
        </div>
      )}

      {viewingDetalle && (
        <div className="modal-overlay" onClick={() => setViewingDetalle(null)}>
          <div className="modal" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Detalles de Solicitud #{viewingDetalle.id}</h3>
              <button className="modal-close" onClick={() => setViewingDetalle(null)}>×</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: 16 }}>
                <strong>Estado:</strong> <span className={`badge badge-${viewingDetalle.estado.toLowerCase()}`}>{viewingDetalle.estado_display}</span>
                <br />
                {viewingDetalle.gestor_nombre && (
                  <span style={{ color: '#555', marginTop: 8, display: 'inline-block' }}>
                    <strong>Gestionado/Despachado por:</strong> {viewingDetalle.gestor_nombre}
                  </span>
                )}
              </p>
              <div style={{ background: '#FAFAFA', borderRadius: 6, padding: 12 }}>
                <h4 style={{ marginBottom: 12 }}>Productos Solicitados</h4>
                <ul style={{ paddingLeft: 20 }}>
                  {viewingDetalle.detalles.map(d => (
                    <li key={d.id} style={{ marginBottom: 8 }}>
                      <strong>{d.producto_nombre}</strong> <br />
                      <span style={{ fontSize: '0.9em', color: '#666' }}>
                        Solicitado: {d.cantidad_solicitada} 
                        {d.cantidad_aprobada !== null && ` | Aprobado/Despachado: ${d.cantidad_aprobada}`}
                        {d.lote_orden_compra && ` | Lote OC: ${d.lote_orden_compra}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setViewingDetalle(null)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
