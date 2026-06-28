import { Module } from '@nestjs/common';
import { ExtractController } from './extract.controller';
import { llmProviders } from '@infrastructure/providers/llm.providers';

@Module({
  controllers: [ExtractController],
  providers: [...llmProviders],
})
export class ExtractModule {}
