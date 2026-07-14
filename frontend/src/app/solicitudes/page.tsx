'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import { Solicitud, Lote, PaginatedResponse } from '@/types';

export default function SolicitudesPage() {
  const { user } = useAuth();
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [selected, setSelected] = useState<Solicitud | null>(null);
  const [action, setAction] = useState<string>('');
  const [motivo, setMotivo] = useState('');
  const [viewingDetalle, setViewingDetalle] = useState<Solicitud | null>(null);
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [asignaciones, setAsignaciones] = useState<Record<number, { lote_id: string; cantidad: string }>>({});

  const load = () => {
    apiFetch<PaginatedResponse<Solicitud>>('/solicitudes/?page_size=100').then(r => setSolicitudes(r.results));
  };
  useEffect(() => { load(); }, []);

  const openAction = async (sol: Solicitud, act: string) => {
    setSelected(sol);
    setAction(act);
    setMotivo('');
    if (act === 'aprobar') {
      const r = await apiFetch<PaginatedResponse<Lote>>('/lotes/?estado=ACTIVO&page_size=200');
      setLotes(r.results);
      const init: Record<number, { lote_id: string; cantidad: string }> = {};
      sol.detalles.forEach(d => { init[d.id] = { lote_id: '', cantidad: String(d.cantidad_solicitada) }; });
      setAsignaciones(init);
    }
  };

  const handleAprobar = async () => {
    const data = Object.entries(asignaciones).map(([did, v]) => ({
      detalle_id: parseInt(did), lote_id: parseInt(v.lote_id), cantidad_aprobada: parseInt(v.cantidad),
    }));
    await apiFetch(`/solicitudes/${selected!.id}/aprobar/`, { method: 'POST', body: JSON.stringify({ asignaciones: data }) });
    setSelected(null); load();
  };

  const handleRechazar = async () => {
    await apiFetch(`/solicitudes/${selected!.id}/rechazar/`, { method: 'POST', body: JSON.stringify({ motivo_rechazo: motivo }) });
    setSelected(null); load();
  };

  const handleDespachar = async () => {
    await apiFetch(`/solicitudes/${selected!.id}/despachar/`, { method: 'POST' });
    setSelected(null); load();
  };

  const handleCancelar = async (id: number) => {
    await apiFetch(`/solicitudes/${id}/cancelar/`, { method: 'POST' });
    load();
  };

  return (
    <AppShell title="Solicitudes">
      <div className="page-header">
        <h2>{user?.rol === 'GESTOR' ? 'Gestión de Solicitudes' : 'Mis Solicitudes'}</h2>
        {user?.rol === 'SOLICITANTE' && <Link href="/solicitudes/nueva" className="btn btn-primary">+ Nueva Solicitud</Link>}
      </div>
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead><tr><th>#</th><th>Fecha</th><th>Solicitante</th><th>Productos</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {solicitudes.length === 0 ? (
                <tr><td colSpan={6} className="table-empty">Sin solicitudes</td></tr>
              ) : solicitudes.map(s => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{new Date(s.created_at).toLocaleDateString('es-CL')}</td>
                  <td>{s.solicitante_nombre}</td>
                  <td>{s.detalles.map(d => `${d.producto_nombre} (x${d.cantidad_solicitada})`).join(', ')}</td>
                  <td><span className={`badge badge-${s.estado.toLowerCase()}`}>{s.estado_display}</span></td>
                  <td className="flex gap-2">
                    {user?.rol === 'GESTOR' && s.estado === 'PENDIENTE' && (
                      <>
                        <button className="btn btn-sm btn-primary" onClick={() => openAction(s, 'aprobar')}>Aprobar</button>
                        <button className="btn btn-sm btn-danger" onClick={() => openAction(s, 'rechazar')}>Rechazar</button>
                      </>
                    )}
                    {user?.rol === 'GESTOR' && s.estado === 'APROBADA' && (
                      <button className="btn btn-sm btn-success" onClick={() => openAction(s, 'despachar')}>Despachar</button>
                    )}
                    {user?.rol === 'SOLICITANTE' && s.estado === 'PENDIENTE' && (
                      <button className="btn btn-sm btn-secondary" onClick={() => handleCancelar(s.id)}>Cancelar</button>
                    )}
                    <button className="btn btn-sm btn-secondary" onClick={() => setViewingDetalle(s)}>Ver Detalles</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && action === 'aprobar' && (
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

      {selected && action === 'rechazar' && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h3>Rechazar Solicitud #{selected.id}</h3><button className="modal-close" onClick={() => setSelected(null)}>×</button></div>
            <div className="modal-body">
              <div className="form-group"><label className="form-label">Motivo del rechazo (mín. 10 caracteres)</label><textarea className="form-textarea" required minLength={10} value={motivo} onChange={e => setMotivo(e.target.value)} /></div>
            </div>
            <div className="modal-footer"><button className="btn btn-secondary" onClick={() => setSelected(null)}>Cancelar</button><button className="btn btn-danger" onClick={handleRechazar} disabled={motivo.length < 10}>Confirmar Rechazo</button></div>
          </div>
        </div>
      )}

      {selected && action === 'despachar' && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h3>Despachar Solicitud #{selected.id}</h3><button className="modal-close" onClick={() => setSelected(null)}>×</button></div>
            <div className="modal-body">
              <p>¿Confirma el despacho físico de los siguientes productos?</p>
              <ul style={{ marginTop: 12 }}>{selected.detalles.map(d => <li key={d.id}>{d.producto_nombre} — {d.cantidad_aprobada} uds</li>)}</ul>
            </div>
            <div className="modal-footer"><button className="btn btn-secondary" onClick={() => setSelected(null)}>Cancelar</button><button className="btn btn-success" onClick={handleDespachar}>Confirmar Despacho</button></div>
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
                {viewingDetalle.motivo_rechazo && (
                  <>
                    <br />
                    <span style={{ color: '#e74c3c', marginTop: 8, display: 'inline-block' }}>
                      <strong>Motivo de Rechazo:</strong> {viewingDetalle.motivo_rechazo}
                    </span>
                  </>
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
