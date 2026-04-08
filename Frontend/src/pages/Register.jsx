import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Register() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [organization, setOrganization] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          first_name: firstName, 
          last_name: lastName, 
          organization: organization, 
          email: email, 
          password: password 
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Registro completado con éxito. Redirigiendo al login...');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        if (response.status === 422) {
            setError('Por favor, rellena todos los campos correctamente.');
        } else {
            setError(data.detail || 'Error al registrar el usuario');
        }
      }
    } catch (err) {
      setError('Error de conexión con el servidor.');
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body p-5">
              <h2 className="text-center mb-4">NEWSRADAR</h2>
              <h4 className="text-center mb-4 text-muted">Crear Cuenta</h4>
              
              {error && <div className="alert alert-danger">{error}</div>}
              {success && <div className="alert alert-success">{success}</div>}
              
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="firstName" className="form-label">Nombre</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="firstName" 
                    placeholder="Tu nombre" 
                    required 
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="lastName" className="form-label">Apellidos</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="lastName" 
                    placeholder="Tus apellidos" 
                    required 
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="organization" className="form-label">Organización</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="organization" 
                    placeholder="Tu universidad o empresa" 
                    required 
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                  />
                </div>
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
                
                <button type="submit" className="btn btn-success w-100 mb-3">
                  Registrarse
                </button>
              </form>

              <div className="text-center mt-3">
                <p className="mb-0">¿Ya tienes cuenta? <Link to="/login">Inicia sesión aquí</Link></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}