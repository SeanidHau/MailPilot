export type AIProvider = 'mock' | 'openai' | 'anthropic';

export interface AIProviderConfig {
  provider: AIProvider;
  openai_api_key: string;
  openai_base_url: string;
  openai_model: string;
  anthropic_api_key: string;
  anthropic_base_url: string;
  anthropic_model: string;
}
