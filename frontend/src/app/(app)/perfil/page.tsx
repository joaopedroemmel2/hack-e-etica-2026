'use client';

import { FormEvent, useEffect, useState } from 'react';
import { CheckCircle2, LogOut, Mail, ShieldCheck, UserRound } from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';
import { apiFetch, ApiError } from '@/lib/api';
import type { User } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const roleNames = { ADMIN: 'Administrador', GESTOR: 'Gestor', COLABORADOR: 'Colaborador' };

export default function ProfilePage() {
  const { user, logout, refreshProfile } = useAuth();
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => { if (user) setName(user.name); }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await apiFetch<User>('/users/me', { method: 'PATCH', body: JSON.stringify({ name }) });
      await refreshProfile();
      setMessage('Perfil atualizado com sucesso.');
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Não foi possível atualizar o perfil.');
    } finally { setSaving(false); }
  }

  if (!user) return null;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-primary">Minha conta</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Perfil</h1>
        <p className="mt-1 text-sm text-muted-foreground">Gerencie seus dados pessoais e consulte seu acesso.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Dados pessoais</CardTitle>
            <CardDescription>Essas informações identificam você no FlowLog AI.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={submit}>
              <div className="space-y-2">
                <Label htmlFor="name">Nome completo</Label>
                <Input id="name" value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={120} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input id="email" value={user.email} disabled />
                <p className="text-xs text-muted-foreground">O e-mail só pode ser alterado por um administrador.</p>
              </div>
              {message && <p className="flex items-center gap-2 text-sm text-emerald-600"><CheckCircle2 className="size-4" />{message}</p>}
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" disabled={saving || name.trim().length < 2}>{saving ? 'Salvando...' : 'Salvar alterações'}</Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><UserRound className="size-6" /></div>
              <CardTitle className="pt-2">{user.name}</CardTitle>
              <CardDescription className="flex items-center gap-2"><Mail className="size-4" />{user.email}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between border-t pt-4">
                <span className="flex items-center gap-2 text-sm text-muted-foreground"><ShieldCheck className="size-4" />Nível de acesso</span>
                <Badge>{roleNames[user.role]}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Capacidade semanal</span>
                <span className="text-sm font-semibold">{user.weeklyCapacityHours}h</span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-base">Sessão</CardTitle><CardDescription>Encerre o acesso neste dispositivo.</CardDescription></CardHeader>
            <CardContent><Button variant="outline" className="w-full justify-start" onClick={logout}><LogOut className="size-4" />Sair da conta</Button></CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
