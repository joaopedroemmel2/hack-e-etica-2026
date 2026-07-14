'use client';

import { useCallback, useEffect, useState } from 'react';
import { CalendarDays, FolderKanban, LoaderCircle, Plus, Search, UserRound } from 'lucide-react';
import { EmptyState } from '@/components/empty-state';
import { LoadingState } from '@/components/loading-state';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/auth-context';
import { apiFetch } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import type { Paginated, Project } from '@/types';

interface TeamItem { id: string; name: string }
const statusMap = {
  PLANNING: { label: 'Planejamento', className: 'bg-slate-100 text-slate-700' },
  ACTIVE: { label: 'Ativo', className: 'bg-emerald-50 text-emerald-700' },
  ON_HOLD: { label: 'Em pausa', className: 'bg-amber-50 text-amber-700' },
  COMPLETED: { label: 'Concluído', className: 'bg-violet-50 text-violet-700' },
  CANCELLED: { label: 'Cancelado', className: 'bg-red-50 text-red-700' },
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [teams, setTeams] = useState<TeamItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', teamId: '', dueDate: '' });
  const { user } = useAuth();
  const canManage = user?.role !== 'COLABORADOR';

  const load = useCallback(async (query = search) => {
    setLoading(true);
    try {
      const [projectResponse, teamResponse] = await Promise.all([
        apiFetch<Paginated<Project>>(`/projects?limit=100${query ? `&search=${encodeURIComponent(query)}` : ''}`),
        apiFetch<Paginated<TeamItem>>('/teams?limit=100'),
      ]);
      setProjects(projectResponse.data); setTeams(teamResponse.data);
    } finally { setLoading(false); }
  }, [search]);
  useEffect(() => { void load(); }, [load]);

  async function createProject(event: React.FormEvent) {
    event.preventDefault(); setSaving(true);
    try { await apiFetch('/projects', { method: 'POST', body: JSON.stringify({ ...form, description: form.description || undefined, dueDate: form.dueDate ? new Date(form.dueDate).toISOString() : undefined }) }); setOpen(false); setForm({ name: '', description: '', teamId: '', dueDate: '' }); await load(search); }
    finally { setSaving(false); }
  }

  return <div className="space-y-6"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="relative max-w-md flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"/><Input value={search} onChange={(event) => setSearch(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void load(); }} placeholder="Buscar projetos..." className="bg-card pl-9"/></div>{canManage && <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><Button><Plus className="size-4"/> Novo projeto</Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Criar projeto</DialogTitle><DialogDescription>Defina o objetivo, equipe e prazo inicial.</DialogDescription></DialogHeader><form onSubmit={createProject} className="space-y-4"><div className="space-y-2"><Label>Nome do projeto</Label><Input value={form.name} onChange={(e) => setForm({...form, name:e.target.value})} required/></div><div className="space-y-2"><Label>Equipe</Label><select className="h-11 w-full rounded-xl border bg-background px-3 text-sm" value={form.teamId} onChange={(e) => setForm({...form, teamId:e.target.value})} required><option value="">Selecione uma equipe</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></div><div className="space-y-2"><Label>Descrição</Label><textarea className="min-h-24 w-full rounded-xl border bg-background p-3 text-sm outline-none focus:border-primary" value={form.description} onChange={(e) => setForm({...form, description:e.target.value})}/></div><div className="space-y-2"><Label>Prazo</Label><Input type="date" value={form.dueDate} onChange={(e) => setForm({...form, dueDate:e.target.value})}/></div><Button className="w-full" disabled={saving}>{saving && <LoaderCircle className="size-4 animate-spin"/>} Criar projeto</Button></form></DialogContent></Dialog>}</div>
    {loading ? <LoadingState/> : projects.length === 0 ? <EmptyState title="Nenhum projeto encontrado" description="Crie seu primeiro projeto ou ajuste os termos da busca."/> : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.map((project) => { const status = statusMap[project.status]; return <Card key={project.id} className="group transition hover:-translate-y-0.5 hover:shadow-lg"><CardContent className="p-5"><div className="mb-5 flex items-start justify-between gap-3"><div className="rounded-xl bg-primary/10 p-2.5 text-primary"><FolderKanban className="size-5"/></div><Badge className={status.className}>{status.label}</Badge></div><h3 className="text-lg font-bold tracking-tight">{project.name}</h3><p className="mt-1 line-clamp-2 min-h-10 text-sm text-muted-foreground">{project.description || 'Sem descrição cadastrada.'}</p><div className="mt-5 space-y-2.5 border-t pt-4 text-sm"><div className="flex items-center justify-between"><span className="flex items-center gap-2 text-muted-foreground"><CalendarDays className="size-4"/> Prazo</span><span className="font-medium">{formatDate(project.dueDate)}</span></div><div className="flex items-center justify-between"><span className="flex items-center gap-2 text-muted-foreground"><UserRound className="size-4"/> Responsável</span><span className="max-w-36 truncate font-medium">{project.manager?.name || 'Não definido'}</span></div><div className="flex items-center justify-between"><span className="text-muted-foreground">Tarefas</span><span className="font-bold text-primary">{project.tasksCount}</span></div></div></CardContent></Card>; })}</div>}
  </div>;
}
