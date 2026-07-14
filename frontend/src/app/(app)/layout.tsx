'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/app-header';
import { AppSidebar } from '@/components/app-sidebar';
import { LoadingState } from '@/components/loading-state';
import { useAuth } from '@/contexts/auth-context';

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!loading && !user) router.replace('/login'); }, [loading, user, router]);
  if (loading || !user) return <div className="min-h-screen"><LoadingState label="Preparando sua área de trabalho..."/></div>;
  return <div className="min-h-screen"><AppSidebar open={menuOpen} onClose={() => setMenuOpen(false)}/><div className="lg:pl-68"><AppHeader onMenu={() => setMenuOpen(true)}/><main className="p-5 lg:p-8">{children}</main></div></div>;
}
