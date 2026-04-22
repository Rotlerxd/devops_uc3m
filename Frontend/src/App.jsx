import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import AlertsPage from './pages/AlertsPage.jsx';
import SourcesPage from './pages/SourcesPage.jsx';
import NotificationsPage from './pages/NotificationsPage.jsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/alertas" element={<AlertsPage />} />
        <Route path="/fuentes" element={<SourcesPage />} />
        <Route path="/buzon" element={<NotificationsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;