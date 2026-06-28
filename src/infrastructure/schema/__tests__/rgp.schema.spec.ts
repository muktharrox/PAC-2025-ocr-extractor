import { parseRgp, RGPSchema } from '../rgp.schema';

describe('RGPSchema (parse defensivo)', () => {
  it('aplica defaults para objeto vazio', () => {
    const r = parseRgp({});
    expect(r.tipo_pessoa).toBe('PF');
    expect(r.numero_rgp).toBeNull();
    expect(r.especie_alvo).toEqual([]);
    expect(r.fauna_acompanhante).toEqual([]);
  });

  it('coage string única para array', () => {
    const r = parseRgp({ especie_alvo: 'Tainha' });
    expect(r.especie_alvo).toEqual(['Tainha']);
  });

  it('normaliza tipo_pessoa em minúsculas e cai no default para inválido', () => {
    expect(parseRgp({ tipo_pessoa: 'pj' }).tipo_pessoa).toBe('PJ');
    expect(parseRgp({ tipo_pessoa: 'X' }).tipo_pessoa).toBe('PF');
  });

  it('transforma string vazia/espaços em null', () => {
    expect(parseRgp({ numero_rgp: '   ' }).numero_rgp).toBeNull();
    expect(parseRgp({ nome: ' Fulano ' }).nome).toBe('Fulano');
  });

  it('nunca lança, mesmo com entrada não-objeto', () => {
    expect(() => parseRgp(null)).not.toThrow();
    expect(() => parseRgp('lixo')).not.toThrow();
    expect(RGPSchema.parse({}).tipo_pessoa).toBe('PF');
  });
});
