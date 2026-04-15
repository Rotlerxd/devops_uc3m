const API_URL = 'http://localhost:8000/api/v1';

// --- FUNCIONES DE FUENTES ---
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
  if (!response.ok) throw new Error('Error al eliminar la fuente');
  return true;
};

// --- FUNCIONES DE CATEGORÍAS Y CANALES RSS ---
export const getCategories = async (token) => {
  const response = await fetch(`${API_URL}/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener las categorías');
  return response.json();
};

export const getChannels = async (token, sourceId) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}/rss-channels`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error(`Error al obtener canales de la fuente ${sourceId}`);
  return response.json();
};

export const createChannel = async (token, sourceId, channelData) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}/rss-channels`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(channelData)
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Error al crear el canal RSS');
  }
  return response.json();
};

export const deleteChannel = async (token, sourceId, channelId) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}/rss-channels/${channelId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al eliminar el canal RSS');
  return true;
};