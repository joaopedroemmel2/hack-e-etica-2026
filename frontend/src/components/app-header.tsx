'use client';
import { Bell, Menu, Search } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { Input } from './ui/input';
import { useAuth } from '@/contexts/auth-context';

const titles: Record<string, { title: string; description: string }> = {
  '/dashboard': { title: 'Visão geral', description: 'Acompanhe a saúde da sua operação.' },
  '/projetos': { title: 'Projetos', description: 'Prazos, responsáveis e progresso em um só lugar.' },
  '/tarefas': { title: 'Tarefas', description: 'Organize prioridades e mantenha o fluxo.' },
  '/perfil': { title: 'Meu perfil', description: 'Gerencie suas informações e capacidade.' },
};
export function AppHeader({ onMenu }: { onMenu(): void }) { const pathname = usePathname(); const { user } = useAuth(); const content = titles[pathname] ?? titles['/dashboard']; return <header className="flex min-h-22 items-center justify-between gap-4 border-b bg-background/90 px-5 backdrop-blur lg:px-8"><div className="flex items-center gap-3"><button onClick={onMenu} className="rounded-xl border bg-card p-2.5 lg:hidden"><Menu className="size-5"/></button><div><h1 className="text-xl font-bold tracking-tight lg:text-2xl">{content.title}</h1><p className="hidden text-sm text-muted-foreground sm:block">{content.description}</p></div></div><div className="flex items-center gap-2"><div className="relative hidden xl:block"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"/><Input placeholder="Buscar na plataforma..." className="w-64 bg-card pl-9"/></div><button className="relative rounded-xl border bg-card p-2.5 text-muted-foreground hover:text-foreground"><Bell className="size-4.5"/><span className="absolute right-2 top-2 size-1.5 rounded-full bg-red-500"/></button><div className="ml-1 hidden items-center gap-2 sm:flex"><div className="flex size-9 items-center justify-center rounded-xl bg-primary text-sm font-bold text-white">{user?.name?.charAt(0).toUpperCase()}</div></div></div></header>; }
