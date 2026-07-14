import { LoaderCircle } from 'lucide-react';
export function LoadingState({ label = 'Carregando dados...' }: { label?: string }) { return <div className="flex min-h-64 flex-col items-center justify-center gap-3 text-muted-foreground"><LoaderCircle className="size-7 animate-spin text-primary" /><p className="text-sm">{label}</p></div>; }
