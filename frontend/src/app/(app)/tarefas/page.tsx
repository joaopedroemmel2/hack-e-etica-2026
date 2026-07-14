'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CalendarDays, CheckCircle2, Circle, Clock3, LoaderCircle, Plus, Search, UserRound } from 'lucide-react';
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
import { formatDate, formatHours } from '@/lib/utils';
import type { Paginated, Project, Task, TaskPriority, TaskStatus } from '@/types';

const statuses: Array<{ value: TaskStatus; label: string }> = [
  { value: 'TODO', label: 'A fazer' }, { value: 'IN_PROGRESS', label: 'Em andamento' }, { value: 'BLOCKED', label: 'Bloqueada' }, { value: 'DONE', label: 'Concluída' },
];
const priorityMap = {
  LOW: { label: 'Baixa', className: 'bg-slate-100 text-slate-600' }, MEDIUM: { label: 'Média', className: 'bg-blue-50 text-blue-700' }, HIGH: { label: 'Alta', className: 'bg-amber-50 text-amber-700' }, URGENT: { label: 'Urgente', className: 'bg-red-50 text-red-700' },
};
const statusIcon = { TODO: Circle, IN_PROGRESS: Clock3, BLOCKED: AlertCircle, DONE: CheckCircle2 };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<TaskStatus | ''>('');
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<{ title: string; projectId: string; priority: TaskPriority; estimatedHours: string; dueDate: string }>({ title: '', projectId: '', priority: 'MEDIUM', estimatedHours: '', dueDate: '' });
  const { user } = useAuth();
  const canManage = user?.role !== 'COLABORADOR';

  const load = useCallback(async (status: TaskStatus | '' = '') => { setLoading(true); try { const [taskResponse, projectResponse] = await Promise.all([apiFetch<Paginated<Task>>(`/tasks?limit=100${status ? `&status=${status}` : ''}`), apiFetch<Paginated<Project>>('/projects?limit=100')]); setTasks(taskResponse.data); setProjects(projectResponse.data); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);

  async function updateStatus(id: string, status: TaskStatus) { await apiFetch(`/tasks/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }); setTasks((current) => current.map((task) => task.id === id ? { ...task, status } : task)); }
  async function createTask(event: React.FormEvent) { event.preventDefault(); setSaving(true); try { await apiFetch('/tasks', { method: 'POST', body: JSON.stringify({ title: form.title, projectId: form.projectId, priority: form.priority, estimatedHours: form.estimatedHours ? Number(form.estimatedHours) : undefined, dueDate: form.dueDate ? new Date(form.dueDate).toISOString() : undefined }) }); setOpen(false); setForm({ title: '', projectId: '', priority: 'MEDIUM', estimatedHours: '', dueDate: '' }); await load(filter); } finally { setSaving(false); } }
  const visibleTasks = tasks.filter((task) => task.title.toLowerCase().includes(search.toLowerCase()));

  return <div className="space-y-6"><div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between"><div className="flex flex-1 flex-col gap-3 sm:flex-row"><div className="relative max-w-md flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"/><Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar tarefas..." className="bg-card pl-9"/></div><select value={filter} onChange={(e) => { const value = e.target.value as TaskStatus | ''; setFilter(value); void load(value); }} className="h-11 rounded-xl border bg-card px-3 text-sm"><option value="">Todos os status</option>{statuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></div>{canManage && <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><Button><Plus className="size-4"/> Nova tarefa</Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Criar tarefa</DialogTitle><DialogDescription>Organize o trabalho com prioridade, prazo e estimativa.</DialogDescription></DialogHeader><form onSubmit={createTask} className="space-y-4"><div className="space-y-2"><Label>Título</Label><Input value={form.title} onChange={(e) => setForm({...form,title:e.target.value})} required/></div><div className="space-y-2"><Label>Projeto</Label><select className="h-11 w-full rounded-xl border bg-background px-3 text-sm" value={form.projectId} onChange={(e) => setForm({...form,projectId:e.target.value})} required><option value="">Selecione</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></div><div className="grid grid-cols-2 gap-3"><div className="space-y-2"><Label>Prioridade</Label><select className="h-11 w-full rounded-xl border bg-background px-3 text-sm" value={form.priority} onChange={(e) => setForm({...form,priority:e.target.value as TaskPriority})}>{Object.entries(priorityMap).map(([value,item]) => <option key={value} value={value}>{item.label}</option>)}</select></div><div className="space-y-2"><Label>Estimativa (h)</Label><Input type="number" min="0" step="0.5" value={form.estimatedHours} onChange={(e) => setForm({...form,estimatedHours:e.target.value})}/></div></div><div className="space-y-2"><Label>Prazo</Label><Input type="date" value={form.dueDate} onChange={(e) => setForm({...form,dueDate:e.target.value})}/></div><Button className="w-full" disabled={saving}>{saving && <LoaderCircle className="size-4 animate-spin"/>} Criar tarefa</Button></form></DialogContent></Dialog>}</div>
    {loading ? <LoadingState/> : visibleTasks.length === 0 ? <EmptyState title="Nenhuma tarefa encontrada" description="Ajuste seus filtros ou crie uma nova tarefa para começar."/> : <div className="space-y-3">{visibleTasks.map((task) => { const Icon = statusIcon[task.status]; const priority = priorityMap[task.priority]; const overdue = task.dueDate && new Date(task.dueDate) < new Date() && task.status !== 'DONE'; return <Card key={task.id}><CardContent className="grid gap-4 p-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center"><div className="flex min-w-0 items-start gap-3"><div className={`mt-0.5 rounded-xl p-2 ${task.status === 'DONE' ? 'bg-emerald-50 text-emerald-600' : task.status === 'BLOCKED' ? 'bg-red-50 text-red-600' : 'bg-primary/10 text-primary'}`}><Icon className="size-4"/></div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className={`font-semibold ${task.status === 'DONE' ? 'text-muted-foreground line-through' : ''}`}>{task.title}</h3><Badge className={priority.className}>{priority.label}</Badge></div><p className="mt-1 text-sm text-muted-foreground">{task.project.name}</p><div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground"><span className={overdue ? 'font-semibold text-red-600' : ''}><CalendarDays className="mr-1 inline size-3.5"/>{formatDate(task.dueDate)}</span><span><Clock3 className="mr-1 inline size-3.5"/>{formatHours(task.estimatedHours ?? 0)} estimadas</span><span><UserRound className="mr-1 inline size-3.5"/>{task.assignee?.name || 'Sem responsável'}</span></div></div></div><select value={task.status} onChange={(e) => void updateStatus(task.id, e.target.value as TaskStatus)} className="h-9 rounded-xl border bg-background px-3 text-xs font-semibold"><option value="TODO">A fazer</option><option value="IN_PROGRESS">Em andamento</option><option value="BLOCKED">Bloqueada</option><option value="DONE">Concluída</option></select></CardContent></Card>; })}</div>}
  </div>;
}
