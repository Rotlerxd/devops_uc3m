// Pantalla de Login
import React, {useState} from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault(); 
    setError(''); 

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // 1. Guardamos el token
        localStorage.setItem('token', data.access_token);
        
        // 2. Buscamos el ID del usuario usando su email
        const userRes = await fetch('http://127.0.0.1:8000/api/v1/users', {
          headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        
        if (userRes.ok) {
          const users = await userRes.json();
          const currentUser = users.find(u => u.email === email);
          if (currentUser) {
            localStorage.setItem('userId', currentUser.id);
            // Opcional: guardar los roles para proteger rutas más adelante
            localStorage.setItem('userRoles', JSON.stringify(currentUser.role_ids)); 
          }
        }

        navigate('/alertas'); // Te redirijo a alertas directamente para probar
      } else {
        setError(data.detail || 'Credenciales incorrectas');
      }
    } catch (err) {
      setError('Error de conexión: El servidor en 127.0.0.1:8000 está apagado o bloqueando CORS.');
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body p-5">
              <h2 className="text-center mb-4">NEWSRADAR</h2>
              <h4 className="text-center mb-4 text-muted">Iniciar Sesión</h4>
              
              {error && <div className="alert alert-danger">{error}</div>}
              
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">Correo electrónico</label>
                  <input 
                    type="email" 
                    className="form-control" 
                    id="email" 
                    placeholder="usuario@uc3m.es" 
                    required 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="password" className="form-label">Contraseña</label>
                  <input 
                    type="password" 
                    className="form-control" 
                    id="password" 
                    required 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
                
                <button type="submit" className="btn btn-primary w-100 mb-3">
                  Entrar
                </button>
              </form>

              <div className="text-center mt-3">
                <p className="mb-0">¿No tienes cuenta? <Link to="/register">Regístrate aquí</Link></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}