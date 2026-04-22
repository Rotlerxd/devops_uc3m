const API_URL = 'http://localhost:8000/api/v1';

export const getAlertNotifications = async (userId, token, alertId) => {
  const response = await fetch(
    `${API_URL}/users/${userId}/alerts/${alertId}/notifications`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) throw new Error('Error al obtener notificaciones');
  return response.json();
};

export const deleteAlertNotification = async (userId, token, alertId, notificationId) => {
  const response = await fetch(
    `${API_URL}/users/${userId}/alerts/${alertId}/notifications/${notificationId}`,
    { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) throw new Error('Error al eliminar la notificación');
  return true;
};
