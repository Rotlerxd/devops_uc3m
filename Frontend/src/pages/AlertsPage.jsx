import React, { useState, useEffect } from 'react';
import { getAlerts, createAlert, deleteAlert } from '../services/alertsService';

export default function AlertsPage() {
  // Leer credenciales reales del Login
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');

  // Creamos un objeto user "virtual" para no romper el resto del código que ya escribimos
  const user = { id: userId };  
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  // Estado del formulario
  const [formData, setFormData] = useState({
    name: '',
    descriptors: '',
    cron_expression: '0 0 * * *', // Valor por defecto
    categories: []
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const data = await getAlerts(user.id, token);
      setAlerts(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);

    // Parsear descriptores separados por coma
    const parsedDescriptors = formData.descriptors
      .split(',')
      .map(d => d.trim())
      .filter(d => d !== '');

    // Validación del Frontend
    if (alerts.length >= 20) {
      return setError('Límite máximo de 20 alertas alcanzado.');
    }
    if (parsedDescriptors.length < 3 || parsedDescriptors.length > 10) {
      return setError('Debes incluir entre 3 y 10 descriptores separados por coma.');
    }

    try {
      await createAlert(user.id, token, {
        ...formData,
        descriptors: parsedDescriptors,
        categories: [{ code: 'ECON', label: 'Economía' }] 
      });
      setShowModal(false);
      setFormData({ name: '', descriptors: '', cron_expression: '0 0 * * *', categories: [] });
      fetchAlerts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (alertId) => {
    if (!window.confirm('¿Seguro que quieres eliminar esta alerta?')) return;
    try {
      await deleteAlert(user.id, token, alertId);
      fetchAlerts();
    } catch (err) {
      setError(err.message);
    }
  };

  const openModal = () => {
    setError(null);
    setShowModal(true);
  };

  const closeModal = () => {
    setError(null);
    setShowModal(false);
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Gestión de Alertas</h2>
        <button className="btn btn-dark" onClick={openModal}>
          + NUEVA ALERTA
        </button>
      </div>

      {/* Error general de la página (ej. fallo al cargar) */}
      {error && !showModal && <div className="alert alert-danger">{error}</div>}

      {/* Tabla de Alertas */}
      <div className="card shadow-sm">
        <div className="card-body p-0">
          <table className="table table-hover mb-0">
            <thead className="table-dark">
              <tr>
                <th>NOMBRE DE LA ALERTA</th>
                <th>DESCRIPTORES</th>
                <th>PERIODICIDAD</th>
                <th>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr><td colSpan="4" className="text-center py-4">No hay alertas configuradas.</td></tr>
              ) : (
                alerts.map(alert => (
                  <tr key={alert.id}>
                    <td className="align-middle fw-bold">{alert.name}</td>
                    <td className="align-middle">
                      {alert.descriptors.map(d => (
                        <span key={d} className="badge bg-secondary me-1">{d}</span>
                      ))}
                    </td>
                    <td className="align-middle">{alert.cron_expression}</td>
                    <td className="align-middle">
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(alert.id)}>
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

      {/* Modal de Bootstrap (Estilo simplificado para React) */}
      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">CREAR NUEVA ALERTA</h5>
                <button type="button" className="btn-close btn-close-white" onClick={closeModal}></button>
              </div>
              <div className="modal-body">
                
                {/* AQUI ESTÁ EL ERROR DENTRO DEL MODAL */}
                {error && <div className="alert alert-danger">{error}</div>}
                
                <form onSubmit={handleCreate}>
                  <div className="mb-3">
                    <label className="form-label">NOMBRE DE LA ALERTA</label>
                    <input 
                      type="text" 
                      className="form-control bg-light" 
                      placeholder="EJ: TENDENCIAS TECH 2026"
                      value={formData.name}
                      onChange={e => setFormData({...formData, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">DESCRIPTORES (SEPARADOS POR COMA)</label>
                      <input 
                        type="text" 
                        className="form-control bg-light" 
                        placeholder="IA, ROBÓTICA, CHIPS"
                        value={formData.descriptors}
                        onChange={e => setFormData({...formData, descriptors: e.target.value})}
                        required
                      />
                      <small className="text-muted">Introduce entre 3 y 10 palabras.</small>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">PERIODICIDAD (CRON)</label>
                      <input 
                        type="text" 
                        className="form-control bg-light" 
                        value={formData.cron_expression}
                        onChange={e => setFormData({...formData, cron_expression: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <div className="d-flex justify-content-end gap-2 mt-4">
                    <button type="button" className="btn btn-outline-secondary" onClick={closeModal}>
                      CANCELAR
                    </button>
                    <button type="submit" className="btn btn-dark">
                      GUARDAR ALERTA
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}