'use client';

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DashboardData } from '@/types';

const statusLabels = { TODO: 'A fazer', IN_PROGRESS: 'Em andamento', BLOCKED: 'Bloqueadas', DONE: 'Concluídas' };
const colors = ['#5746d9', '#8b7ff0', '#ef6b73', '#55b99d'];
const shortDate = (value: string) => new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`));

export function HoursChart({ data }: { data: DashboardData['hoursChart'] }) {
  return <ResponsiveContainer width="100%" height={270}><AreaChart data={data} margin={{ top: 12, right: 10, left: -18, bottom: 0 }}><defs><linearGradient id="hours" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#5746d9" stopOpacity={0.3}/><stop offset="95%" stopColor="#5746d9" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eceef3"/><XAxis dataKey="date" tickFormatter={shortDate} axisLine={false} tickLine={false} tick={{ fill: '#8a91a1', fontSize: 11 }} minTickGap={28}/><YAxis axisLine={false} tickLine={false} tick={{ fill: '#8a91a1', fontSize: 11 }}/><Tooltip labelFormatter={(label) => shortDate(String(label))} formatter={(value) => [`${value}h`, 'Horas']} contentStyle={{ borderRadius: 12, borderColor: '#e3e6ec', fontSize: 12 }}/><Area type="monotone" dataKey="hours" stroke="#5746d9" strokeWidth={2.5} fill="url(#hours)"/></AreaChart></ResponsiveContainer>;
}

export function TaskStatusChart({ data }: { data: DashboardData['taskCharts']['byStatus'] }) {
  const formatted = data.map((item) => ({ ...item, name: statusLabels[item.status] }));
  return <div className="grid items-center gap-4 sm:grid-cols-[1fr_140px]"><ResponsiveContainer width="100%" height={220}><PieChart><Pie data={formatted} dataKey="value" nameKey="name" innerRadius={60} outerRadius={88} paddingAngle={4} stroke="none">{formatted.map((entry, index) => <Cell key={entry.status} fill={colors[index]}/>)}</Pie><Tooltip contentStyle={{ borderRadius: 12, borderColor: '#e3e6ec', fontSize: 12 }}/></PieChart></ResponsiveContainer><div className="space-y-3">{formatted.map((item, index) => <div key={item.status} className="flex items-center justify-between gap-4 text-sm"><span className="flex items-center gap-2 text-muted-foreground"><span className="size-2.5 rounded-full" style={{ background: colors[index] }}/>{item.name}</span><strong>{item.value}</strong></div>)}</div></div>;
}

export function ProductivityChart({ data }: { data: DashboardData['productivityChart'] }) {
  return <ResponsiveContainer width="100%" height={250}><BarChart data={data} margin={{ top: 10, right: 8, left: -22, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eceef3"/><XAxis dataKey="date" tickFormatter={shortDate} axisLine={false} tickLine={false} tick={{ fill: '#8a91a1', fontSize: 11 }} minTickGap={24}/><YAxis axisLine={false} tickLine={false} allowDecimals={false} tick={{ fill: '#8a91a1', fontSize: 11 }}/><Tooltip labelFormatter={(label) => shortDate(String(label))} contentStyle={{ borderRadius: 12, borderColor: '#e3e6ec', fontSize: 12 }}/><Bar dataKey="createdTasks" name="Criadas" fill="#d7d2ff" radius={[4,4,0,0]}/><Bar dataKey="completedTasks" name="Concluídas" fill="#5746d9" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer>;
}
