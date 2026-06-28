import { validateCnpj } from '../cnpj';

describe('validateCnpj', () => {
  it('aceita CNPJ válido (Lealmar) e retorna mascarado', () => {
    expect(validateCnpj('05383614000113')).toEqual({
      valid: true,
      normalized: '05.383.614/0001-13',
      messages: [],
    });
    expect(validateCnpj('05.383.614/0001-13').valid).toBe(true);
  });

  it('rejeita dígitos verificadores inválidos', () => {
    expect(validateCnpj('05.383.614/0001-99').valid).toBe(false);
  });

  it('rejeita todos os dígitos iguais', () => {
    expect(validateCnpj('11.111.111/1111-11').valid).toBe(false);
  });

  it('rejeita comprimento incorreto', () => {
    expect(validateCnpj('1234').valid).toBe(false);
  });

  it('rejeita vazio/nulo', () => {
    expect(validateCnpj('').valid).toBe(false);
    expect(validateCnpj(null).valid).toBe(false);
  });
});
