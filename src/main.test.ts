import { describe, expect, it } from 'vitest';
import { makePreview } from './runtime';

describe('Mock Stateful Runtime preview', () => {
  it('changes the preview as the runtime advances', () => {
    expect(makePreview(1, 42, false)).not.toBe(makePreview(2, 42, false));
  });

  it('marks a rejected local solution in the preview', () => {
    expect(makePreview(1, 42, true)).toContain('f06b5d');
  });
});
