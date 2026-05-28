'use client';
import { useAuth } from '@/lib/auth';

export default function Header({ title }: { title: string }) {
  const { user } = useAuth();
  if (!user) return null;

  const initials = `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`;

  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-user">
        <span>{user.nombre_completo}</span>
        <div className="header-avatar">{initials}</div>
      </div>
    </header>
  );
}
