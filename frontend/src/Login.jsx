import React, { useState } from 'react';
import './index.css';

const Login = ({ onLoginSuccess, onGoToOnboarding }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Veuillez saisir votre adresse email.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Erreur de connexion');
      }

      // Succès
      onLoginSuccess(data.user, data.token);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Mock auto-login using the seeded data for the demo
  const mockLogin = () => {
    setEmail('sophie.martin@shop-avenue.fr');
    setPassword('demo');
  };

  return (
    <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <div className="wizard-card" style={{ width: '100%', maxWidth: '400px', padding: '40px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <img src="/logo_premium.png" alt="Refundly" style={{ height: '150px', objectFit: 'contain', marginBottom: '20px' }} />
          <p className="text-muted" style={{ fontSize: '0.9rem' }}>Connexion à votre espace professionnel</p>
        </div>

        {error && (
          <div style={{ backgroundColor: '#fef2f2', color: '#b91c1c', padding: '10px', borderRadius: '6px', marginBottom: '20px', fontSize: '0.9rem', textAlign: 'center', border: '1px solid #f87171' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label" style={{ fontSize: '0.9rem', fontWeight: '600' }}>Adresse Email</label>
            <input 
              type="email" 
              className="form-input" 
              placeholder="contact@maboutique.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" style={{ fontSize: '0.9rem', fontWeight: '600' }}>Mot de passe</label>
            <input 
              type="password" 
              className="form-input" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '10px', padding: '12px', fontSize: '1rem' }}
            disabled={loading}
          >
            {loading ? 'Connexion en cours...' : 'Se connecter'}
          </button>
        </form>

        <div style={{ marginTop: '25px', textAlign: 'center', borderTop: '1px solid #e2e8f0', paddingTop: '20px' }}>
          <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '10px' }}>Nouveau sur Refundly ?</p>
          <button 
            onClick={onGoToOnboarding}
            className="btn btn-secondary" 
            style={{ width: '100%', fontSize: '0.9rem' }}
          >
            Créer un compte (Onboarding)
          </button>
        </div>

        {/* Secret magic button for demo purposes */}
        <div style={{ textAlign: 'center', marginTop: '15px' }}>
           <button onClick={mockLogin} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}>
             Remplir identifiants de démo
           </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
