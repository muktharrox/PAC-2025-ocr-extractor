import { validateRgp } from '../rgp';

describe('validateRgp', () => {
  it('aceita RGPs válidos no formato estrito', () => {
    expect(validateRgp('SC-0001300-7')).toEqual({ valid: true, normalized: 'SC-0001300-7', messages: [] });
    expect(validateRgp('SC-0004006-8').valid).toBe(true);
    expect(validateRgp('SC-0004633-8').valid).toBe(true);
  });

  it('normaliza formato divergente e sinaliza por mensagem', () => {
    const r = validateRgp('sc 0004633 8');
    expect(r.valid).toBe(true);
    expect(r.normalized).toBe('SC-0004633-8');
    expect(r.messages.length).toBeGreaterThan(0);
  });

  it('rejeita UF inexistente', () => {
    expect(validateRgp('ZZ-0000000-0').valid).toBe(false);
  });

  it('rejeita quando colado a outros caracteres (guard de lookbehind)', () => {
    expect(validateRgp('ABSC-0004633-8').valid).toBe(false);
  });

  it('rejeita vazio', () => {
    expect(validateRgp('').valid).toBe(false);
    expect(validateRgp(null).valid).toBe(false);
  });
});
