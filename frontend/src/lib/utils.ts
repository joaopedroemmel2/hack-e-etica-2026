import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatHours(value: number) {
  return `${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(value)}h`;
}

export function formatDate(value?: string | null) {
  if (!value) return 'Sem prazo';
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }).format(
    new Date(value),
  );
}
