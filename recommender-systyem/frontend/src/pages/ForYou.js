import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { recsAPI } from '../utils/api';
import ProductCard from '../components/ProductCard';
import { MethodBadges, TrustBar } from '../components/TrustComponents';
import { useAuth } from '../context/AuthContext';
import { Shield, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import './ForYou.css';

export default function ForYou() {
  const { user } = useAuth();
  const [recs, setRecs] = useState([]);
  const [seedAsin, setSeedAsin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [minTrust, setMinTrust] = useState(0.4);
  const [showExplain, setShowExplain] = useState(null);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    recsAPI.forYou({ top_n: 12, min_trust: minTrust })
      .then(r => {
        setRecs(r.data.recommendations || []);
        setSeedAsin(r.data.seed_asin);
      })
      .finally(() => setLoading(false));
  }, [user, minTrust]);

  if (!user) {
    return (
      <div className="for-you page-enter">
        <div className="container not-logged-in">
          <Shield size={48} style={{ color: 'var(--accent2)' }} />
          <h2>Personalised Recommendations</h2>
          <p>Log in to see trustworthy recommendations tailored to your rating history.</p>
          <div style={{ display: 'flex', gap: 12 }}>
            <Link to="/login" className="btn btn-primary">Log in</Link>
            <Link to="/register" className="btn btn-ghost">Sign up</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="for-you page-enter">
      <div className="container">
        <div className="fy-header">
          <div>
            <h1 className="page-title">For You, {user.username}</h1>
            <p className="page-sub">
              Trustworthy recommendations based on your rating history
              {seedAsin && <> · seeded from <code>{seedAsin}</code></>}
            </p>
          </div>
          <div className="fy-controls">
            <label className="trust-filter">
              Min Trust: <strong>{Math.round(minTrust * 100)}%</strong>
              <input type="range" min="0.2" max="0.8" step="0.1" value={minTrust}
                onChange={e => setMinTrust(parseFloat(e.target.value))} />
            </label>
          </div>
        </div>

        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : recs.length === 0 ? (
          <div className="fy-empty">
            <Zap size={40} style={{ color: 'var(--text3)' }} />
            <h3>No recommendations yet</h3>
            <p>Rate some products to get personalized trustworthy recommendations.</p>
            <Link to="/products" className="btn btn-primary">Browse Products</Link>
          </div>
        ) : (
          <div className="fy-grid">
            {recs.map((rec, i) => (
              <div key={rec.product.id} className="fy-rec-item">
                <ProductCard product={rec.product} showSimilarity similarity={rec.similarity} />
                <div className="fy-rec-meta">
                  <TrustBar score={rec.product.trust?.final_trust_score || 0} label="Trust" />
                  <MethodBadges breakdown={rec.method_breakdown} />
                  <button className="explain-btn"
                    onClick={() => setShowExplain(showExplain === i ? null : i)}>
                    {showExplain === i ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
                    Why recommended?
                  </button>
                  {showExplain === i && (
                    <div className="explain-panel card">
                      <pre className="explain-text">{rec.explanation}</pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}