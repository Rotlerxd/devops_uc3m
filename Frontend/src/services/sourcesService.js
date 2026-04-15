const API_URL = 'http://localhost:8000/api/v1';

export const getSources = async (token) => {
  const response = await fetch(`${API_URL}/information-sources`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener las fuentes');
  return response.json();
};

export const createSource = async (token, sourceData) => {
  const response = await fetch(`${API_URL}/information-sources`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(sourceData)
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Error al crear la fuente');
  }
  return response.json();
};

export const deleteSource = async (token, sourceId) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al eliminar la fuente (puede que tenga canales RSS asociados)');
  return true;
};