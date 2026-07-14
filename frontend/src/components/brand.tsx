import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Brand({ compact = false, className }: { compact?: boolean; className?: string }) {
  return <div className={cn('flex items-center gap-3', className)}><div className="flex size-10 items-center justify-center rounded-xl bg-primary text-white shadow-lg shadow-primary/20"><Sparkles className="size-5" /></div>{!compact && <div><p className="text-lg font-bold leading-none tracking-tight">FlowLog <span className="text-primary">AI</span></p><p className="mt-1 text-[10px] font-semibold uppercase tracking-[.18em] text-muted-foreground">Work smarter</p></div>}</div>;
}
