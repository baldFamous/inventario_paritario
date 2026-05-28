import './globals.css';
import { AuthProvider } from '@/lib/auth';

export const metadata = {
  title: 'Gestión de Inventario - Comité Paritario',
  description: 'Sistema de gestión de inventario del Comité Paritario',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
