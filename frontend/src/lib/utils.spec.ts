import { describe, expect, it } from 'vitest';

import { formatDate, formatHours } from './utils';

describe('formatters', () => {
  it('formats hours for the Portuguese interface', () => {
    expect(formatHours(8.5)).toBe('8,5h');
  });

  it('returns a fallback for an absent date', () => {
    expect(formatDate(null)).toBe('Sem prazo');
  });
});
