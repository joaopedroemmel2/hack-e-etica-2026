'use client';

import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock3, FolderKanban, RefreshCw, UsersRound } from 'lucide-react';
import { HoursChart, ProductivityChart, TaskStatusChart } from '@/components/dashboard-charts';
import { LoadingState } from '@/components/loading-state';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { apiFetch } from '@/lib/api';
import { formatHours } from '@/lib/utils';
import type { DashboardData } from '@/types';

const metrics = [
  { key: 'activeProjects', label: 'Projetos ativos', icon: FolderKanban, tone: 'bg-violet-50 text-violet-600', suffix: '' },
  { key: 'overdueTasks', label: 'Tarefas atrasadas', icon: AlertTriangle, tone: 'bg-red-50 text-red-600', suffix: '' },
  { key: 'completionPercentage', label: 'Taxa de conclusão', icon: CheckCircle2, tone: 'bg-emerald-50 text-emerald-600', suffix: '%' },
  { key: 'loggedHours', label: 'Horas registradas', icon: Clock3, tone: 'bg-blue-50 text-blue-600', suffix: 'h' },
] as const;

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function load() { setLoading(true); setError(''); try { setData(await apiFetch<DashboardData>('/dashboard')); } catch (reason) { setError(reason instanceof Error ? reason.message : 'Falha ao carregar dashboard.'); } finally { setLoading(false); } }
  useEffect(() => { void load(); }, []);
  if (loading) return <LoadingState label="Calculando indicadores..."/>;
  if (error || !data) return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700"><p className="font-semibold">Não foi possível carregar o dashboard</p><p className="mt-1 text-sm">{error}</p><Button variant="outline" className="mt-4" onClick={() => void load()}><RefreshCw className="size-4"/> Tentar novamente</Button></div>;

  return <div className="space-y-6"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(({ key, label, icon: Icon, tone, suffix }) => <Card key={key}><CardContent className="flex items-center justify-between p-5"><div><p className="text-sm text-muted-foreground">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight">{data.summary[key]}{suffix}</p></div><div className={`rounded-2xl p-3 ${tone}`}><Icon className="size-5"/></div></CardContent></Card>)}</div>
    <div className="grid gap-6 xl:grid-cols-[1.55fr_1fr]"><Card><CardHeader className="flex-row items-start justify-between"><div><CardTitle>Horas registradas</CardTitle><CardDescription>Evolução diária nos últimos 30 dias</CardDescription></div><Activity className="size-5 text-primary"/></CardHeader><CardContent><HoursChart data={data.hoursChart}/></CardContent></Card><Card><CardHeader><CardTitle>Fluxo das tarefas</CardTitle><CardDescription>Distribuição atual por status</CardDescription></CardHeader><CardContent><TaskStatusChart data={data.taskCharts.byStatus}/></CardContent></Card></div>
    <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]"><Card><CardHeader><CardTitle>Produtividade</CardTitle><CardDescription>Tarefas criadas versus concluídas por dia</CardDescription></CardHeader><CardContent><ProductivityChart data={data.productivityChart}/></CardContent></Card><Card><CardHeader className="flex-row items-center justify-between"><div><CardTitle>Capacidade da equipe</CardTitle><CardDescription>{data.summary.overloadedUsers} pessoa(s) acima do limite</CardDescription></div><UsersRound className="size-5 text-primary"/></CardHeader><CardContent className="space-y-5">{data.workload.slice(0, 6).map((item) => <div key={item.user.id}><div className="mb-2 flex items-end justify-between gap-3"><div><p className="text-sm font-semibold">{item.user.name}</p><p className="text-xs text-muted-foreground">{formatHours(item.committedHours)} de {formatHours(item.capacityHours)}</p></div><span className={`text-sm font-bold ${item.overloaded ? 'text-red-600' : 'text-foreground'}`}>{item.utilizationPercentage}%</span></div><Progress value={item.utilizationPercentage} className={item.overloaded ? '[&>div]:bg-red-500' : ''}/></div>)}{data.workload.length === 0 && <p className="py-8 text-center text-sm text-muted-foreground">Nenhum dado de capacidade disponível.</p>}</CardContent></Card></div>
  </div>;
}
