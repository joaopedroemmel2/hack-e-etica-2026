'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, FolderKanban, LayoutDashboard, LogOut, UserRound, X } from 'lucide-react';
import { Brand } from './brand';
import { useAuth } from '@/contexts/auth-context';
import { cn } from '@/lib/utils';

const navigation = [
  { href: '/dashboard', label: 'Visão geral', icon: LayoutDashboard },
  { href: '/projetos', label: 'Projetos', icon: FolderKanban },
  { href: '/tarefas', label: 'Tarefas', icon: BarChart3 },
  { href: '/perfil', label: 'Meu perfil', icon: UserRound },
];

export function AppSidebar({ open, onClose }: { open: boolean; onClose(): void }) {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  return <><div className={cn('fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-sm lg:hidden', open ? 'block' : 'hidden')} onClick={onClose}/><aside className={cn('fixed inset-y-0 left-0 z-50 flex w-68 flex-col border-r bg-card p-4 transition-transform lg:translate-x-0', open ? 'translate-x-0' : '-translate-x-full')}><div className="flex items-center justify-between px-2 py-3"><Brand/><button className="rounded-lg p-2 hover:bg-muted lg:hidden" onClick={onClose}><X className="size-5"/></button></div><nav className="mt-8 flex-1 space-y-1.5">{navigation.map(({ href, label, icon: Icon }) => { const active = pathname === href; return <Link key={href} href={href} onClick={onClose} className={cn('flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition', active ? 'bg-primary text-white shadow-md shadow-primary/15' : 'text-muted-foreground hover:bg-muted hover:text-foreground')}><Icon className="size-4.5"/>{label}</Link>; })}</nav><div className="rounded-2xl bg-muted/70 p-3"><div className="mb-3 flex items-center gap-3"><div className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-sm font-bold text-primary">{user?.name?.charAt(0).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-sm font-semibold">{user?.name}</p><p className="truncate text-[11px] uppercase tracking-wide text-muted-foreground">{user?.role === 'COLABORADOR' ? 'Colaborador' : user?.role === 'GESTOR' ? 'Gestor' : 'Administrador'}</p></div></div><button onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-xs font-semibold text-muted-foreground hover:bg-white hover:text-destructive"><LogOut className="size-3.5"/> Sair da conta</button></div></aside></>;
}
