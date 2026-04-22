const API_URL = 'http://localhost:8000/api/v1';

export const getCategories = async (token) => {
  const response = await fetch(`${API_URL}/categories`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener categorías');
  return response.json();
};

export const getRssChannels = async (token, sourceId) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}/rss-channels`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener los canales RSS');
  return response.json();
};

export const createRssChannel = async (token, sourceId, channelData) => {
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

export const deleteRssChannel = async (token, sourceId, channelId) => {
  const response = await fetch(`${API_URL}/information-sources/${sourceId}/rss-channels/${channelId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al eliminar el canal RSS');
  return true;
};