'use client';
import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import { Producto, Categoria, PaginatedResponse } from '@/types';

export default function ProductosPage() {
  const { user } = useAuth();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [search, setSearch] = useState('');
  const [filterCodigo, setFilterCodigo] = useState('');
  const [filterNombre, setFilterNombre] = useState('');
  const [filterCategoria, setFilterCategoria] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ categoria: '', codigo: '', nombre: '', unidad_medida: '', stock_minimo: '0' });
  const [editAsignacion, setEditAsignacion] = useState<number | null>(null);
  const [asignacionValue, setAsignacionValue] = useState('');

  const load = () => {
    apiFetch<PaginatedResponse<Producto>>(`/productos/?search=${search}&page_size=100`).then(r => setProductos(r.results));
  };

  useEffect(() => { load(); }, [search]);
  useEffect(() => {
    apiFetch<PaginatedResponse<Categoria>>('/categorias/?page_size=100').then(r => setCategorias(r.results));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch('/productos/', {
      method: 'POST',
      body: JSON.stringify({ ...form, stock_minimo: parseInt(form.stock_minimo) }),
    });
    setShowModal(false);
    setForm({ categoria: '', codigo: '', nombre: '', unidad_medida: '', stock_minimo: '0' });
    load();
  };

  const handleUpdateAsignacion = async (id: number) => {
    await apiFetch(`/productos/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ asignado_a: asignacionValue || null }),
    });
    setEditAsignacion(null);
    load();
  };

  const filteredProductos = productos.filter(p => {
    return p.codigo.toLowerCase().includes(filterCodigo.toLowerCase()) &&
      p.nombre.toLowerCase().includes(filterNombre.toLowerCase()) &&
      p.categoria_nombre.toLowerCase().includes(filterCategoria.toLowerCase());
  });

  return (
    <AppShell title="Productos">
      <div className="page-header">
        <h2>Catálogo de Productos</h2>
        {user?.rol === 'GESTOR' && (
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Nuevo Producto</button>
        )}
      </div>
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  Código
                  <input className="form-input" style={{ marginTop: '4px', padding: '4px', fontSize: '0.8rem', width: '10rem' }} placeholder="Filtrar..." value={filterCodigo} onChange={e => setFilterCodigo(e.target.value)} />
                </th>
                <th>
                  Nombre
                  <input className="form-input" style={{ marginTop: '4px', padding: '4px', fontSize: '0.8rem', width: '10rem' }} placeholder="Filtrar..." value={filterNombre} onChange={e => setFilterNombre(e.target.value)} />
                </th>
                <th>
                  Categoría
                  <select className="form-select" style={{ marginTop: '4px', padding: '4px', fontSize: '0.8rem', width: '10rem' }} value={filterCategoria} onChange={e => setFilterCategoria(e.target.value)}>
                    <option value="">Todas</option>
                    {categorias.map(c => <option key={c.id} value={c.nombre}>{c.nombre}</option>)}
                  </select>
                </th>
                <th>Unidad</th><th>Disponible</th><th>Reservado</th><th>Mínimo</th><th>Asignado A</th>
                {user?.rol === 'GESTOR' && <th>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {filteredProductos.length === 0 ? (
                <tr><td colSpan={user?.rol === 'GESTOR' ? 9 : 8} className="table-empty">No hay productos</td></tr>
              ) : filteredProductos.map(p => (
                <tr key={p.id}>
                  <td><strong>{p.codigo}</strong></td>
                  <td>{p.nombre}</td>
                  <td>{p.categoria_nombre}</td>
                  <td>{p.unidad_medida}</td>
                  <td className={p.stock_disponible <= p.stock_minimo ? 'stock-critical' : ''}>
                    {p.stock_disponible}
                  </td>
                  <td>{p.stock_reservado}</td>
                  <td>{p.stock_minimo}</td>
                  <td>
                    {editAsignacion === p.id ? (
                      <input 
                        className="form-input" 
                        placeholder="Ej: Gimnasio, Juan..."
                        value={asignacionValue} 
                        onChange={e => setAsignacionValue(e.target.value)} 
                        autoFocus
                      />
                    ) : (
                      p.asignado_a ? <span className="badge badge-info">{p.asignado_a}</span> : <span className="text-muted">Sin asignar</span>
                    )}
                  </td>
                  {user?.rol === 'GESTOR' && (
                    <td>
                      {editAsignacion === p.id ? (
                        <div className="flex gap-2" style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn btn-sm btn-primary" onClick={() => handleUpdateAsignacion(p.id)}>Guardar</button>
                          <button className="btn btn-sm btn-secondary" onClick={() => setEditAsignacion(null)}>Cancelar</button>
                        </div>
                      ) : (
                        <button className="btn btn-sm btn-secondary" onClick={() => { setEditAsignacion(p.id); setAsignacionValue(p.asignado_a || ''); }}>Editar</button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Nuevo Producto</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Categoría</label>
                  <select className="form-select" required value={form.categoria}
                    onChange={e => setForm({ ...form, categoria: e.target.value })}>
                    <option value="">Seleccionar...</option>
                    {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Código</label>
                    <input className="form-input" required value={form.codigo}
                      onChange={e => setForm({ ...form, codigo: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Unidad de Medida</label>
                    <input className="form-input" required value={form.unidad_medida}
                      onChange={e => setForm({ ...form, unidad_medida: e.target.value })} placeholder="ej: litro, caja, par" />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Nombre</label>
                  <input className="form-input" required value={form.nombre}
                    onChange={e => setForm({ ...form, nombre: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Stock Mínimo</label>
                  <input className="form-input" type="number" min="0" value={form.stock_minimo}
                    onChange={e => setForm({ ...form, stock_minimo: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" type="button" onClick={() => setShowModal(false)}>Cancelar</button>
                <button className="btn btn-primary" type="submit">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
