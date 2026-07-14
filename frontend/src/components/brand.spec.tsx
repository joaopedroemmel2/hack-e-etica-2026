import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Brand } from './brand';

describe('Brand', () => {
  it('renders the product identity', () => {
    render(<Brand />);
    expect(screen.getByText('FlowLog')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });
});
