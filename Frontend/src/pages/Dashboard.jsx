import WordCloudChart from '../components/WordCloudChart';
import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { getGlobalStats, getCategoryDistribution } from '../services/statsService';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function Dashboard() {
  const token = localStorage.getItem('token');
  const [stats, setStats] = useState({ total_news: 0, active_alerts: 0, sources: 0 });
  const [chartData, setChartData] = useState([]);

  const mockWords = [
    { text: 'IA', value: 10 }, { text: 'Ciberseguridad', value: 8 }, 
    { text: 'Mercados', value: 7 }, { text: 'Innovación', value: 6 },
    { text: 'Sostenibilidad', value: 5 }, { text: 'Bolsa', value: 4 },
    { text: 'Elecciones', value: 3 }, { text: 'Europa', value: 3 }
  ];
  
  useEffect(() => {
    // Aquí cargaríamos los datos reales de los Sprints 3.1 y 3.2
    async function loadDashboard() {
      try {
        const s = await getGlobalStats(token);
        const c = await getCategoryDistribution(token);
        setStats(s);
        setChartData(c);
      } catch (e) {
        console.error("Error cargando los datos reales:", e);
      }
    }
    loadDashboard();
  }, [token]);

  return (
    <div className="container mt-4">
      <h2 className="mb-4">Dashboard Global - NewsRadar</h2>
      
      {/* 1. Tarjetas de Métricas */}
      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card bg-dark text-white shadow-sm">
            <div className="card-body text-center">
              <h6>Noticias Procesadas (24h)</h6>
              <h2 className="display-4">{stats.total_news}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-dark shadow-sm">
            <div className="card-body text-center">
              <h6>Alertas Activas</h6>
              <h2 className="display-4 text-primary">{stats.active_alerts}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card border-dark shadow-sm">
            <div className="card-body text-center">
              <h6>Fuentes Monitorizadas</h6>
              <h2 className="display-4">{stats.sources}</h2>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        {/* 2. Gráfico de Distribución por Categoría */}
        <div className="col-md-6">
          <div className="card shadow-sm h-100">
            <div className="card-header bg-white fw-bold">DISTRIBUCIÓN POR CATEGORÍA IPTC</div>
            <div className="card-body" style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* 3. Placeholder para Nube de Palabras */}
        <div className="col-md-6">
          <div className="card shadow-sm h-100">
            <div className="card-header bg-white fw-bold">TENDENCIAS (WORD CLOUD)</div>
            <div className="card-body d-flex align-items-center justify-content-center text-muted">
              <WordCloudChart words={mockWords} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}