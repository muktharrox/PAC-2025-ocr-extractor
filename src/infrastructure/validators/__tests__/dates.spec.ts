import { validateDate, validateRange } from '../dates';

describe('validateDate', () => {
  it('converte dd/mm/aaaa para ISO', () => {
    expect(validateDate('22/04/2020')).toEqual({ valid: true, normalized: '2020-04-22', messages: [] });
    expect(validateDate('01/01/2020').normalized).toBe('2020-01-01');
    expect(validateDate('12/11/2018').normalized).toBe('2018-11-12');
  });

  it('aceita ISO já formatado', () => {
    expect(validateDate('2023-11-12').normalized).toBe('2023-11-12');
  });

  it('rejeita data inexistente', () => {
    expect(validateDate('31/02/2020').valid).toBe(false);
  });

  it('rejeita ano fora da faixa', () => {
    expect(validateDate('01/01/1800').valid).toBe(false);
  });

  it('rejeita formato desconhecido / vazio', () => {
    expect(validateDate('ontem').valid).toBe(false);
    expect(validateDate('').valid).toBe(false);
  });
});

describe('validateRange', () => {
  it('aceita início <= fim', () => {
    expect(validateRange('2018-11-12', '2023-11-12').valid).toBe(true);
  });

  it('rejeita início > fim', () => {
    expect(validateRange('2025-01-01', '2020-01-01').valid).toBe(false);
  });

  it('ignora quando falta uma das datas', () => {
    expect(validateRange(null, '2023-11-12').valid).toBe(true);
    expect(validateRange('2018-11-12', null).valid).toBe(true);
  });
});
