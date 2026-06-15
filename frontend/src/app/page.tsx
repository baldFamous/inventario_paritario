'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { Producto, PaginatedResponse } from '@/types';

interface CartItem {
  producto_id: number;
  nombre: string;
  cantidad_solicitada: number;
}

export default function PublicRequestForm() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [nombre, setNombre] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    apiFetch<PaginatedResponse<Producto>>('/productos/?page_size=100')
      .then(r => setProductos(r.results))
      .catch(e => console.error('Error cargando catálogo', e));
  }, []);

  const addToCart = (producto: Producto) => {
    setCart(prev => {
      const exists = prev.find(i => i.producto_id === producto.id);
      if (exists) {
        return prev.map(i => i.producto_id === producto.id ? { ...i, cantidad_solicitada: i.cantidad_solicitada + 1 } : i);
      }
      return [...prev, { producto_id: producto.id, nombre: producto.nombre, cantidad_solicitada: 1 }];
    });
  };

  const removeFromCart = (id: number) => {
    setCart(prev => prev.filter(i => i.producto_id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cart.length === 0) return alert('Debes agregar al menos un producto.');
    if (!nombre.trim()) return alert('Tu nombre es requerido.');

    setLoading(true);
    try {
      await apiFetch('/solicitudes/crear/', {
        method: 'POST',
        body: JSON.stringify({
          solicitante_nombre: nombre,
          observaciones,
          items: cart.map(c => ({
            producto_id: c.producto_id,
            cantidad_solicitada: c.cantidad_solicitada
          }))
        })
      });
      setSuccess(true);
      setCart([]);
      setNombre('');
      setObservaciones('');
    } catch (err: any) {
      alert(err.message || 'Error al enviar la solicitud');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="login-container">
        <div className="login-card" style={{ textAlign: 'center' }}>
          <h2 style={{ color: 'var(--success)', marginBottom: 16 }}>¡Solicitud Enviada!</h2>
          <p style={{ marginBottom: 24, color: 'var(--text-secondary)' }}>
            Tu solicitud ha sido registrada exitosamente. El comité paritario la revisará pronto.
          </p>
          <button className="btn btn-primary" onClick={() => setSuccess(false)}>
            Hacer otra solicitud
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--background)' }}>
      <header className="header" style={{ marginLeft: 0, justifyContent: 'space-between', padding: '0 2rem' }}>
        <h1 className="header-title">Comité Paritario - Solicitud de Insumos</h1>
        <Link href="/login" className="btn btn-secondary btn-sm">Acceso Mantenedores</Link>
      </header>

      <main style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 400px', gap: '2rem' }}>
        <section>
          <h2 style={{ marginBottom: '1rem' }}>Catálogo de Insumos</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
            {productos.map(p => (
              <div key={p.id} className="card" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{p.categoria_nombre}</div>
                <strong style={{ fontSize: '1.1rem' }}>{p.nombre}</strong>
                <button className="btn btn-secondary btn-sm" style={{ marginTop: 'auto' }} onClick={() => addToCart(p)}>
                  + Añadir
                </button>
              </div>
            ))}
            {productos.length === 0 && <p>No hay productos disponibles en el catálogo.</p>}
          </div>
        </section>

        <aside>
          <form className="card" onSubmit={handleSubmit} style={{ position: 'sticky', top: '5rem' }}>
            <h3 style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>Tu Solicitud</h3>
            
            <div className="form-group">
              <label className="form-label">Tu Nombre Completo *</label>
              <input className="form-input" required value={nombre} onChange={e => setNombre(e.target.value)} placeholder="Ej: Juan Pérez" />
            </div>

            <div className="form-group">
              <label className="form-label">Productos Seleccionados</label>
              {cart.length === 0 ? (
                <div style={{ padding: '1rem', backgroundColor: 'var(--background)', borderRadius: 'var(--radius)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Añade productos desde el catálogo
                </div>
              ) : (
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {cart.map(c => (
                    <li key={c.producto_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--background)', padding: '0.5rem', borderRadius: 'var(--radius)' }}>
                      <div>
                        <strong>{c.nombre}</strong>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Cantidad: {c.cantidad_solicitada}</div>
                      </div>
                      <button type="button" onClick={() => removeFromCart(c.producto_id)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '0.5rem' }}>×</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Observaciones (Opcional)</label>
              <textarea className="form-input" rows={3} value={observaciones} onChange={e => setObservaciones(e.target.value)} placeholder="Motivo de la solicitud, unidad, etc." />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading || cart.length === 0}>
              {loading ? 'Enviando...' : 'Enviar Solicitud'}
            </button>
          </form>
        </aside>
      </main>
    </div>
  );
}
