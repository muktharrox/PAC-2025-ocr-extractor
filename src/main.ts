import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { NestExpressApplication } from '@nestjs/platform-express';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from '@presentation/modules/app.module';
import { AppErrorFilter } from '@presentation/filters/app-error.filter';

process.env.TZ = 'UTC';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);

  app.setGlobalPrefix('api');
  app.enableCors({ origin: process.env.CORS_ORIGIN || true });
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  app.useGlobalFilters(new AppErrorFilter());

  const config = new DocumentBuilder()
    .setTitle('PAC RGP Extractor API')
    .setDescription('Extrai dados de certificados RGP (PDF/imagem) em JSON via Google Gemini')
    .setVersion('1.0')
    .addServer('/api')
    .build();
  SwaggerModule.setup('api/doc', app, SwaggerModule.createDocument(app, config));

  const port = Number(process.env.PORT) || 3001;
  await app.listen(port);
  // eslint-disable-next-line no-console
  console.log(`PAC RGP Extractor ouvindo em http://localhost:${port} (docs: /api/doc)`);
}

bootstrap();
