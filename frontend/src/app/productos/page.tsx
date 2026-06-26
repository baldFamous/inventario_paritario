'use client';
import { useEffect, useState } from 'react';
import AppShell from '@/components/AppShell';
import { useAuth } from '@/lib/auth';
import { apiFetch } from '@/lib/api';
import { Producto, Categoria, PaginatedResponse, AsignacionProducto } from '@/types';

export default function ProductosPage() {
  const { user } = useAuth();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  
  // Filters
  const [search, setSearch] = useState('');
  const [filterCodigo, setFilterCodigo] = useState('');
  const [filterNombre, setFilterNombre] = useState('');
  const [filterCategoria, setFilterCategoria] = useState('');
  
  // Modals
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState<Producto | null>(null);
  
  // Forms
  const [form, setForm] = useState({ categoria: '', codigo: '', nombre: '', unidad_medida: '', stock_minimo: '0' });
  const [editForm, setEditForm] = useState({ categoria: '', codigo: '', nombre: '', unidad_medida: '', stock_minimo: '0', asignado_a: '' });
  const [asignacionForm, setAsignacionForm] = useState({ asignado_a: '', cantidad: '1', observaciones: '' });

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

  const openEditModal = (p: Producto) => {
    setEditForm({
      categoria: p.categoria.toString(),
      codigo: p.codigo,
      nombre: p.nombre,
      unidad_medida: p.unidad_medida,
      stock_minimo: p.stock_minimo.toString(),
      asignado_a: p.asignado_a || ''
    });
    setShowEditModal(p);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showEditModal) return;
    await apiFetch(`/productos/${showEditModal.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ 
        ...editForm, 
        stock_minimo: parseInt(editForm.stock_minimo),
        asignado_a: editForm.asignado_a || null
      }),
    });
    setShowEditModal(null);
    load();
  };

  const handleAddAsignacion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showEditModal) return;
    await apiFetch(`/asignaciones-producto/`, {
      method: 'POST',
      body: JSON.stringify({
        producto: showEditModal.id,
        asignado_a: asignacionForm.asignado_a,
        cantidad: parseInt(asignacionForm.cantidad),
        observaciones: asignacionForm.observaciones
      }),
    });
    setAsignacionForm({ asignado_a: '', cantidad: '1', observaciones: '' });
    load();
    
    // Refresh the edit modal's data
    const updatedProd = await apiFetch<Producto>(`/productos/${showEditModal.id}/`);
    setShowEditModal(updatedProd);
  };

  const handleDeleteAsignacion = async (id: number) => {
    if (!showEditModal) return;
    await apiFetch(`/asignaciones-producto/${id}/`, { method: 'DELETE' });
    load();
    const updatedProd = await apiFetch<Producto>(`/productos/${showEditModal.id}/`);
    setShowEditModal(updatedProd);
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

      <div className="card mb-4" style={{ marginBottom: '1rem' }}>
        <div style={{ padding: '1rem' }}>
          <h4 style={{ marginBottom: '1rem' }}>Filtros de Búsqueda</h4>
          <div className="form-row" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
              <label className="form-label">Filtrar por Código</label>
              <input className="form-input" placeholder="Ej: P-001..." value={filterCodigo} onChange={e => setFilterCodigo(e.target.value)} />
            </div>
            <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
              <label className="form-label">Filtrar por Nombre</label>
              <input className="form-input" placeholder="Ej: Mouse..." value={filterNombre} onChange={e => setFilterNombre(e.target.value)} />
            </div>
            <div className="form-group" style={{ flex: '1', minWidth: '200px' }}>
              <label className="form-label">Filtrar por Categoría</label>
              <select className="form-select" value={filterCategoria} onChange={e => setFilterCategoria(e.target.value)}>
                <option value="">Todas las categorías</option>
                {categorias.map(c => <option key={c.id} value={c.nombre}>{c.nombre}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Categoría</th>
                <th>Unidad</th>
                <th>Disponible</th>
                <th>Reservado</th>
                <th>Mínimo</th>
                <th>Asignado A (General)</th>
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
                    {p.asignado_a ? <span className="badge badge-info">{p.asignado_a}</span> : <span className="text-muted">Sin asignar</span>}
                    {p.asignaciones_individuales && p.asignaciones_individuales.length > 0 && (
                      <span style={{ display: 'block', fontSize: '0.8rem', color: '#666', marginTop: '4px' }}>
                        + {p.asignaciones_individuales.length} asignaciones ind.
                      </span>
                    )}
                  </td>
                  {user?.rol === 'GESTOR' && (
                    <td>
                      <button className="btn btn-sm btn-secondary" onClick={() => openEditModal(p)}>Editar</button>
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

      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(null)}>
          <div className="modal" style={{ maxWidth: '800px', width: '90%' }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Editar Producto: {showEditModal.codigo}</h3>
              <button className="modal-close" onClick={() => setShowEditModal(null)}>×</button>
            </div>
            
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Sección de Edición Principal */}
              <form onSubmit={handleUpdate}>
                <h4 style={{ marginBottom: '1rem', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Datos Generales</h4>
                <div className="form-group">
                  <label className="form-label">Categoría</label>
                  <select className="form-select" required value={editForm.categoria}
                    onChange={e => setEditForm({ ...editForm, categoria: e.target.value })}>
                    <option value="">Seleccionar...</option>
                    {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Código</label>
                    <input className="form-input" required value={editForm.codigo}
                      onChange={e => setEditForm({ ...editForm, codigo: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Unidad de Medida</label>
                    <input className="form-input" required value={editForm.unidad_medida}
                      onChange={e => setEditForm({ ...editForm, unidad_medida: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Nombre</label>
                  <input className="form-input" required value={editForm.nombre}
                    onChange={e => setEditForm({ ...editForm, nombre: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Stock Mínimo</label>
                    <input className="form-input" type="number" min="0" value={editForm.stock_minimo}
                      onChange={e => setEditForm({ ...editForm, stock_minimo: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Asignado A (General)</label>
                    <input className="form-input" value={editForm.asignado_a} placeholder="Ej: Gimnasio, Oficina 1..."
                      onChange={e => setEditForm({ ...editForm, asignado_a: e.target.value })} />
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
                  <button className="btn btn-primary" type="submit">Actualizar Producto</button>
                </div>
              </form>

              {/* Sección de Asignaciones Individuales */}
              <div>
                <h4 style={{ marginBottom: '1rem', borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Asignaciones Individuales</h4>
                <p className="text-muted" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
                  Lleva un control de qué persona tiene asignada unidades de este producto.
                </p>
                
                <form onSubmit={handleAddAsignacion} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '1.5rem', background: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                  <div className="form-group" style={{ flex: 2, marginBottom: 0 }}>
                    <label className="form-label">Persona asignada</label>
                    <input className="form-input" required placeholder="Nombre de la persona" value={asignacionForm.asignado_a} onChange={e => setAsignacionForm({...asignacionForm, asignado_a: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                    <label className="form-label">Cant.</label>
                    <input className="form-input" type="number" min="1" required value={asignacionForm.cantidad} onChange={e => setAsignacionForm({...asignacionForm, cantidad: e.target.value})} />
                  </div>
                  <button className="btn btn-primary" type="submit" style={{ whiteSpace: 'nowrap' }}>+ Asignar</button>
                </form>

                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Persona</th>
                      <th style={{ padding: '8px' }}>Cant.</th>
                      <th style={{ padding: '8px' }}>Fecha</th>
                      <th style={{ padding: '8px' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {(!showEditModal.asignaciones_individuales || showEditModal.asignaciones_individuales.length === 0) ? (
                      <tr><td colSpan={4} style={{ padding: '8px', textAlign: 'center', color: '#888' }}>Sin asignaciones registradas</td></tr>
                    ) : showEditModal.asignaciones_individuales.map(asig => (
                      <tr key={asig.id} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '8px' }}><strong>{asig.asignado_a}</strong></td>
                        <td style={{ padding: '8px' }}>{asig.cantidad}</td>
                        <td style={{ padding: '8px' }}>{new Date(asig.fecha).toLocaleDateString('es-CL')}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDeleteAsignacion(asig.id)}>Quitar</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>
      )}

    </AppShell>
  );
}
