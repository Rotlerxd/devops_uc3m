import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAlerts } from '../services/alertsService';
import { getAlertNotifications, deleteAlertNotification } from '../services/notificationsService';

export default function NotificationsPage() {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');

  const [alerts, setAlerts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [filterCategory, setFilterCategory] = useState('');
  const [filterAlertId, setFilterAlertId] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 60000); // refresco cada 60s
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const userAlerts = await getAlerts(userId, token);
      setAlerts(userAlerts);

      const results = await Promise.all(
        userAlerts.map(async (alert) => {
          try {
            const notifs = await getAlertNotifications(userId, token, alert.id);
            return notifs.map((n) => ({ ...n, alertName: alert.name }));
          } catch {
            return [];
          }
        })
      );
      const flat = results.flat().sort(
        (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
      );
      setNotifications(flat);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (alertId, notificationId) => {
    if (!window.confirm('¿Eliminar esta notificación del buzón?')) return;
    try {
      await deleteAlertNotification(userId, token, alertId, notificationId);
      fetchAll();
    } catch (err) {
      setError(err.message);
    }
  };

  const uniqueCategories = Array.from(
    new Set(notifications.map((n) => n.iptc_category).filter(Boolean))
  );

  const filtered = notifications.filter((n) => {
    if (filterCategory && n.iptc_category !== filterCategory) return false;
    if (filterAlertId && String(n.alert_id) !== String(filterAlertId)) return false;
    return true;
  });

  const formatDate = (ts) => {
    try {
      return new Date(ts).toLocaleString('es-ES');
    } catch {
      return ts;
    }
  };

  const getMatches = (metrics) => {
    if (!Array.isArray(metrics)) return 0;
    const hit = metrics.find((m) => m.name === 'noticias_encontradas');
    return hit ? hit.value : 0;
  };

  return (
    <div className="container mt-4">
      {/* Navegación entre secciones */}
      <ul className="nav nav-pills mb-4">
        <li className="nav-item"><Link className="nav-link" to="/alertas">Alertas</Link></li>
        <li className="nav-item"><Link className="nav-link" to="/fuentes">Fuentes</Link></li>
        <li className="nav-item"><Link className="nav-link active" to="/buzon">Buzón</Link></li>
      </ul>

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-1">Buzón de Avisos</h2>
          <small className="text-muted">
            Notificaciones generadas automáticamente por el motor RSS al detectar
            coincidencias con tus alertas. También recibes un correo con cada aviso.
          </small>
        </div>
        <button className="btn btn-outline-dark" onClick={fetchAll} disabled={loading}>
          {loading ? 'Actualizando…' : '↻ Refrescar'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Filtros */}
      <div className="card shadow-sm mb-3">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-5">
              <label className="form-label mb-1">Filtrar por alerta</label>
              <select
                className="form-select"
                value={filterAlertId}
                onChange={(e) => setFilterAlertId(e.target.value)}
              >
                <option value="">Todas las alertas</option>
                {alerts.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div className="col-md-5">
              <label className="form-label mb-1">Filtrar por categoría IPTC</label>
              <select
                className="form-select"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
              >
                <option value="">Todas las categorías</option>
                {uniqueCategories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="col-md-2 d-flex align-items-end">
              <button
                className="btn btn-outline-secondary w-100"
                onClick={() => { setFilterAlertId(''); setFilterCategory(''); }}
              >
                Limpiar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Lista */}
      <div className="card shadow-sm">
        <div className="card-body p-0">
          <table className="table table-hover mb-0">
            <thead className="table-dark">
              <tr>
                <th>FECHA</th>
                <th>ALERTA</th>
                <th>CATEGORÍA IPTC</th>
                <th>COINCIDENCIAS</th>
                <th>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="5" className="text-center py-4 text-muted">
                    {loading ? 'Cargando…' : 'No hay notificaciones en el buzón.'}
                  </td>
                </tr>
              ) : (
                filtered.map((n) => (
                  <tr key={`${n.alert_id}-${n.id}`}>
                    <td className="align-middle">{formatDate(n.timestamp)}</td>
                    <td className="align-middle fw-bold">{n.alertName}</td>
                    <td className="align-middle">
                      <span className="badge bg-info text-dark">
                        {n.iptc_category || 'General'}
                      </span>
                    </td>
                    <td className="align-middle">
                      <span className="badge bg-success">{getMatches(n.metrics)}</span>
                    </td>
                    <td className="align-middle">
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => handleDelete(n.alert_id, n.id)}
                      >
                        Borrar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
