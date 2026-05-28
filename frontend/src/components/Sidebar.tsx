'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const GESTOR_NAV = [
  { section: 'General' },
  { href: '/dashboard', icon: '📊', label: 'Dashboard' },
  { section: 'Inventario' },
  { href: '/productos', icon: '📦', label: 'Productos' },
  { href: '/lotes', icon: '🏷️', label: 'Lotes' },
  { href: '/movimientos', icon: '📋', label: 'Movimientos' },
  { section: 'Solicitudes' },
  { href: '/solicitudes', icon: '📝', label: 'Solicitudes' },
];

const SOLICITANTE_NAV = [
  { section: 'General' },
  { href: '/dashboard', icon: '📊', label: 'Dashboard' },
  { href: '/productos', icon: '📦', label: 'Catálogo' },
  { section: 'Mis Solicitudes' },
  { href: '/solicitudes', icon: '📝', label: 'Mis Solicitudes' },
  { href: '/solicitudes/nueva', icon: '➕', label: 'Nueva Solicitud' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  if (!user) return null;

  const nav = user.rol === 'GESTOR' ? GESTOR_NAV : SOLICITANTE_NAV;

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h2>Comité Paritario</h2>
        <p>Gestión de Inventario</p>
      </div>
      <nav className="sidebar-nav">
        {nav.map((item, i) => {
          if ('section' in item && !('href' in item)) {
            return <div key={i} className="nav-section">{item.section}</div>;
          }
          if ('href' in item) {
            return (
              <Link key={item.href} href={item.href!}
                className={`nav-link ${pathname === item.href ? 'active' : ''}`}>
                <span className="icon">{item.icon}</span>
                {item.label}
              </Link>
            );
          }
          return null;
        })}
      </nav>
      <div className="sidebar-footer">
        <div style={{ marginBottom: 8 }}>
          <strong>{user.first_name} {user.last_name}</strong>
          <br />{user.rol === 'GESTOR' ? 'Gestor Paritario' : 'Solicitante'}
        </div>
        <button className="btn btn-sm btn-secondary" onClick={logout}
          style={{ width: '100%', justifyContent: 'center', color: '#fff', borderColor: 'rgba(255,255,255,0.2)' }}>
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
}
