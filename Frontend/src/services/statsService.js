const API_URL = 'http://localhost:8000/api/v1';

export const getGlobalStats = async (token) => {
  const response = await fetch(`${API_URL}/stats/global`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al cargar estadísticas');
  return response.json();
};

export const getCategoryDistribution = async (token) => {
  const response = await fetch(`${API_URL}/stats/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.json();
};