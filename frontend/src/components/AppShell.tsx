'use client';
import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import Sidebar from './Sidebar';
import Header from './Header';

export default function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace('/login');
  }, [user, loading, router]);

  if (loading) return <div className="loading">Cargando...</div>;
  if (!user) return null;

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-wrapper">
        <Header title={title} />
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
