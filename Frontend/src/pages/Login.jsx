// Pantalla de Login 
import { Link } from 'react-router-dom';

export default function Login() {
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm">
            <div className="card-body p-5">
              <h2 className="text-center mb-4">NEWSRADAR</h2>
              <h4 className="text-center mb-4 text-muted">Iniciar Sesión</h4>
              
              <form>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">Correo electrónico</label>
                  <input type="email" className="form-control" id="email" placeholder="usuario@uc3m.es" required />
                </div>
                <div className="mb-4">
                  <label htmlFor="password" className="form-label">Contraseña</label>
                  <input type="password" className="form-control" id="password" required />
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