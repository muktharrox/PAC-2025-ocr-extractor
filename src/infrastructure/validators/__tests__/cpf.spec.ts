import { validateCpf } from '../cpf';

describe('validateCpf', () => {
  it('aceita CPFs válidos e retorna mascarado', () => {
    expect(validateCpf('52998224725')).toEqual({ valid: true, normalized: '529.982.247-25', messages: [] });
    expect(validateCpf('590.660.679-34').valid).toBe(true);
    expect(validateCpf('019.256.729-21').valid).toBe(true);
  });

  it('rejeita dígitos verificadores inválidos', () => {
    expect(validateCpf('529.982.247-24').valid).toBe(false);
  });

  it('rejeita todos os dígitos iguais', () => {
    expect(validateCpf('111.111.111-11').valid).toBe(false);
  });

  it('rejeita comprimento incorreto', () => {
    expect(validateCpf('123').valid).toBe(false);
  });

  it('rejeita vazio/nulo', () => {
    expect(validateCpf('').valid).toBe(false);
    expect(validateCpf(null).valid).toBe(false);
    expect(validateCpf(undefined).valid).toBe(false);
  });
});
