import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAlerts, createAlert, deleteAlert, generateSynonyms } from '../services/alertsService';
import { getCategories } from '../services/sourcesService';

// Presets comunes de expresión cron para el motor de captura RSS (Sprint 3.1)
const CRON_PRESETS = [
  { label: 'Cada 15 minutos', value: '*/15 * * * *' },
  { label: 'Cada 30 minutos', value: '*/30 * * * *' },
  { label: 'Cada hora',       value: '0 * * * *'   },
  { label: 'Cada 6 horas',    value: '0 */6 * * *' },
  { label: 'Diario (00:00)',  value: '0 0 * * *'   },
  { label: 'Personalizado',   value: 'custom'      },
];

export default function AlertsPage() {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');
  const user = { id: userId };

  const [alerts, setAlerts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [synonymLoading, setSynonymLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    descriptors: '',
    cron_preset: '0 0 * * *',
    cron_expression: '0 0 * * *',
    category_ids: [],
  });

  const fetchAlerts = async () => {
    try {
      const data = await getAlerts(user.id, token);
      setAlerts(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await getCategories(token);
      setCategories(data);
    } catch {
      // no rompemos la página si falla
    }
  };

  useEffect(() => {
    fetchAlerts();
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handlePresetChange = (value) => {
    if (value === 'custom') {
      setFormData({ ...formData, cron_preset: 'custom' });
    } else {
      setFormData({ ...formData, cron_preset: value, cron_expression: value });
    }
  };

  const toggleCategory = (cat) => {
    const exists = formData.category_ids.includes(cat.id);
    const nextIds = exists
      ? formData.category_ids.filter((id) => id !== cat.id)
      : [...formData.category_ids, cat.id];
    setFormData({ ...formData, category_ids: nextIds });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);

    const parsedDescriptors = formData.descriptors
      .split(',')
      .map((d) => d.trim())
      .filter((d) => d !== '');

    if (alerts.length >= 20) {
      return setError('Límite máximo de 20 alertas alcanzado.');
    }
    if (parsedDescriptors.length < 3 || parsedDescriptors.length > 10) {
      return setError('Debes incluir entre 3 y 10 descriptores separados por coma.');
    }
    if (!formData.cron_expression.trim()) {
      return setError('Debes especificar una expresión cron.');
    }

    // Construimos las categorías IPTC seleccionadas (con code + label)
    const selectedCategories = categories
      .filter((c) => formData.category_ids.includes(c.id))
      .map((c) => ({ code: c.source || 'IPTC', label: c.name }));

    const payloadCategories = selectedCategories.length > 0
      ? selectedCategories
      : [{ code: 'IPTC', label: 'General' }];

    try {
      await createAlert(user.id, token, {
        name: formData.name,
        descriptors: parsedDescriptors,
        cron_expression: formData.cron_expression,
        categories: payloadCategories,
      });
      setShowModal(false);
      setFormData({
        name: '',
        descriptors: '',
        cron_preset: '0 0 * * *',
        cron_expression: '0 0 * * *',
        category_ids: [],
      });
      fetchAlerts();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleGenerateSynonyms = async () => {
    setError(null);
    const baseTerm = formData.descriptors
      .split(',')
      .map((d) => d.trim())
      .filter((d) => d !== '')[0];

    if (!baseTerm) {
      return setError('Introduce un término base para generar sinónimos.');
    }

    setSynonymLoading(true);
    try {
      const data = await generateSynonyms(token, baseTerm, 10);
      if (!data.synonyms || data.synonyms.length < 3) {
        return setError(`No se encontraron suficientes sinónimos para "${baseTerm}".`);
      }

      setFormData({ ...formData, descriptors: data.synonyms.join(', ') });
    } catch (err) {
      setError(err.message);
    } finally {
      setSynonymLoading(false);
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

  const openModal = () => { setError(null); setShowModal(true); };
  const closeModal = () => { setError(null); setShowModal(false); };

  return (
    <div className="container mt-4">
      {/* Navegación entre secciones */}
      <ul className="nav nav-pills mb-4">
        <li className="nav-item"><Link className="nav-link active" to="/alertas">Alertas</Link></li>
        <li className="nav-item"><Link className="nav-link" to="/fuentes">Fuentes</Link></li>
        <li className="nav-item"><Link className="nav-link" to="/buzon">Buzón</Link></li>
      </ul>

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-1">Gestión de Alertas</h2>
          <small className="text-muted">
            El motor RSS ejecuta cada alerta según su expresión cron y notifica por buzón y email.
          </small>
        </div>
        <button className="btn btn-dark" onClick={openModal}>+ NUEVA ALERTA</button>
      </div>

      {error && !showModal && <div className="alert alert-danger">{error}</div>}

      <div className="card shadow-sm">
        <div className="card-body p-0">
          <table className="table table-hover mb-0">
            <thead className="table-dark">
              <tr>
                <th>NOMBRE DE LA ALERTA</th>
                <th>DESCRIPTORES (PALABRAS CLAVE)</th>
                <th>CATEGORÍAS IPTC</th>
                <th>PERIODICIDAD (CRON)</th>
                <th>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr><td colSpan="5" className="text-center py-4">No hay alertas configuradas.</td></tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="align-middle fw-bold">{alert.name}</td>
                    <td className="align-middle">
                      {alert.descriptors.map((d) => (
                        <span key={d} className="badge bg-secondary me-1">{d}</span>
                      ))}
                    </td>
                    <td className="align-middle">
                      {(alert.categories || []).map((c, idx) => (
                        <span key={`${c.label}-${idx}`} className="badge bg-info text-dark me-1">
                          {c.label}
                        </span>
                      ))}
                    </td>
                    <td className="align-middle"><code>{alert.cron_expression}</code></td>
                    <td className="align-middle">
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => handleDelete(alert.id)}
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

      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">CREAR NUEVA ALERTA</h5>
                <button type="button" className="btn-close btn-close-white" onClick={closeModal}></button>
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}

                <form onSubmit={handleCreate}>
                  <div className="mb-3">
                    <label className="form-label">NOMBRE DE LA ALERTA</label>
                    <input
                      type="text"
                      className="form-control bg-light"
                      placeholder="EJ: TENDENCIAS TECH 2026"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label">DESCRIPTORES / PALABRAS CLAVE (separados por coma)</label>
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control bg-light"
                        placeholder="IA, ROBÓTICA, CHIPS"
                        value={formData.descriptors}
                        onChange={(e) => setFormData({ ...formData, descriptors: e.target.value })}
                        required
                      />
                      <button
                        type="button"
                        className="btn btn-outline-dark"
                        onClick={handleGenerateSynonyms}
                        disabled={synonymLoading}
                      >
                        {synonymLoading ? 'GENERANDO...' : 'GENERAR SINÓNIMOS'}
                      </button>
                    </div>
                    <small className="text-muted">Introduce entre 3 y 10 palabras.</small>
                  </div>

                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">PERIODICIDAD</label>
                      <select
                        className="form-select bg-light"
                        value={formData.cron_preset}
                        onChange={(e) => handlePresetChange(e.target.value)}
                      >
                        {CRON_PRESETS.map((p) => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">EXPRESIÓN CRON</label>
                      <input
                        type="text"
                        className="form-control bg-light font-monospace"
                        value={formData.cron_expression}
                        onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })}
                        disabled={formData.cron_preset !== 'custom'}
                        required
                      />
                      <small className="text-muted">
                        Formato: min hora día mes día-semana
                      </small>
                    </div>
                  </div>

                  <div className="mb-3">
                    <label className="form-label">CATEGORÍAS IPTC</label>
                    {categories.length === 0 ? (
                      <div className="text-muted small">
                        No hay categorías IPTC disponibles. Se usará "General" por defecto.
                      </div>
                    ) : (
                      <div className="d-flex flex-wrap gap-2">
                        {categories.map((cat) => {
                          const selected = formData.category_ids.includes(cat.id);
                          return (
                            <button
                              type="button"
                              key={cat.id}
                              className={`btn btn-sm ${selected ? 'btn-dark' : 'btn-outline-dark'}`}
                              onClick={() => toggleCategory(cat)}
                            >
                              {cat.name}
                            </button>
                          );
                        })}
                      </div>
                    )}
                    <small className="text-muted d-block mt-1">
                      Si no seleccionas ninguna, la alerta buscará en todas las categorías.
                    </small>
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
