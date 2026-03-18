import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { productsAPI, recsAPI, ratingsAPI } from '../utils/api';
import { TrustBadge, TrustBreakdown, StarRating, MethodBadges, TrustBar } from '../components/TrustComponents';
import ProductCard from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Shield, ShieldCheck, ShieldAlert, ChevronDown, ChevronUp, MessageSquare, Zap } from 'lucide-react';
import './ProductDetail.css';

export default function ProductDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { addToast } = useToast();

  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [trustCheck, setTrustCheck] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recLoading, setRecLoading] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showExplain, setShowExplain] = useState(null);

  // Rating state
  const [ratingVal, setRatingVal] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Threshold slider for interactive trust check (mirrors RL threshold concept)
  const [threshold, setThreshold] = useState(0.5);

  useEffect(() => {
    setLoading(true);
    productsAPI.get(id).then(r => {
      setProduct(r.data);
      if (r.data.user_rating) setRatingVal(r.data.user_rating);

      // Load similar products + trust check in parallel
      setRecLoading(true);
      Promise.all([
        recsAPI.similar(r.data.asin, { top_n: 6, min_trust: 0.3 }),
        recsAPI.trustCheck(r.data.asin, { threshold })
      ]).then(([sRes, tRes]) => {
        setSimilar(sRes.data.recommendations || []);
        setTrustCheck(tRes.data);
      }).finally(() => setRecLoading(false));
    }).catch(() => addToast('Product not found', 'error'))
      .finally(() => setLoading(false));
  }, [id]);

  // Recompute trust check when threshold changes
  useEffect(() => {
    if (!product) return;
    recsAPI.trustCheck(product.asin, { threshold }).then(r => setTrustCheck(r.data));
  }, [threshold, product?.asin]);

  const handleRating = async () => {
    if (!user) { addToast('Please log in to rate products', 'error'); return; }
    if (ratingVal < 1) { addToast('Please select a star rating', 'error'); return; }
    setSubmitting(true);
    try {
      const r = await ratingsAPI.submit({ product_id: product.id, rating: ratingVal, review_text: reviewText });
      setProduct(prev => ({ ...prev, ...r.data.product, reviews: prev.reviews }));
      addToast('Rating submitted! Trust scores updated.', 'success');
      setReviewText('');
    } catch (e) {
      addToast(e.response?.data?.error || 'Error submitting rating', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading-center" style={{ paddingTop: 120 }}><div className="spinner" /></div>;
  if (!product) return <div className="container" style={{ paddingTop: 80 }}>Product not found.</div>;

  const trust = product.trust || {};
  const isVerdict = trustCheck?.rl_decision;
  const isTrusty = isVerdict?.is_trustworthy;

  return (
    <div className="product-detail page-enter">
      <div className="container">

        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/products">Products</Link> / {product.category} / <span>{product.title.slice(0, 40)}…</span>
        </div>

        <div className="detail-grid">
          {/* LEFT: Product info */}
          <div className="detail-left">
            <div className="detail-img-wrap">
              <img src={product.image_url} alt={product.title}
                onError={e => { e.target.src = `https://picsum.photos/seed/${product.asin}/600/400`; }} />
              <div className="detail-img-badge">
                <TrustBadge score={trust.final_trust_score || 0} size="lg" />
              </div>
            </div>

            {/* Interactive Trust Check Panel — mirrors display_product_recommendation */}
            <div className="trust-check-panel card">
              <div className="tcp-header">
                {isTrusty
                  ? <ShieldCheck size={20} color="var(--green)" />
                  : <ShieldAlert size={20} color="var(--red)" />}
                <h3>Trust Verdict</h3>
                <span className={`badge ${isTrusty ? 'badge-green' : 'badge-red'}`} style={{ marginLeft: 'auto' }}>
                  {isVerdict?.verdict || '—'}
                </span>
              </div>

              <div className="tcp-scores">
                <div className="tcp-score">
                  <span>Product Trust</span>
                  <strong style={{ color: 'var(--accent2)' }}>{(trust.product_trust * 100).toFixed(1)}%</strong>
                </div>
                <div className="tcp-score">
                  <span>Seller Trust</span>
                  <strong style={{ color: 'var(--purple)' }}>{(trust.seller_trust * 100).toFixed(1)}%</strong>
                </div>
                <div className="tcp-score">
                  <span>Final Trust</span>
                  <strong style={{ color: trust.final_trust_score >= 0.5 ? 'var(--green2)' : 'var(--red)' }}>
                    {(trust.final_trust_score * 100).toFixed(1)}%
                  </strong>
                </div>
              </div>

              {/* RL Threshold slider — mirrors RL agent threshold concept */}
              <div className="tcp-threshold">
                <label>
                  RL Threshold: <strong style={{ color: 'var(--accent2)' }}>{(threshold * 100).toFixed(0)}%</strong>
                </label>
                <input type="range" min="0" max="1" step="0.05" value={threshold}
                  onChange={e => setThreshold(parseFloat(e.target.value))} />
                <p className="tcp-reason">{isVerdict?.reason}</p>
              </div>

              <button className="btn btn-ghost btn-sm" style={{ marginTop: 8, width: '100%', justifyContent: 'center' }}
                onClick={() => setShowBreakdown(!showBreakdown)}>
                {showBreakdown ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
                {showBreakdown ? 'Hide' : 'Show'} Detailed Breakdown
              </button>

              {showBreakdown && (
                <div className="trust-breakdown-wrap">
                  <TrustBreakdown trust={trust} />
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: Details */}
          <div className="detail-right">
            <div className="detail-cat badge badge-blue">{product.category}</div>
            <h1 className="detail-title">{product.title}</h1>
            <div className="detail-meta">
              <StarRating value={product.avg_rating} />
              <span className="meta-count">{product.avg_rating?.toFixed(1)} ({product.rating_count} reviews)</span>
              <span className="detail-price">${product.price?.toFixed(2)}</span>
            </div>

            <p className="detail-desc">{product.description}</p>

            {/* Features */}
            {product.features_list?.length > 0 && (
              <div className="detail-features">
                <h4>Key Features</h4>
                <ul>
                  {product.features_list.map((f, i) => <li key={i}>✓ {f}</li>)}
                </ul>
              </div>
            )}

            {/* ASIN */}
            <div className="detail-asin">ASIN: <code>{product.asin}</code></div>

            {/* Rate this product */}
            <div className="rating-form card">
              <div className="rating-form-header">
                <MessageSquare size={16} />
                <h4>{user ? 'Rate this Product' : 'Log in to Rate'}</h4>
              </div>
              {user ? (
                <>
                  <div className="rating-stars-row">
                    <StarRating value={ratingVal} interactive onChange={setRatingVal} size={26} />
                    <span className="rating-val-label">{ratingVal > 0 ? `${ratingVal} / 5` : 'Select'}</span>
                  </div>
                  <textarea
                    className="review-input"
                    placeholder="Write a review (optional)…"
                    value={reviewText}
                    onChange={e => setReviewText(e.target.value)}
                    rows={3}
                  />
                  <button className="btn btn-primary" onClick={handleRating} disabled={submitting}>
                    {submitting ? 'Submitting…' : 'Submit Rating'}
                  </button>
                </>
              ) : (
                <Link to="/login" className="btn btn-ghost" style={{ justifyContent: 'center' }}>Log in to rate</Link>
              )}
            </div>

            {/* Reviews */}
            {product.reviews?.length > 0 && (
              <div className="reviews-section">
                <h4>Recent Reviews</h4>
                {product.reviews.map((r, i) => (
                  <div key={i} className="review-item">
                    <div className="review-header">
                      <div className="review-avatar">{r.username[0].toUpperCase()}</div>
                      <strong className="review-user">{r.username}</strong>
                      <StarRating value={r.rating} size={12} />
                      {r.verified && <span className="badge badge-green" style={{ fontSize: 10 }}>✓ Verified</span>}
                    </div>
                    <p className="review-text">{r.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Similar Trustworthy Products — mirrors display_similar_product_recommendations */}
        <div className="similar-section">
          <div className="section-header">
            <div>
              <h2 className="section-title" style={{ fontSize: 22 }}>
                <Zap size={18} style={{ color: 'var(--accent2)' }} /> Similar Trustworthy Products
              </h2>
              <p style={{ color: 'var(--text2)', fontSize: 13, marginTop: 4 }}>
                Hybrid collaborative + content-based recommendations (min trust ≥ 30%)
              </p>
            </div>
          </div>

          {recLoading ? (
            <div className="loading-center"><div className="spinner" /></div>
          ) : similar.length === 0 ? (
            <div className="empty-state" style={{ padding: 40 }}>No similar trustworthy products found.</div>
          ) : (
            <div className="grid-3">
              {similar.map((rec, i) => (
                <div key={rec.product.id} className="sim-card-wrap">
                  <ProductCard product={rec.product} showSimilarity similarity={rec.similarity} />
                  <div className="sim-meta">
                    <MethodBadges breakdown={rec.method_breakdown} />
                    <button className="explain-btn"
                      onClick={() => setShowExplain(showExplain === i ? null : i)}>
                      {showExplain === i ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
                      Explain
                    </button>
                  </div>
                  {showExplain === i && (
                    <div className="explain-panel card">
                      <pre className="explain-text">{rec.explanation}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}