'use client';
import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import { Movimiento, PaginatedResponse } from '@/types';

export default function MovimientosPage() {
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [filtroTipo, setFiltroTipo] = useState('');

  useEffect(() => {
    const q = filtroTipo ? `?tipo=${filtroTipo}&page_size=100` : '?page_size=100';
    apiFetch<PaginatedResponse<Movimiento>>(`/movimientos/${q}`).then(r => setMovimientos(r.results));
  }, [filtroTipo]);

  return (
    <AppShell title="Movimientos">
      <div className="page-header"><h2>Historial de Movimientos</h2></div>
      <div className="toolbar">
        <select className="form-select" style={{ maxWidth: 200 }} value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)}>
          <option value="">Todos los tipos</option>
          <option value="INGRESO">Ingreso</option>
          <option value="DESPACHO">Despacho</option>
          <option value="BAJA">Baja</option>
          <option value="RESERVA">Reserva</option>
          <option value="LIBERACION">Liberación</option>
        </select>
      </div>
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>Fecha</th><th>Tipo</th><th>Lote</th><th>Cantidad</th><th>Stock Ant.</th><th>Stock Post.</th><th>Ejecutor</th><th>Motivo</th></tr>
            </thead>
            <tbody>
              {movimientos.length === 0 ? (
                <tr><td colSpan={8} className="table-empty">Sin movimientos</td></tr>
              ) : movimientos.map(m => (
                <tr key={m.id}>
                  <td>{new Date(m.created_at).toLocaleString('es-CL')}</td>
                  <td><span className={`badge badge-${m.tipo.toLowerCase()}`}>{m.tipo_display}</span></td>
                  <td>{m.lote_info}</td>
                  <td>{m.cantidad}</td>
                  <td>{m.stock_anterior}</td>
                  <td>{m.stock_posterior}</td>
                  <td>{m.ejecutado_por_nombre}</td>
                  <td>{m.motivo || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
