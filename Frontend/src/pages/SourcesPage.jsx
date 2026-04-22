import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  getSources, createSource, deleteSource,
  getCategories, getChannels, createChannel, deleteChannel
} from '../services/sourcesService';

export default function SourcesPage() {
  const token = localStorage.getItem('token');
  
  // Estados generales
  const [activeTab, setActiveTab] = useState('fuentes'); // 'fuentes' o 'canales'
  const [error, setError] = useState(null);
  
  // Datos
  const [sources, setSources] = useState([]);
  const [categories, setCategories] = useState([]);
  const [allChannels, setAllChannels] = useState([]);
  
  // Modales
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [showChannelModal, setShowChannelModal] = useState(false);
  
  // Formularios
  const [sourceForm, setSourceForm] = useState({ name: '', url: '' });
  const [channelForm, setChannelForm] = useState({ source_id: '', category_id: '', url: '' });

  useEffect(() => {
    fetchInitialData();
  }, []);

  // Cuando cambiamos a la pestaña de canales, los recargamos
  useEffect(() => {
    if (activeTab === 'canales') {
      fetchAllChannels(sources);
    }
  }, [activeTab, sources]);

  const fetchInitialData = async () => {
    try {
      const [sourcesData, categoriesData] = await Promise.all([
        getSources(token),
        getCategories(token)
      ]);
      setSources(sourcesData);
      setCategories(categoriesData);
    } catch (err) {
      setError(err.message);
    }
  };

  // El backend pide los canales por fuente, así que iteramos para juntarlos todos
  const fetchAllChannels = async (currentSources) => {
    try {
      let channelsList = [];
      for (const source of currentSources) {
        const sourceChannels = await getChannels(token, source.id);
        // Le añadimos el nombre de la fuente para pintarlo en la tabla
        const mapped = sourceChannels.map(ch => ({ ...ch, sourceName: source.name }));
        channelsList = [...channelsList, ...mapped];
      }
      setAllChannels(channelsList);
    } catch (err) {
      setError('Error al cargar la lista de canales RSS');
    }
  };

  /* --- HANDLERS PARA FUENTES --- */
  const handleCreateSource = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await createSource(token, sourceForm);
      setShowSourceModal(false);
      setSourceForm({ name: '', url: '' });
      fetchInitialData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm('¿Seguro que quieres eliminar esta fuente?')) return;
    try {
      await deleteSource(token, sourceId);
      fetchInitialData();
    } catch (err) {
      setError(err.message);
    }
  };

  /* --- HANDLERS PARA CANALES RSS --- */
  const handleCreateChannel = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const payload = {
        url: channelForm.url,
        category_id: parseInt(channelForm.category_id)
      };
      await createChannel(token, channelForm.source_id, payload);
      setShowChannelModal(false);
      setChannelForm({ source_id: '', category_id: '', url: '' });
      fetchAllChannels(sources);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteChannel = async (sourceId, channelId) => {
    if (!window.confirm('¿Seguro que quieres eliminar este canal RSS?')) return;
    try {
      await deleteChannel(token, sourceId, channelId);
      fetchAllChannels(sources);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container mt-4">
      <ul className="nav nav-pills mb-4">
        <li className="nav-item"><Link className="nav-link" to="/alertas">Alertas</Link></li>
        <li className="nav-item"><Link className="nav-link active" to="/fuentes">Fuentes</Link></li>
        <li className="nav-item"><Link className="nav-link" to="/buzon">Buzón</Link></li>
      </ul>
      {/* Cabecera con Pestañas y Botones */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Fuentes e Información</h2>
        
        <div>
          <div className="btn-group me-3" role="group">
            <button 
              type="button" 
              className={`btn ${activeTab === 'fuentes' ? 'btn-dark' : 'btn-outline-dark'}`}
              onClick={() => { setError(null); setActiveTab('fuentes'); }}
            >
              FUENTES
            </button>
            <button 
              type="button" 
              className={`btn ${activeTab === 'canales' ? 'btn-dark' : 'btn-outline-dark'}`}
              onClick={() => { setError(null); setActiveTab('canales'); }}
            >
              CANALES RSS
            </button>
          </div>

          {activeTab === 'fuentes' ? (
            <button className="btn btn-dark" onClick={() => setShowSourceModal(true)}>+ AÑADIR FUENTE</button>
          ) : (
            <button className="btn btn-dark" onClick={() => setShowChannelModal(true)}>+ AÑADIR CANAL RSS</button>
          )}
        </div>
      </div>

      {error && !showSourceModal && !showChannelModal && <div className="alert alert-danger">{error}</div>}

      {/* VISTA DE FUENTES */}
      {activeTab === 'fuentes' && (
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
                        <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteSource(source.id)}>Borrar</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VISTA DE CANALES RSS */}
      {activeTab === 'canales' && (
        <div className="card shadow-sm">
          <div className="card-body p-0">
            <table className="table table-hover mb-0">
              <thead className="table-dark">
                <tr>
                  <th>MEDIO</th>
                  <th>URL DEL CANAL RSS</th>
                  <th>ACCIONES</th>
                </tr>
              </thead>
              <tbody>
                {allChannels.length === 0 ? (
                  <tr><td colSpan="3" className="text-center py-4">No hay canales RSS configurados.</td></tr>
                ) : (
                  allChannels.map(channel => (
                    <tr key={channel.id}>
                      <td className="align-middle fw-bold">{channel.sourceName}</td>
                      <td className="align-middle text-muted">
                        <a href={channel.url} target="_blank" rel="noopener noreferrer">{channel.url}</a>
                      </td>
                      <td className="align-middle">
                        <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteChannel(channel.information_source_id, channel.id)}>Borrar</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL PARA AÑADIR FUENTE */}
      {showSourceModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">AÑADIR NUEVA FUENTE</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowSourceModal(false)}></button>
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}
                <form onSubmit={handleCreateSource}>
                  <div className="mb-3">
                    <label className="form-label">Nombre del Medio</label>
                    <input type="text" className="form-control" value={sourceForm.name} onChange={e => setSourceForm({...sourceForm, name: e.target.value})} required />
                  </div>
                  <div className="mb-4">
                    <label className="form-label">URL Principal</label>
                    <input type="url" className="form-control" value={sourceForm.url} onChange={e => setSourceForm({...sourceForm, url: e.target.value})} required />
                  </div>
                  <div className="d-flex justify-content-end gap-2">
                    <button type="button" className="btn btn-outline-secondary" onClick={() => setShowSourceModal(false)}>CANCELAR</button>
                    <button type="submit" className="btn btn-dark">GUARDAR FUENTE</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL PARA AÑADIR CANAL RSS */}
      {showChannelModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">AÑADIR CANAL RSS</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowChannelModal(false)}></button>
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}
                <form onSubmit={handleCreateChannel}>
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Medio de Comunicación</label>
                      <select className="form-select" value={channelForm.source_id} onChange={e => setChannelForm({...channelForm, source_id: e.target.value})} required>
                        <option value="">Selecciona una fuente...</option>
                        {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                    </div>
                    <div className="col-md-6 mb-3">
                      <label className="form-label">Categoría IPTC</label>
                      <select className="form-select" value={channelForm.category_id} onChange={e => setChannelForm({...channelForm, category_id: e.target.value})} required>
                        <option value="">Selecciona una categoría...</option>
                        {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="form-label">URL del feed RSS</label>
                    <input type="url" className="form-control" placeholder="https://elpais.com/rss/tecnologia.xml" value={channelForm.url} onChange={e => setChannelForm({...channelForm, url: e.target.value})} required />
                  </div>
                  <div className="d-flex justify-content-end gap-2">
                    <button type="button" className="btn btn-outline-secondary" onClick={() => setShowChannelModal(false)}>CANCELAR</button>
                    <button type="submit" className="btn btn-dark">GUARDAR CANAL</button>
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