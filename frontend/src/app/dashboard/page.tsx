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

  useEffect(() => {
    if (!user) return;
    apiFetch<PaginatedResponse<Producto>>('/productos/?page_size=100').then(r => {
      const criticos = r.results.filter(p => p.stock_disponible <= p.stock_minimo).length;
      setStats(s => ({ ...s, productos: r.count, criticos }));
    });
    if (user.rol === 'GESTOR') {
      apiFetch<PaginatedResponse<Lote>>('/lotes/?estado=ACTIVO&page_size=1').then(r =>
        setStats(s => ({ ...s, lotesActivos: r.count })));
    }
    apiFetch<PaginatedResponse<Solicitud>>('/solicitudes/?page_size=5').then(r => {
      setSolicitudesRecientes(r.results);
      const pendientes = r.results.filter(s => s.estado === 'PENDIENTE').length;
      setStats(s => ({ ...s, pendientes }));
    });
  }, [user]);

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
              <tr><th>ID</th><th>Fecha</th><th>Solicitante</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {solicitudesRecientes.length === 0 ? (
                <tr><td colSpan={4} className="table-empty">Sin solicitudes</td></tr>
              ) : solicitudesRecientes.map(s => (
                <tr key={s.id}>
                  <td>#{s.id}</td>
                  <td>{new Date(s.created_at).toLocaleDateString('es-CL')}</td>
                  <td>{s.solicitante_nombre}</td>
                  <td><span className={`badge badge-${s.estado.toLowerCase()}`}>{s.estado_display}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
