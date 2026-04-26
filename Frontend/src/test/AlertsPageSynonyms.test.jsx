import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AlertsPage from '../pages/AlertsPage';
import { generateSynonyms, getAlerts } from '../services/alertsService';
import { getCategories } from '../services/sourcesService';

vi.mock('../services/alertsService', () => ({
  getAlerts: vi.fn(),
  createAlert: vi.fn(),
  deleteAlert: vi.fn(),
  generateSynonyms: vi.fn()
}));

vi.mock('../services/sourcesService', () => ({
  getCategories: vi.fn()
}));

describe('AlertsPage synonym generation', () => {
  beforeEach(() => {
    const storage = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: (key) => storage[key] || null,
        setItem: (key, value) => {
          storage[key] = String(value);
        },
        removeItem: (key) => {
          delete storage[key];
        },
        clear: () => {
          Object.keys(storage).forEach((key) => {
            delete storage[key];
          });
        }
      },
      configurable: true
    });
    window.localStorage.setItem('token', 'token-test');
    window.localStorage.setItem('userId', '42');
    vi.clearAllMocks();
    getAlerts.mockResolvedValue([]);
    getCategories.mockResolvedValue([]);
  });

  const openModal = async () => {
    render(
      <MemoryRouter>
        <AlertsPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /\+ nueva alerta/i }));
    await waitFor(() => {
      expect(screen.getByText(/crear nueva alerta/i)).toBeInTheDocument();
    });
  };

  it('generates suggestions for each descriptor and appends selected synonym', async () => {
    generateSynonyms
      .mockResolvedValueOnce({ term: 'ia', language: 'spa', limit: 10, synonyms: ['inteligencia artificial'] })
      .mockResolvedValueOnce({ term: 'coche', language: 'spa', limit: 10, synonyms: ['auto'] });

    await openModal();

    const descriptorsInput = screen.getByPlaceholderText(/ia, robótica, chips/i);
    fireEvent.change(descriptorsInput, { target: { value: 'ia, coche' } });
    fireEvent.click(screen.getByRole('button', { name: /generar sinónimos/i }));

    await waitFor(() => {
      expect(generateSynonyms).toHaveBeenCalledTimes(2);
    });

    expect(generateSynonyms).toHaveBeenNthCalledWith(1, 'token-test', 'ia', 10);
    expect(generateSynonyms).toHaveBeenNthCalledWith(2, 'token-test', 'coche', 10);
    expect(descriptorsInput).toHaveValue('ia, coche');

    fireEvent.click(screen.getByRole('button', { name: 'auto' }));
    expect(descriptorsInput).toHaveValue('ia, coche, auto');
  });

  it('prevents adding extra descriptor by suggestion when max limit is reached', async () => {
    generateSynonyms.mockImplementation(async (_, term) => ({
      term,
      language: 'spa',
      limit: 10,
      synonyms: [`${term}-syn`]
    }));

    await openModal();

    const descriptorsInput = screen.getByPlaceholderText(/ia, robótica, chips/i);
    const tenDescriptors = 'a,b,c,d,e,f,g,h,i,j';
    fireEvent.change(descriptorsInput, { target: { value: tenDescriptors } });
    fireEvent.click(screen.getByRole('button', { name: /generar sinónimos/i }));

    await waitFor(() => {
      expect(generateSynonyms).toHaveBeenCalledTimes(10);
    });

    fireEvent.click(screen.getByRole('button', { name: 'a-syn' }));
    expect(screen.getByText(/ya tienes 10 descriptores/i)).toBeInTheDocument();
    expect(descriptorsInput).toHaveValue(tenDescriptors);
  });
});
