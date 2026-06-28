import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ExtractModule } from './extract/extract.module';

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true }), ExtractModule],
})
export class AppModule {}
