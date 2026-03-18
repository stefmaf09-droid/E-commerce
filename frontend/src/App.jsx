import { useState, useEffect } from 'react';
import Login from './Login';
import Claims from './Claims';
import './index.css';
const STEPS = [
  { id: 1, label: 'Profil' },
  { id: 2, label: 'Boutique' },
  { id: 3, label: 'Documents' },
  { id: 4, label: 'Banque' },
  { id: 5, label: 'Prêt !' }
];

function App() {
  // 1. Initialiser le state depuis le localStorage
  const loadState = (key, defaultValue) => {
    const saved = localStorage.getItem(key);
    if (saved !== null) {
      try { return JSON.parse(saved); } catch { return saved; }
    }
    return defaultValue;
  };

  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState(() => loadState('isAuthenticated', false));
  const [user, setUser] = useState(() => loadState('user', null));
  const [showOnboarding, setShowOnboarding] = useState(() => loadState('showOnboarding', false));

  // Onboarding State
  const [step, setStep] = useState(() => loadState('onboarding_step', 1));

  const [formData, setFormData] = useState(() => loadState('onboarding_data', {
    name: '',
    company: '',
    email: '',
    phone: '',
    platform: 'Shopify',
    storeName: '',
    storeUrl: '',
    apiKey: '',
    iban: '',
    bic: '',
    holder: '',
  }));

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // States for Document Upload (OCR Simulation)
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Vue Dashboard & Claims
  const [isDashboard, setIsDashboard] = useState(() => loadState('isDashboard', false));
  const [showClaims, setShowClaims] = useState(false);
  const [isVerificationMode, setIsVerificationMode] = useState(false);
  
  // Dashboard Data State
  const [dashboardMetrics, setDashboardMetrics] = useState({ recovered_amount: 0, pending_claims: 0, total_claims: 0 });
  const [recentClaims, setRecentClaims] = useState([]);
  const [isDashboardLoading, setIsDashboardLoading] = useState(false);

  // 2. Sauvegarder dans localStorage à chaque changement
  useEffect(() => {
    localStorage.setItem('onboarding_step', JSON.stringify(step));
    localStorage.setItem('onboarding_data', JSON.stringify(formData));
    localStorage.setItem('isDashboard', JSON.stringify(isDashboard));
    localStorage.setItem('isAuthenticated', JSON.stringify(isAuthenticated));
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('showOnboarding', JSON.stringify(showOnboarding));
  }, [step, formData, isDashboard, isAuthenticated, user, showOnboarding]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    setShowOnboarding(false);
    setIsDashboard(true);
    // Update local config with the user's fetched details to show in Dashboard nicely
    setFormData(prev => ({
      ...prev,
      name: userData.name,
      company: userData.company,
      email: userData.email,
      storeName: prev.storeName || "Boutique de Démo"
    }));
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setIsDashboard(false);
    setShowOnboarding(false);
    localStorage.clear(); // Clear all onboarding data on logout
  };

  // 2.5 Charger les données du Dashboard
  useEffect(() => {
    if (isAuthenticated && isDashboard && user?.email) {
      const fetchDashboardData = async () => {
        setIsDashboardLoading(true);
        try {
          const metricsRes = await fetch(`http://localhost:8000/api/dashboard/metrics?email=${encodeURIComponent(user.email)}`);
          if (metricsRes.ok) {
            const metrics = await metricsRes.json();
            setDashboardMetrics(metrics);
          }
          
          const claimsRes = await fetch(`http://localhost:8000/api/claims?email=${encodeURIComponent(user.email)}`);
          if (claimsRes.ok) {
            const claims = await claimsRes.json();
            setRecentClaims(claims.slice(0, 5)); // get only 5 most recent
          }
        } catch (error) {
          console.error("Failed to load dashboard data:", error);
        } finally {
          setIsDashboardLoading(false);
        }
      };
      fetchDashboardData();
    }
  }, [isAuthenticated, isDashboard, user]);

  // 3. Gestionnaire de saisie
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Effacer l'erreur quand l'utilisateur tape
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  // 4. Validation et Navigation
  const nextStep = () => {
    let newErrors = {};
    if (step === 1) {
      if (!formData.name) newErrors.name = 'Le nom est obligatoire';
      if (!formData.company) newErrors.company = "L'entreprise est obligatoire";
      if (!formData.email) newErrors.email = "L'email est obligatoire";
    } else if (step === 2) {
      if (!formData.storeName) newErrors.storeName = 'Nom de boutique obligatoire';
      if (!formData.storeUrl) newErrors.storeUrl = 'URL de la boutique obligatoire';
      if (!formData.apiKey) newErrors.apiKey = 'Clé API / Jeton obligatoire';
    } else if (step === 3) {
      // Étape Documents: Optionnelle, aucune erreur bloquante
    } else if (step === 4) {
      if (!formData.iban) newErrors.iban = 'L\'IBAN est obligatoire';
      if (!formData.holder) newErrors.holder = 'Le titulaire est obligatoire';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
    setStep(prev => prev + 1);
  };

  const prevStep = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setStep(prev => prev - 1);
  };

  // 5. Finalisation (Étape 4) - Envoi de l'email via API Python
  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      // 1. Envoi à l'API Python
      const response = await fetch('http://localhost:8000/api/onboarding/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error("Erreur lors de l'envoi au serveur Python");
      }

      // Successfully completed onboarding
      setIsAuthenticated(true);
      setUser({
        id: 999, // placeholder new user
        name: formData.name,
        company: formData.company,
        email: formData.email
      });
      setIsDashboard(true);
      setShowOnboarding(false);
      setStep(5); // Ensure step is 5 for the "Prêt !" state
    } catch (err) {
      console.error(err);
      alert("Une erreur s'est produite lors de la finalisation.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ================= Rendu des Étapes =================

  const renderProgress = () => (
    <div className="progress-container">
      <div
        className="progress-bar-fill"
        style={{ width: `${((step - 1) / (STEPS.length - 1)) * 100}%` }}
      />
      {STEPS.map((s) => {
        let className = "progress-step";
        if (s.id === step) className += " active";
        if (s.id < step) className += " completed";

        return (
          <div key={s.id} className={className}>
            <div className="step-circle">
              {s.id < step ? '✓' : s.id}
            </div>
            <span className="step-label">{s.label}</span>
          </div>
        );
      })}
    </div>
  );

  const renderStep1 = () => (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>👋</div>
        <h2 className="title-gradient">Bienvenue sur Refundly !</h2>
        <p className="text-muted">La configuration prend moins de 5 minutes.</p>
      </div>

      <div className="info-box">
        <span className="info-icon">💡</span>
        <div className="info-text">
          <strong>Comment ça marche ?</strong> Notre IA détecte automatiquement vos litiges
          transporteurs non résolus et les traite pour vous. Vous recevez <strong>80 %</strong> des remboursements obtenus.
        </div>
      </div>

      <h3 className="mb-4">1. Dites-nous qui vous êtes</h3>

      <div className="form-group">
        <label className="form-label">👤 Nom complet *</label>
        <input
          type="text" name="name" className="form-input"
          placeholder="Jean Dupont" value={formData.name} onChange={handleChange}
        />
        {errors.name && <span className="form-error">{errors.name}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">🏢 Entreprise *</label>
        <input
          type="text" name="company" className="form-input"
          placeholder="Ma Boutique SAS" value={formData.company} onChange={handleChange}
        />
        {errors.company && <span className="form-error">{errors.company}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">📧 Email de contact *</label>
        <input
          type="email" name="email" className="form-input"
          placeholder="contact@maboutique.com" value={formData.email} onChange={handleChange}
        />
        {errors.email && <span className="form-error">{errors.email}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">📱 Téléphone (optionnel)</label>
        <input
          type="text" name="phone" className="form-input"
          placeholder="+33 6 12 34 56 78" value={formData.phone} onChange={handleChange}
        />
      </div>

      <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
        <button className="btn btn-primary" onClick={nextStep}>Étape suivante →</button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏪</div>
        <h2>Connectez votre boutique</h2>
        <p className="text-muted">Refundly lit vos commandes en lecture seule.</p>
      </div>

      <div className="form-group">
        <label className="form-label">Plateforme e-commerce</label>
        <select name="platform" className="form-select" value={formData.platform} onChange={handleChange}>
          <option value="Shopify">Shopify</option>
          <option value="WooCommerce">WooCommerce</option>
          <option value="PrestaShop">PrestaShop</option>
          <option value="Magento">Magento</option>
          <option value="Wix">Wix</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">🏷️ Nom de votre boutique *</label>
        <input
          type="text" name="storeName" className="form-input"
          placeholder="Ma Boutique" value={formData.storeName} onChange={handleChange}
        />
        {errors.storeName && <span className="form-error">{errors.storeName}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">🌐 URL de la boutique *</label>
        <input
          type="text" name="storeUrl" className="form-input"
          placeholder="https://maboutique.com" value={formData.storeUrl} onChange={handleChange}
        />
        {errors.storeUrl && <span className="form-error">{errors.storeUrl}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">🔑 Clé API / Access Token *</label>
        <input
          type="password" name="apiKey" className="form-input"
          placeholder="shpat_xxxxxxxxxxxxxxxx" value={formData.apiKey} onChange={handleChange}
        />
        <p className="text-muted text-sm mt-4">🔒 Chiffré AES-256 · Lecture seule · Révocable à tout moment</p>
        {errors.apiKey && <span className="form-error">{errors.apiKey}</span>}
      </div>

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={prevStep}>← Retour</button>
        <button className="btn btn-primary" onClick={nextStep}>Étape suivante →</button>
      </div>
    </div>
  );

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      // Appel à la véritable API OCR Python
      const formData = new FormData();
      formData.append('file', files[0]);

      const response = await fetch('http://localhost:8000/api/onboarding/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Erreur de traitement OCR');
      }

      const result = await response.json();

      setAnalysisResult({
        fileName: result.fileName,
        carrier: result.carrier,
        reason: result.reason,
        advice: result.advice,
        count: files.length
      });
    } catch (error) {
      console.error(error);
      setAnalysisResult({
        fileName: files[0].name,
        carrier: "Erreur",
        reason: "Le traitement OCR a échoué",
        advice: "Assurez-vous que le backend FastAPI est lancé sur le port 8000.",
        count: 1
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderStep3 = () => (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
        <h2>Preuves & Documents</h2>
        <p className="text-muted">Si vous avez des preuves de livraison ou des historiques, importez-les ici.</p>
      </div>

      <div className="info-box">
        <span className="info-icon">💡</span>
        <div className="info-text">
          <strong>Pourquoi uploader ?</strong><br/>
          Une preuve photo d'un colis endommagé accélère le remboursement. Les documents sont analysés automatiquement par notre IA (OCR). Cette étape est <strong>optionnelle</strong>.
        </div>
      </div>

      <div className="form-group" style={{ textAlign: 'center', padding: '2rem', border: '2px dashed var(--border)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📤</div>
        <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Glissez-déposez vos fichiers ici</p>
        <p className="text-muted text-sm mb-4">PNG, JPG ou PDF (max. 10MB)</p>
        <button className="btn btn-secondary" style={{ width: 'auto' }} onClick={() => document.getElementById('file-upload').click()}>
          Parcourir mes fichiers
        </button>
        <input id="file-upload" type="file" multiple style={{ display: 'none' }} accept=".png,.jpg,.jpeg,.pdf" onChange={handleFileUpload} />
      </div>

      {isAnalyzing && (
        <div style={{ textAlign: 'center', padding: '1rem' }}>
          <p className="text-muted">🤖 L'IA Refundly analyse vos documents (OCR)...</p>
          <div style={{ width: '40px', height: '40px', border: '3px solid #f3f3f3', borderTop: '3px solid var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }}></div>
        </div>
      )}

      {analysisResult && !isAnalyzing && (
        <div className="animate-fade-in" style={{ backgroundColor: 'rgba(13,148,136,.05)', padding: '15px', borderRadius: '8px', marginBottom: '15px', borderLeft: '4px solid var(--primary)' }}>
          <p style={{ color: 'var(--primary)', fontWeight: 'bold', marginBottom: '10px' }}>
            ✅ {analysisResult.count} fichier(s) analysé(s) avec succès
          </p>
          <p style={{ margin: '5px 0' }}><strong>📄 Dernier fichier :</strong> {analysisResult.fileName}</p>
          <p style={{ margin: '5px 0' }}><strong>🚚 Transporteur détecté :</strong> {analysisResult.carrier}</p>
          <p style={{ margin: '5px 0' }}><strong>🔍 Motif IA :</strong> {analysisResult.reason}</p>
          <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>💡 <em>{analysisResult.advice}</em></p>
        </div>
      )}

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={prevStep}>← Retour</button>
        <button className="btn btn-primary" onClick={nextStep}>Étape suivante →</button>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💳</div>
        <h2>Coordonnées bancaires</h2>
        <p className="text-muted">Pour recevoir vos remboursements automatiquement.</p>
      </div>

      <div className="info-box">
        <span className="info-icon">💰</span>
        <div className="info-text">
          <strong>Comment vous êtes payé ?</strong><br/>
          À chaque remboursement obtenu : <strong>80 %</strong> vous est viré sur cet IBAN. <strong>20 %</strong> est notre commission de succès.
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">🏦 IBAN *</label>
        <input
          type="text" name="iban" className="form-input"
          placeholder="FR76 1234 5678 9012 3456 7890 123" value={formData.iban} onChange={handleChange}
        />
        {errors.iban && <span className="form-error">{errors.iban}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">🔢 BIC / SWIFT</label>
        <input
          type="text" name="bic" className="form-input"
          placeholder="BNPAFRPP" value={formData.bic} onChange={handleChange}
        />
      </div>

      <div className="form-group">
        <label className="form-label">👤 Titulaire *</label>
        <input
          type="text" name="holder" className="form-input"
          placeholder="Ma Boutique SAS" value={formData.holder} onChange={handleChange}
        />
        {errors.holder && <span className="form-error">{errors.holder}</span>}
      </div>

      <div className="btn-row">
        <button className="btn btn-secondary" onClick={prevStep}>← Retour</button>
        <button className="btn btn-primary" onClick={nextStep}>Terminer →</button>
      </div>
    </div>
  );

  const renderStep5 = () => (
    <div className="animate-fade-in text-center">
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🚀</div>
      <h1 className="title-gradient">Tout est prêt !</h1>
      <p className="text-muted mb-8" style={{ fontSize: '1.1rem' }}>
        Refundly va maintenant analyser vos commandes en arrière-plan.
      </p>

      <div className="done-card-grid">
        <div className="done-card">
          <div className="done-icon">🔍</div>
          <div className="done-title">Analyse auto</div>
          <div className="done-desc">Notre IA scanne vos 12 derniers mois.</div>
        </div>
        <div className="done-card">
          <div className="done-icon">📨</div>
          <div className="done-title">Envoi auto</div>
          <div className="done-desc">Les réclamations partent d'elles-mêmes.</div>
        </div>
        <div className="done-card">
          <div className="done-icon">💰</div>
          <div className="done-title">80 % pour vous</div>
          <div className="done-desc">Remboursements virés sur votre IBAN.</div>
        </div>
      </div>

      <div className="info-box" style={{ justifyContent: 'center', marginBottom: '2rem' }}>
        <span className="info-icon">✅</span>
        <div className="info-text">
          Boutique connectée : <strong>{formData.storeName || 'Ma Boutique'}</strong>
        </div>
      </div>

      <div className="btn-row" style={{ justifyContent: 'center' }}>
        <button className="btn btn-secondary" onClick={prevStep} disabled={isSubmitting}>← Retour</button>
        <button className="btn btn-primary" onClick={handleComplete} disabled={isSubmitting}>
          {isSubmitting ? 'Finalisation...' : '🚀 Accéder à mon tableau de bord'}
        </button>
      </div>
    </div>
  );

  // ================= Rendu du Dashboard =================
  const renderDashboard = () => (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className="title-gradient" style={{ margin: 0 }}>Tableau de Bord Refundly</h2>
        <button onClick={handleLogout} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>Déconnexion</button>
      </div>
      <div className="text-center mb-6">
        <p className="text-muted">Bienvenue, {user?.name || formData.name || 'Utilisateur'} de {user?.company || formData.company || 'votre entreprise'}</p>
      </div>

      <div className="info-box" style={{ marginBottom: '20px' }}>
        <span className="info-icon">🏪</span>
        <div className="info-text">
          Boutique connectée : <strong>{user?.company || formData.storeName || 'Non configurée'}</strong>
        </div>
      </div>

      {isDashboardLoading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Chargement de vos données...</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
            <div style={{ padding: '20px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
              <h3 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '10px' }}>
                {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(dashboardMetrics.recovered_amount || 0)}
              </h3>
              <p className="text-muted">Récupérés ce mois-ci</p>
            </div>
            <div style={{ padding: '20px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
              <h3 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '10px' }}>{dashboardMetrics.pending_claims || 0}</h3>
              <p className="text-muted">Litiges en cours</p>
            </div>
          </div>

          <div style={{ padding: '20px', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)' }}>
            <h3 style={{ marginBottom: '15px' }}>Dernières Activités</h3>
            {/* Si un document d'onboarding vient d'être uploadé, l'afficher en priorité pour la démo */}
            {analysisResult ? (
              (() => {
                const isUnknownReason = analysisResult.reason.toLowerCase().includes('inconnu') || analysisResult.reason.toLowerCase().includes('automatique');
                return (
                  <div style={{ padding: '15px', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px', marginBottom: '15px' }}>
                    <div>
                      <p style={{ fontWeight: 'bold', marginBottom: '5px' }}>📄 Preuve uploadée : {analysisResult.fileName}</p>
                      <p className="text-muted text-sm">Transporteur : {analysisResult.carrier} | Motif détecté : {analysisResult.reason}</p>
                    </div>
                    {isUnknownReason ? (
                      <button
                        onClick={() => setIsVerificationMode(true)}
                        style={{
                          backgroundColor: 'rgba(234,179,8,.1)',
                          color: '#ca8a04',
                          padding: '8px 16px',
                          borderRadius: '20px',
                          fontSize: '0.9em',
                          fontWeight: 'bold',
                          border: '1px solid #ca8a04',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          whiteSpace: 'nowrap'
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.backgroundColor = 'rgba(234,179,8,.2)' }}
                        onMouseOut={(e) => { e.currentTarget.style.backgroundColor = 'rgba(234,179,8,.1)' }}
                      >
                        ⚠️ Effectuer la vérification
                      </button>
                    ) : (
                      <span style={{ backgroundColor: 'rgba(13,148,136,.1)', color: 'var(--primary)', padding: '5px 10px', borderRadius: '20px', fontSize: '0.85em', fontWeight: 'bold', whiteSpace: 'nowrap' }}>
                        En cours de réclamation
                      </span>
                    )}
                  </div>
                );
              })()
            ) : null}

            {recentClaims.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {recentClaims.map(claim => (
                  <div key={claim.id} style={{ padding: '12px 15px', border: '1px solid #f1f5f9', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fafafa' }}>
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '0.9rem', marginBottom: '2px' }}>{claim.reference}</p>
                      <p className="text-muted text-sm">{claim.carrier} • {claim.date}</p>
                    </div>
                    <div>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '12px', 
                        fontSize: '0.75rem', 
                        fontWeight: 'bold',
                        backgroundColor: claim.status === 'accepted' ? '#dcfce7' : claim.status === 'pending' ? '#e0f2fe' : '#f1f5f9',
                        color: claim.status === 'accepted' ? '#166534' : claim.status === 'pending' ? '#0369a1' : '#475569'
                      }}>
                        {claim.status === 'accepted' ? 'Remboursé' : claim.status === 'pending' ? 'En cours' : claim.status}
                      </span>
                      <span style={{ fontWeight: 'bold', marginLeft: '15px' }}>
                        {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(claim.amount)}
                      </span>
                    </div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', marginTop: '10px' }}>
                  <button 
                    onClick={() => setShowClaims(true)} 
                    style={{ background: 'none', border: 'none', color: '#0f766e', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.9rem' }}
                  >
                    Voir tous les litiges →
                  </button>
                </div>
              </div>
            ) : !analysisResult && (
              <p className="text-muted" style={{ fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                L'IA Refundly analyse actuellement votre historique de commandes. Les premiers litiges apparaîtront ici d'ici quelques heures.
              </p>
            )}
          </div>
        </>
      )}

      <div className="btn-row" style={{ marginTop: '30px', justifyContent: 'center' }}>
         <button className="btn btn-secondary" onClick={() => {
           setIsDashboard(false);
           setShowOnboarding(true); // Go back to onboarding for demo
           setStep(1);
         }}>Relancer l'onboarding (Démo)</button>
      </div>
    </div>
  );

  // Routing Principal
  if (!isAuthenticated && !showOnboarding) {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onGoToOnboarding={() => setShowOnboarding(true)}
      />
    );
  }

  return (
    <div className="app-container">
      <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem' }}>
          <img src="/logo_premium.png" alt="Refundly" style={{ height: '150px', objectFit: 'contain', cursor: 'pointer' }} onClick={() => { if(isAuthenticated) setIsDashboard(true) }} />
        </div>
        <p className="text-muted text-sm">Recouvrement logistique automatisé</p>
      </div>

      <div className="wizard-card" style={{ maxWidth: (isVerificationMode || showClaims) ? '800px' : '600px', transition: 'max-width 0.3s' }}>
        {showClaims ? (
          <Claims user={user} onClose={() => setShowClaims(false)} />
        ) : isVerificationMode ? (
          <div className="animate-fade-in" style={{ display: 'flex', gap: '30px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1', minWidth: '300px' }}>
              <div className="text-center mb-6">
                <h2 style={{ color: '#ca8a04', margin: 0 }}>Renseignements manquants</h2>
                <p className="text-muted text-sm mt-1">Notre IA n'a pas pu identifier la raison exacte du rejet sur votre document.</p>
              </div>

              <div style={{ backgroundColor: '#f8fafc', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '20px' }}>
                <p><strong>Fichier :</strong> {analysisResult?.fileName}</p>
                <p className="text-muted text-sm mt-2">Pour que nous puissions lancer la réclamation, merci de nous indiquer manuellement la raison du refus invoquée par le transporteur sur ce document.</p>
              </div>

              <div className="form-group">
                <label className="form-label">Sélectionnez le motif exact du rejet :</label>
                <select className="form-select" defaultValue="Signature Non Conforme">
                  <option value="Signature Non Conforme">Signature Non Conforme</option>
                  <option value="Colis non présenté / Relais manqué">Colis non présenté / Relais manqué</option>
                  <option value="Poids Conforme (Erreur Système)">Poids Conforme (Erreur Système)</option>
                  <option value="Délai contractuel dépassé">Délai contractuel dépassé</option>
                  <option value="Avarie constatée">Avarie constatée</option>
                </select>
              </div>

              <div className="btn-row" style={{ marginTop: '20px' }}>
                <button className="btn btn-secondary" onClick={() => setIsVerificationMode(false)}>
                  Annuler
                </button>
                <button className="btn btn-primary" onClick={() => {
                  setAnalysisResult(prev => ({ ...prev, reason: "Signature Non Conforme" })); // Simulons le choix
                  setIsVerificationMode(false);
                }}>
                  Valider et Relancer 🚀
                </button>
              </div>
            </div>

            <div style={{ flex: '1', minWidth: '300px', backgroundColor: '#f1f5f9', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', border: '2px dashed #cbd5e1' }}>
               <div style={{ textAlign: 'center', color: '#64748b' }}>
                 <div style={{ fontSize: '3rem', marginBottom: '10px' }}>🖼️</div>
                 <p>Aperçu du document: <br/><strong>{analysisResult?.fileName}</strong></p>
                 <p style={{ fontSize: '0.8em', marginTop: '10px' }}>(Visualiseur PDF/Image simulé)</p>
               </div>
            </div>
          </div>
        ) : isDashboard ? (
          renderDashboard()
        ) : (
          <>
            {renderProgress()}
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
            {step === 4 && renderStep4()}
            {step === 5 && renderStep5()}
          </>
        )}
      </div>
    </div>
  );
}

export default App;
