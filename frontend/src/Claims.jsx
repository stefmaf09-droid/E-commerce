import React, { useState, useEffect } from 'react';
import './index.css';

const Claims = ({ user, onClose }) => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, pending, accepted, rejected
  const [selectedClaim, setSelectedClaim] = useState(null);

  useEffect(() => {
    const fetchAllClaims = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/api/claims?email=${encodeURIComponent(user.email)}`);
        if (response.ok) {
          const data = await response.json();
          setClaims(data);
        }
      } catch (error) {
        console.error("Failed to load claims:", error);
      } finally {
        setLoading(false);
      }
    };
    if (user?.email) fetchAllClaims();
  }, [user]);

  const filteredClaims = claims.filter(c => {
    if (filter === 'all') return true;
    return c.status === filter;
  });

  const getStatusBadge = (status) => {
    if (status === 'accepted') return <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold', backgroundColor: '#dcfce7', color: '#166534' }}>Remboursé</span>;
    if (status === 'rejected') return <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold', backgroundColor: '#fee2e2', color: '#991b1b' }}>Rejeté</span>;
    return <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold', backgroundColor: '#e0f2fe', color: '#0369a1' }}>En cours</span>;
  };

  if (selectedClaim) {
    return (
      <div className="animate-fade-in" style={{ padding: '20px' }}>
        <button className="btn-secondary" onClick={() => setSelectedClaim(null)} style={{ marginBottom: '20px', fontSize: '0.85rem' }}>
          ← Retour à la liste
        </button>
        <h2 className="title-gradient" style={{ marginBottom: '10px' }}>Détails du litige {selectedClaim.reference}</h2>
        
        <div style={{ backgroundColor: '#f8fafc', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div>
              <p className="text-muted text-sm">Transporteur</p>
              <p style={{ fontWeight: 'bold' }}>{selectedClaim.carrier}</p>
            </div>
            <div>
              <p className="text-muted text-sm">Date de création</p>
              <p style={{ fontWeight: 'bold' }}>{selectedClaim.date}</p>
            </div>
            <div>
              <p className="text-muted text-sm">Montant demandé</p>
              <p style={{ fontWeight: 'bold', color: '#ca8a04' }}>{new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(selectedClaim.amount)}</p>
            </div>
            <div>
              <p className="text-muted text-sm">Statut actuel</p>
              {getStatusBadge(selectedClaim.status)}
            </div>
          </div>
        </div>

        <div style={{ padding: '20px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)' }}>
          <h3 style={{ marginBottom: '15px' }}>Historique du dossier</h3>
          <div style={{ borderLeft: '2px solid #e2e8f0', marginLeft: '10px', paddingLeft: '20px', position: 'relative' }}>
            <div style={{ position: 'absolute', left: '-6px', top: '0', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#0f766e' }}></div>
            <p style={{ fontWeight: 'bold', margin: 0 }}>Création du dossier automatisée</p>
            <p className="text-muted text-sm" style={{ marginBottom: '20px' }}>Il y a quelques jours</p>

            {selectedClaim.status === 'accepted' && (
              <>
                <div style={{ position: 'absolute', left: '-6px', top: '60px', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#166534' }}></div>
                <p style={{ fontWeight: 'bold', margin: 0, color: '#166534' }}>Dossier accepté par le transporteur</p>
                <p className="text-muted text-sm">Remboursement validé</p>
              </>
            )}
            {selectedClaim.status === 'rejected' && (
              <>
                <div style={{ position: 'absolute', left: '-6px', top: '60px', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#991b1b' }}></div>
                <p style={{ fontWeight: 'bold', margin: 0, color: '#991b1b' }}>Dossier rejeté par le transporteur</p>
                <p className="text-muted text-sm">Motif: Non conformité des délais</p>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className="title-gradient" style={{ margin: 0 }}>Gestion des Litiges</h2>
        <button onClick={onClose} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>Tableau de bord</button>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button onClick={() => setFilter('all')} className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '6px 15px', borderRadius: '20px' }}>Tous</button>
        <button onClick={() => setFilter('pending')} className={`btn ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '6px 15px', borderRadius: '20px' }}>En cours</button>
        <button onClick={() => setFilter('accepted')} className={`btn ${filter === 'accepted' ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '6px 15px', borderRadius: '20px' }}>Gagnés</button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Chargement des litiges...</div>
      ) : filteredClaims.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontStyle: 'italic', border: '1px dashed #cbd5e1', borderRadius: '8px' }}>
          Aucun litige trouvé pour ce filtre.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '10px' }}>
          {filteredClaims.map(claim => (
            <div 
              key={claim.id} 
              onClick={() => setSelectedClaim(claim)}
              style={{ 
                padding: '15px', 
                border: '1px solid #e2e8f0', 
                borderRadius: '8px', 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                backgroundColor: '#fff',
                cursor: 'pointer',
                transition: 'border-color 0.2s, box-shadow 0.2s',
              }}
              onMouseOver={(e) => { e.currentTarget.style.borderColor = '#0f766e'; Object.assign(e.currentTarget.style, {boxShadow: '0 2px 4px rgba(0,0,0,0.05)'}); }}
              onMouseOut={(e) => { e.currentTarget.style.borderColor = '#e2e8f0'; Object.assign(e.currentTarget.style, {boxShadow: 'none'}); }}
            >
              <div>
                <p style={{ fontWeight: 'bold', marginBottom: '5px', fontSize: '1rem' }}>{claim.reference}</p>
                <p className="text-muted text-sm">{claim.carrier} • Ouvert le {claim.date}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ marginBottom: '5px' }}>{getStatusBadge(claim.status)}</div>
                <span style={{ fontWeight: 'bold', color: '#334155' }}>
                  {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(claim.amount)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Claims;
