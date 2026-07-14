'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, BarChart3, CheckCircle2, Eye, EyeOff, LoaderCircle, ShieldCheck } from 'lucide-react';
import { Brand } from '@/components/brand';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/auth-context';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const { login, user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => { if (!loading && user) router.replace('/dashboard'); }, [loading, user, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault(); setSubmitting(true); setError('');
    try { await login(email, password); router.replace('/dashboard'); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Não foi possível entrar.'); }
    finally { setSubmitting(false); }
  }

  return <main className="grid min-h-screen lg:grid-cols-[1.05fr_.95fr]">
    <section className="subtle-grid relative hidden overflow-hidden bg-[#17152d] p-12 text-white lg:flex lg:flex-col lg:justify-between">
      <div className="absolute -right-32 -top-32 size-96 rounded-full bg-primary/30 blur-3xl" />
      <Brand className="relative [&_p]:text-white [&_p:last-child]:text-white/50" />
      <div className="relative max-w-xl"><p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-violet-200"><BarChart3 className="size-3.5" /> Clareza operacional em tempo real</p><h1 className="text-5xl font-bold leading-[1.08] tracking-tight">Equipes saudáveis.<br/><span className="text-violet-300">Resultados previsíveis.</span></h1><p className="mt-6 max-w-lg text-lg leading-8 text-white/60">Transforme dados de projetos, tarefas e horas em decisões melhores — antes que a sobrecarga vire atraso.</p><div className="mt-10 grid gap-4 sm:grid-cols-2">{['Carga de trabalho equilibrada','Insights acionáveis com IA','Projetos sob controle','Indicadores em um só lugar'].map((item) => <div key={item} className="flex items-center gap-3 text-sm text-white/80"><CheckCircle2 className="size-4 text-violet-300" />{item}</div>)}</div></div>
      <p className="relative text-xs text-white/35">FlowLog AI · Gestão operacional inteligente</p>
    </section>
    <section className="flex items-center justify-center bg-background px-6 py-12"><div className="w-full max-w-md"><Brand className="mb-12 lg:hidden"/><div className="mb-8"><div className="mb-5 flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary"><ShieldCheck className="size-5" /></div><h2 className="text-3xl font-bold tracking-tight">Bem-vindo de volta</h2><p className="mt-2 text-muted-foreground">Acesse sua área de trabalho para continuar.</p></div><form onSubmit={handleSubmit} className="space-y-5"><div className="space-y-2"><Label htmlFor="email">E-mail corporativo</Label><Input id="email" type="email" placeholder="voce@empresa.com" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" /></div><div className="space-y-2"><div className="flex justify-between"><Label htmlFor="password">Senha</Label></div><div className="relative"><Input id="password" type={showPassword ? 'text' : 'password'} placeholder="Sua senha" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" className="pr-11"/><button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Mostrar senha">{showPassword ? <EyeOff className="size-4"/> : <Eye className="size-4"/>}</button></div></div>{error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}<Button type="submit" size="lg" className="w-full" disabled={submitting}>{submitting ? <LoaderCircle className="size-4 animate-spin"/> : <>Entrar na plataforma <ArrowRight className="size-4"/></>}</Button></form><p className="mt-8 text-center text-xs leading-5 text-muted-foreground">Ao entrar, você concorda com as políticas de segurança e privacidade da sua organização.</p></div></section>
  </main>;
}
