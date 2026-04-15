import React, { useState, useEffect } from 'react';
import { getSources, createSource, deleteSource } from '../services/sourcesService';

export default function SourcesPage() {
  const token = localStorage.getItem('token');
  
  const [sources, setSources] = useState([]);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    url: ''
  });

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const data = await getSources(token);
      setSources(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);

    // Validación básica de URL
    if (!formData.url.startsWith('http://') && !formData.url.startsWith('https://')) {
      return setError('La URL debe empezar por http:// o https://');
    }

    try {
      await createSource(token, formData);
      setShowModal(false);
      setFormData({ name: '', url: '' });
      fetchSources();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (sourceId) => {
    if (!window.confirm('¿Seguro que quieres eliminar esta fuente? Se borrarán sus canales RSS asociados.')) return;
    try {
      await deleteSource(token, sourceId);
      fetchSources();
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
        <h2>Fuentes de Información</h2>
        <button className="btn btn-dark" onClick={openModal}>
          + AÑADIR FUENTE
        </button>
      </div>

      {error && !showModal && <div className="alert alert-danger">{error}</div>}

      <div className="card shadow-sm">
        <div className="card-body p-0">
          <table className="table table-hover mb-0">
            <thead className="table-dark">
              <tr>
                <th>MEDIO DE COMUNICACIÓN</th>
                <th>URL PRINCIPAL</th>
                <th>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {sources.length === 0 ? (
                <tr><td colSpan="3" className="text-center py-4">No hay fuentes configuradas.</td></tr>
              ) : (
                sources.map(source => (
                  <tr key={source.id}>
                    <td className="align-middle fw-bold">{source.name}</td>
                    <td className="align-middle text-muted">
                      <a href={source.url} target="_blank" rel="noopener noreferrer">{source.url}</a>
                    </td>
                    <td className="align-middle">
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(source.id)}>
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
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">AÑADIR NUEVA FUENTE</h5>
                <button type="button" className="btn-close btn-close-white" onClick={closeModal}></button>
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}
                
                <form onSubmit={handleCreate}>
                  <div className="mb-3">
                    <label className="form-label">Nombre del Medio</label>
                    <input 
                      type="text" 
                      className="form-control bg-light" 
                      placeholder="Ej: El País"
                      value={formData.name}
                      onChange={e => setFormData({...formData, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label className="form-label">URL Principal</label>
                    <input 
                      type="url" 
                      className="form-control bg-light" 
                      placeholder="https://elpais.com"
                      value={formData.url}
                      onChange={e => setFormData({...formData, url: e.target.value})}
                      required
                    />
                  </div>
                  <div className="d-flex justify-content-end gap-2">
                    <button type="button" className="btn btn-outline-secondary" onClick={closeModal}>
                      CANCELAR
                    </button>
                    <button type="submit" className="btn btn-dark">
                      GUARDAR FUENTE
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