'use client';
import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { apiFetch } from '@/lib/api';
import { Lote, Producto, PaginatedResponse } from '@/types';

export default function LotesPage() {
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [showBaja, setShowBaja] = useState<Lote | null>(null);
  const [form, setForm] = useState({ producto: '', orden_compra: '', costo_unitario: '', cantidad: '', fecha_ingreso: '', fecha_caducidad: '' });
  const [bajaForm, setBajaForm] = useState({ cantidad: '', motivo: '' });

  const load = () => {
    const q = filtroEstado ? `?estado=${filtroEstado}&page_size=100` : '?page_size=100';
    apiFetch<PaginatedResponse<Lote>>(`/lotes/${q}`).then(r => setLotes(r.results));
  };

  useEffect(() => { load(); }, [filtroEstado]);
  useEffect(() => {
    apiFetch<PaginatedResponse<Producto>>('/productos/?page_size=200').then(r => setProductos(r.results));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch('/lotes/', {
      method: 'POST',
      body: JSON.stringify({
        producto: parseInt(form.producto),
        orden_compra: form.orden_compra,
        costo_unitario: form.costo_unitario,
        cantidad: parseInt(form.cantidad),
        fecha_ingreso: form.fecha_ingreso,
        fecha_caducidad: form.fecha_caducidad || null,
      }),
    });
    setShowNew(false);
    setForm({ producto: '', orden_compra: '', costo_unitario: '', cantidad: '', fecha_ingreso: '', fecha_caducidad: '' });
    load();
  };

  const handleBaja = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch(`/lotes/${showBaja!.id}/baja/`, {
      method: 'POST',
      body: JSON.stringify({ cantidad: parseInt(bajaForm.cantidad), motivo: bajaForm.motivo }),
    });
    setShowBaja(null);
    setBajaForm({ cantidad: '', motivo: '' });
    load();
  };

  return (
    <AppShell title="Lotes">
      <div className="page-header">
        <h2>Gestión de Lotes</h2>
        <button className="btn btn-primary" onClick={() => setShowNew(true)}>+ Registrar Lote</button>
      </div>
      <div className="toolbar">
        <select className="form-select" style={{ maxWidth: 200 }} value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="ACTIVO">Activo</option>
          <option value="AGOTADO">Agotado</option>
          <option value="VENCIDO">Vencido</option>
          <option value="BAJA">Baja</option>
        </select>
      </div>
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>#</th><th>Producto</th><th>OC</th><th>Inicial</th><th>Disponible</th><th>Reservado</th><th>Costo Ud.</th><th>Vencimiento</th><th>Estado</th><th></th></tr>
            </thead>
            <tbody>
              {lotes.length === 0 ? (
                <tr><td colSpan={10} className="table-empty">No hay lotes</td></tr>
              ) : lotes.map(l => (
                <tr key={l.id}>
                  <td>{l.id}</td>
                  <td>{l.producto_nombre}</td>
                  <td>{l.orden_compra}</td>
                  <td>{l.cantidad_inicial}</td>
                  <td>{l.cantidad_disponible}</td>
                  <td>{l.cantidad_reservada}</td>
                  <td>${Number(l.costo_unitario).toLocaleString('es-CL')}</td>
                  <td>{l.fecha_caducidad || '—'}</td>
                  <td><span className={`badge badge-${l.estado.toLowerCase()}`}>{l.estado}</span></td>
                  <td>
                    {l.estado === 'ACTIVO' && l.cantidad_disponible > 0 && (
                      <button className="btn btn-sm btn-danger" onClick={() => { setShowBaja(l); setBajaForm({ cantidad: '', motivo: '' }); }}>Baja</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showNew && (
        <div className="modal-overlay" onClick={() => setShowNew(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h3>Registrar Nuevo Lote</h3><button className="modal-close" onClick={() => setShowNew(false)}>×</button></div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Producto</label>
                  <select className="form-select" required value={form.producto} onChange={e => setForm({ ...form, producto: e.target.value })}>
                    <option value="">Seleccionar...</option>
                    {productos.map(p => <option key={p.id} value={p.id}>{p.codigo} - {p.nombre}</option>)}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group"><label className="form-label">Orden de Compra</label><input className="form-input" required value={form.orden_compra} onChange={e => setForm({ ...form, orden_compra: e.target.value })} /></div>
                  <div className="form-group"><label className="form-label">Costo Unitario ($)</label><input className="form-input" type="number" step="0.01" required value={form.costo_unitario} onChange={e => setForm({ ...form, costo_unitario: e.target.value })} /></div>
                </div>
                <div className="form-row">
                  <div className="form-group"><label className="form-label">Cantidad</label><input className="form-input" type="number" min="1" required value={form.cantidad} onChange={e => setForm({ ...form, cantidad: e.target.value })} /></div>
                  <div className="form-group"><label className="form-label">Fecha Ingreso</label><input className="form-input" type="date" required value={form.fecha_ingreso} onChange={e => setForm({ ...form, fecha_ingreso: e.target.value })} /></div>
                </div>
                <div className="form-group"><label className="form-label">Fecha Caducidad (opcional)</label><input className="form-input" type="date" value={form.fecha_caducidad} onChange={e => setForm({ ...form, fecha_caducidad: e.target.value })} /></div>
              </div>
              <div className="modal-footer"><button className="btn btn-secondary" type="button" onClick={() => setShowNew(false)}>Cancelar</button><button className="btn btn-primary" type="submit">Registrar</button></div>
            </form>
          </div>
        </div>
      )}

      {showBaja && (
        <div className="modal-overlay" onClick={() => setShowBaja(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h3>Dar de Baja — Lote #{showBaja.id}</h3><button className="modal-close" onClick={() => setShowBaja(null)}>×</button></div>
            <form onSubmit={handleBaja}>
              <div className="modal-body">
                <p className="text-muted mb-4">{showBaja.producto_nombre} — Disponible: {showBaja.cantidad_disponible}</p>
                <div className="form-group"><label className="form-label">Cantidad a dar de baja</label><input className="form-input" type="number" min="1" max={showBaja.cantidad_disponible} required value={bajaForm.cantidad} onChange={e => setBajaForm({ ...bajaForm, cantidad: e.target.value })} /></div>
                <div className="form-group"><label className="form-label">Motivo (mín. 10 caracteres)</label><textarea className="form-textarea" required minLength={10} value={bajaForm.motivo} onChange={e => setBajaForm({ ...bajaForm, motivo: e.target.value })} /></div>
              </div>
              <div className="modal-footer"><button className="btn btn-secondary" type="button" onClick={() => setShowBaja(null)}>Cancelar</button><button className="btn btn-danger" type="submit">Confirmar Baja</button></div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
