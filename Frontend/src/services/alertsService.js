const API_URL = 'http://localhost:8000/api/v1'; // Ajusta al puerto real de tu backend si no es el 8000

export const getAlerts = async (userId, token) => {
  const response = await fetch(`${API_URL}/users/${userId}/alerts`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al obtener alertas');
  return response.json();
};

export const createAlert = async (userId, token, alertData) => {
  const response = await fetch(`${API_URL}/users/${userId}/alerts`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(alertData)
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Error al crear la alerta');
  }
  return response.json();
};

export const deleteAlert = async (userId, token, alertId) => {
  const response = await fetch(`${API_URL}/users/${userId}/alerts/${alertId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Error al eliminar la alerta');
  return true;
};