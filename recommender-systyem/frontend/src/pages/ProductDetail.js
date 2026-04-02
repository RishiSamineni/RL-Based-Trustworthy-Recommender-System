import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { recsAPI } from '../utils/api';
import { ShieldCheck, ShieldAlert, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import './ProductDetail.css';

export default function ProductDetail() {
  const { id } = useParams();
  const asin = id;

  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [trustCheck, setTrustCheck] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [threshold, setThreshold] = useState(0.5);

  useEffect(() => {
    setLoading(true);

    Promise.all([
      recsAPI.getTrust(asin),
      recsAPI.getSimilar(asin, 6, 0.3)
    ])
      .then(([trustRes, simRes]) => {
        setTrustCheck(trustRes.data);
        setProduct(trustRes.data);
        setSimilar(simRes.data || []);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [asin]);

  useEffect(() => {
    if (!asin) return;
    recsAPI.getTrust(asin)
      .then(r => setTrustCheck(r.data));
  }, [threshold, asin]);

  if (loading) {
    return <div className="loading-center"><div className="spinner" /></div>;
  }

  if (!product) {
    return <div className="container">Product not found</div>;
  }

  const trust = product.trust || {};
  const isTrusty = trustCheck?.rl_decision?.is_trustworthy;

  return (
    <div className="product-detail page-enter">
      <div className="container">

        <h1 className="detail-title">{product.title || "Product"}</h1>

        {/* Trust Panel */}
        <div className="trust-check-panel card">
          <div className="tcp-header">
            {isTrusty
              ? <ShieldCheck color="green" />
              : <ShieldAlert color="red" />}
            <h3>Trust Verdict</h3>
          </div>

          <div className="tcp-scores">
            <p>Final Trust: {(trust.final_trust_score * 100 || 0).toFixed(1)}%</p>
          </div>

          <div>
            <label>Threshold: {(threshold * 100).toFixed(0)}%</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={e => setThreshold(parseFloat(e.target.value))}
            />
          </div>

          <button
            onClick={() => setShowBreakdown(!showBreakdown)}
            className="btn btn-ghost"
          >
            {showBreakdown ? <ChevronUp /> : <ChevronDown />}
            Toggle Breakdown
          </button>

          {showBreakdown && (
            <pre>{JSON.stringify(trust, null, 2)}</pre>
          )}
        </div>

        {/* Similar Products */}
        <div className="similar-section">
          <h2><Zap /> Similar Products</h2>

          {similar.length === 0 ? (
            <p>No similar products found</p>
          ) : (
            <div className="grid-3">
              {similar.map((p, i) => (
                <Link key={i} to={`/product/${p.asin}`} className="card product-card">
                  <h3>{p.title}</h3>
                  <p>⭐ {p.rating || "N/A"}</p>
                  <p>Trust: {((p.final_trust_score || 0) * 100).toFixed(1)}%</p>
                </Link>
              ))}
            </div>
          )}
        </div>

        <Link to="/" className="btn btn-ghost">
          Back
        </Link>

      </div>
    </div>
  );
}