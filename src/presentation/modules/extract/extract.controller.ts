import {
  BadRequestException,
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiBody, ApiConsumes, ApiOkResponse, ApiOperation, ApiResponse, ApiTags } from '@nestjs/swagger';
import { ExtractRgpUseCase } from '@application/usecases/extract-rgp.usecase';
import { ExtractRgpDto } from '@presentation/dtos/extract-rgp.dto';
import { ExtractResultDto } from '@presentation/dtos/extract-result.dto';

// Aceita os tipos conhecidos e octet-stream (enviado por curl/axios/PowerShell).
// A validação definitiva é feita por assinatura de bytes no use case (415 se não bater).
const ALLOWED_MIMETYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/webp',
  'application/octet-stream',
];

@ApiTags('Extract')
@Controller('v1')
export class ExtractController {
  constructor(private readonly extractRgp: ExtractRgpUseCase) {}

  @Get('health')
  @ApiOperation({ summary: 'Healthcheck do serviço' })
  health() {
    return { status: 'ok', service: 'pac-rgp-extractor' };
  }

  @Post('extract')
  @HttpCode(HttpStatus.OK)
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 50 * 1024 * 1024 } }))
  @ApiConsumes('multipart/form-data')
  @ApiBody({ type: ExtractRgpDto })
  @ApiOperation({
    summary: 'Extrai dados de um certificado RGP (PDF/imagem) em JSON via Google Gemini',
  })
  @ApiOkResponse({ type: ExtractResultDto })
  @ApiResponse({ status: 400, description: 'Arquivo ausente ou vazio' })
  @ApiResponse({ status: 413, description: 'Arquivo maior que o limite' })
  @ApiResponse({ status: 415, description: 'Formato não suportado' })
  @ApiResponse({ status: 422, description: 'Falha ao estruturar o documento' })
  async extract(@UploadedFile() file: Express.Multer.File): Promise<ExtractResultDto> {
    if (!file) throw new BadRequestException('Campo "file" é obrigatório (multipart/form-data)');
    if (!ALLOWED_MIMETYPES.includes(file.mimetype)) {
      throw new BadRequestException(`Mimetype não suportado: ${file.mimetype}. Use PDF, PNG, JPEG ou WEBP.`);
    }
    return this.extractRgp.execute({ buffer: file.buffer, filename: file.originalname }) as Promise<ExtractResultDto>;
  }
}
