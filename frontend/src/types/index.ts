export interface Usuario {
  id: number;
  rut: string;
  username: string;
  first_name: string;
  last_name: string;
  nombre_completo: string;
  email: string;
  rol: 'SOLICITANTE' | 'GESTOR';
  unidad: string;
  is_active: boolean;
}

export interface Categoria {
  id: number;
  nombre: string;
  descripcion: string;
  productos_count: number;
}

export interface Producto {
  id: number;
  categoria: number;
  categoria_nombre: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  unidad_medida: string;
  stock_minimo: number;
  is_active: boolean;
  stock_disponible: number;
  stock_reservado: number;
  asignado_a?: string | null;
  asignaciones_individuales?: AsignacionProducto[];
}

export interface AsignacionProducto {
  id: number;
  producto: number;
  asignado_a: string;
  cantidad: number;
  fecha: string;
  observaciones: string;
}

export interface Lote {
  id: number;
  producto: number;
  producto_nombre: string;
  producto_codigo: string;
  orden_compra: string;
  costo_unitario: string;
  costo_total: string;
  cantidad_inicial: number;
  cantidad_disponible: number;
  cantidad_reservada: number;
  fecha_ingreso: string;
  fecha_caducidad: string | null;
  archivo_adjunto: string | null;
  estado: 'ACTIVO' | 'AGOTADO' | 'VENCIDO' | 'BAJA';
  created_at: string;
}

export interface Movimiento {
  id: number;
  lote: number;
  lote_info: string;
  solicitud: number | null;
  ejecutado_por: number;
  ejecutado_por_nombre: string;
  tipo: 'INGRESO' | 'DESPACHO' | 'BAJA' | 'RESERVA' | 'LIBERACION';
  tipo_display: string;
  cantidad: number;
  stock_anterior: number;
  stock_posterior: number;
  motivo: string;
  created_at: string;
}

export interface DetalleSolicitud {
  id: number;
  producto: number;
  producto_nombre: string;
  producto_codigo: string;
  lote: number | null;
  lote_orden_compra: string | null;
  cantidad_solicitada: number;
  cantidad_aprobada: number | null;
}

export interface Solicitud {
  id: number;
  solicitante: number;
  solicitante_nombre: string;
  gestor: number | null;
  gestor_nombre: string | null;
  estado: 'PENDIENTE' | 'APROBADA' | 'DESPACHADA' | 'RECHAZADA' | 'CANCELADA';
  estado_display: string;
  motivo_rechazo: string;
  observaciones: string;
  detalles: DetalleSolicitud[];
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
