import { ApiProperty } from '@nestjs/swagger';

export class RgpCertificadoDto {
  @ApiProperty({ enum: ['PF', 'PJ'] }) tipo_pessoa!: string;

  @ApiProperty({ nullable: true }) numero_processo!: string | null;
  @ApiProperty({ nullable: true }) ato_administrativo_concedente!: string | null;
  @ApiProperty({ nullable: true, example: 'SC-0004633-8' }) numero_rgp!: string | null;
  @ApiProperty({ nullable: true }) codigo_frota!: string | null;
  @ApiProperty({ nullable: true }) inscricao_autoridade_naval!: string | null;

  @ApiProperty({ nullable: true, example: 'LEALMAR' }) nome_embarcacao!: string | null;
  @ApiProperty({ nullable: true }) ano_construcao!: string | null;
  @ApiProperty({ nullable: true }) numero_tripulantes!: string | null;
  @ApiProperty({ nullable: true }) comprimento_m!: string | null;
  @ApiProperty({ nullable: true }) arqueacao_bruta!: string | null;
  @ApiProperty({ nullable: true }) potencia_motor_hp!: string | null;
  @ApiProperty({ nullable: true }) material_casco!: string | null;
  @ApiProperty({ nullable: true }) propulsao!: string | null;
  @ApiProperty({ nullable: true }) tipo_combustivel!: string | null;

  @ApiProperty({ nullable: true }) metodo!: string | null;
  @ApiProperty({ nullable: true }) petrecho!: string | null;
  @ApiProperty({ type: [String] }) especie_alvo!: string[];
  @ApiProperty({ type: [String] }) fauna_acompanhante!: string[];
  @ApiProperty({ type: [String] }) autorizacao_complementar!: string[];
  @ApiProperty({ type: [String] }) area_atuacao!: string[];

  @ApiProperty({ nullable: true }) nome!: string | null;
  @ApiProperty({ nullable: true }) cpf!: string | null;
  @ApiProperty({ nullable: true }) razao_social!: string | null;
  @ApiProperty({ nullable: true, example: '05.383.614/0001-13' }) cnpj!: string | null;
  @ApiProperty({ nullable: true }) nome_representante_legal!: string | null;
  @ApiProperty({ nullable: true }) cpf_representante_legal!: string | null;

  @ApiProperty({ nullable: true }) endereco!: string | null;
  @ApiProperty({ nullable: true }) bairro!: string | null;
  @ApiProperty({ nullable: true }) cidade_uf!: string | null;

  @ApiProperty({ nullable: true, example: '2018-11-12' }) data_inicio_validade!: string | null;
  @ApiProperty({ nullable: true, example: '2023-11-12' }) data_termino_validade!: string | null;
}

export class FieldValidationDto {
  @ApiProperty() campo!: string;
  @ApiProperty({ nullable: true }) valor!: string | null;
  @ApiProperty() valido!: boolean;
  @ApiProperty({ nullable: true }) normalizado!: string | null;
  @ApiProperty({ nullable: true }) mensagem!: string | null;
}

export class ProcessingMetaDto {
  @ApiProperty({ example: 'gemini-2.5-flash' }) model!: string;
  @ApiProperty() input_tokens!: number;
  @ApiProperty() output_tokens!: number;
  @ApiProperty() pages!: number;
  @ApiProperty() used_native_text!: boolean;
  @ApiProperty() duration_ms!: number;
}

export class ExtractResultDto {
  @ApiProperty() success!: boolean;
  @ApiProperty({ enum: ['RGP_PF', 'RGP_PJ', 'NAO_IDENTIFICADO'] }) document_type!: string;
  @ApiProperty({ type: RgpCertificadoDto }) data!: RgpCertificadoDto;
  @ApiProperty({ type: [FieldValidationDto] }) validations!: FieldValidationDto[];
  @ApiProperty({ type: [String] }) warnings!: string[];
  @ApiProperty({ type: ProcessingMetaDto }) processing!: ProcessingMetaDto;
}
