import { ApiProperty } from '@nestjs/swagger';

/** DTO apenas para documentação Swagger do upload multipart. */
export class ExtractRgpDto {
  @ApiProperty({
    type: 'string',
    format: 'binary',
    description: 'Certificado RGP (PDF, PNG, JPG ou WEBP)',
  })
  file!: any;
}
