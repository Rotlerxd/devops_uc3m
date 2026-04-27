import { afterEach, describe, expect, it, vi } from 'vitest';
import { generateSynonyms, warmupSynonyms } from '../services/alertsService';

describe('alertsService', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('requests Spanish synonyms with the configured limit', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ term: 'coche', language: 'spa', limit: 3, synonyms: ['auto', 'carro', 'vehiculo'] })
    });

    const result = await generateSynonyms('token-123', 'coche', 3);

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/alerts/synonyms?term=coche&limit=3',
      { headers: { Authorization: 'Bearer token-123' } }
    );
    expect(result.synonyms).toEqual(['auto', 'carro', 'vehiculo']);
  });

  it('raises the backend error message when synonym generation fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No disponible' })
    });

    await expect(generateSynonyms('token-123', 'x', 3)).rejects.toThrow('No disponible');
  });

  it('calls synonym warmup endpoint with auth header', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'warmed' })
    });

    const result = await warmupSynonyms('token-123');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/alerts/synonyms/warmup',
      { headers: { Authorization: 'Bearer token-123' } }
    );
    expect(result.status).toBe('warmed');
  });
});
