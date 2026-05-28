'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import { apiFetch } from '@/lib/api';
import { Producto, PaginatedResponse } from '@/types';

interface CartItem {
  producto_id: number;
  nombre: string;
  codigo: string;
  stock: number;
  cantidad_solicitada: number;
}

export default function NuevaSolicitudPage() {
  const router = useRouter();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [observaciones, setObservaciones] = useState('');
  const [search, setSearch] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    apiFetch<PaginatedResponse<Producto>>('/productos/?page_size=200').then(r => setProductos(r.results));
  }, []);

  const addToCart = (p: Producto) => {
    if (cart.find(c => c.producto_id === p.id)) return;
    setCart([...cart, { producto_id: p.id, nombre: p.nombre, codigo: p.codigo, stock: p.stock_disponible, cantidad_solicitada: 1 }]);
  };

  const updateQty = (pid: number, qty: number) => {
    setCart(cart.map(c => c.producto_id === pid ? { ...c, cantidad_solicitada: qty } : c));
  };

  const removeFromCart = (pid: number) => {
    setCart(cart.filter(c => c.producto_id !== pid));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    try {
      await apiFetch('/solicitudes/crear/', {
        method: 'POST',
        body: JSON.stringify({
          observaciones,
          items: cart.map(c => ({ producto_id: c.producto_id, cantidad_solicitada: c.cantidad_solicitada })),
        }),
      });
      router.push('/solicitudes');
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error al crear solicitud');
    } finally {
      setSending(false);
    }
  };

  const filtered = productos.filter(p =>
    p.nombre.toLowerCase().includes(search.toLowerCase()) || p.codigo.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppShell title="Nueva Solicitud">
      <div className="page-header"><h2>Crear Solicitud de Insumos</h2></div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="card">
          <div className="card-header"><h3 className="card-title">Catálogo</h3></div>
          <input className="form-input mb-4" placeholder="Buscar producto..." value={search} onChange={e => setSearch(e.target.value)} />
          <div className="table-wrapper" style={{ maxHeight: 400, overflowY: 'auto' }}>
            <table>
              <thead><tr><th>Código</th><th>Nombre</th><th>Stock</th><th></th></tr></thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.id}>
                    <td>{p.codigo}</td>
                    <td>{p.nombre}</td>
                    <td>{p.stock_disponible}</td>
                    <td>
                      <button className="btn btn-sm btn-primary" onClick={() => addToCart(p)}
                        disabled={cart.some(c => c.producto_id === p.id) || p.stock_disponible === 0}>
                        {cart.some(c => c.producto_id === p.id) ? '✓' : '+'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <form onSubmit={handleSubmit}>
            <div className="card mb-4">
              <div className="card-header"><h3 className="card-title">Productos seleccionados ({cart.length})</h3></div>
              {cart.length === 0 ? (
                <p className="text-muted text-center">Agregue productos del catálogo</p>
              ) : (
                <table>
                  <thead><tr><th>Producto</th><th>Cantidad</th><th></th></tr></thead>
                  <tbody>
                    {cart.map(c => (
                      <tr key={c.producto_id}>
                        <td>{c.codigo} - {c.nombre}</td>
                        <td><input className="form-input" type="number" min="1" style={{ width: 80 }} value={c.cantidad_solicitada} onChange={e => updateQty(c.producto_id, parseInt(e.target.value) || 1)} /></td>
                        <td><button type="button" className="btn btn-sm btn-danger" onClick={() => removeFromCart(c.producto_id)}>×</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="card">
              <div className="form-group">
                <label className="form-label">Observaciones (opcional)</label>
                <textarea className="form-textarea" value={observaciones} onChange={e => setObservaciones(e.target.value)} placeholder="Motivo o urgencia de la solicitud..." />
              </div>
              <button className="btn btn-primary btn-lg" type="submit" disabled={cart.length === 0 || sending} style={{ width: '100%', justifyContent: 'center' }}>
                {sending ? 'Enviando...' : 'Enviar Solicitud'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
