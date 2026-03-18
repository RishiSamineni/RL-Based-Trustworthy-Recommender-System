import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productsAPI, analyticsAPI } from '../utils/api';
import ProductCard from '../components/ProductCard';
import { TrustBar } from '../components/TrustComponents';
import { Shield, ShieldCheck, Search, BarChart2, Zap, ArrowRight, Star } from 'lucide-react';
import './Home.css';

export default function Home() {
  const [topProducts, setTopProducts] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      productsAPI.list({ sort: 'trust', per_page: 6 }),
      analyticsAPI.overview()
    ]).then(([pRes, aRes]) => {
      setTopProducts(pRes.data.products);
      setOverview(aRes.data);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="home page-enter">
      {/* Hero */}
      <section className="hero">
        <div className="hero-glow" />
        <div className="container hero-inner">
          <div className="hero-badge">
            <Shield size={13} /> Trustworthy AI Recommendations
          </div>
          <h1 className="hero-title">
            Discover Software You Can
            <span className="hero-accent"> Actually Trust</span>
          </h1>
          <p className="hero-sub">
            Our system scores every product using collaborative filtering, content-based similarity,
            and a multi-dimensional trust model — so you get recommendations that are both
            <em> relevant</em> and <em>trustworthy</em>.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary">
              Browse Products <ArrowRight size={16} />
            </Link>
            <Link to="/analytics" className="btn btn-ghost">
              <BarChart2 size={16} /> View Analytics
            </Link>
          </div>

          {/* Stats strip */}
          {overview && (
            <div className="stats-strip">
              {[
                { label: 'Products',      value: overview.total_products },
                { label: 'Reviews',       value: overview.total_ratings },
                { label: 'Trust Rate',    value: `${overview.trust_rate}%` },
                { label: 'Avg Trust',     value: `${Math.round(overview.avg_trust_score * 100)}%` },
              ].map(s => (
                <div key={s.label} className="stat-item">
                  <div className="stat-value">{s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* How it works */}
      <section className="how-section container">
        <h2 className="section-title">How the Trust Engine Works</h2>
        <p className="section-sub">Adapted from a published trustworthy recommender pipeline</p>
        <div className="grid-3 how-grid">
          {[
            { icon: <Star size={22}/>,       title: 'Product Trust',   color: 'var(--amber)',
              desc: 'Computed from avg rating, verified purchase ratio, review count confidence, price normality, and title–review TF-IDF similarity.' },
            { icon: <Shield size={22}/>,     title: 'User Trust',      color: 'var(--green)',
              desc: 'Weighted from verified purchase ratio, helpful vote ratio, rating consistency, and review text quality for each reviewer.' },
            { icon: <Zap size={22}/>,        title: 'Hybrid Recs',     color: 'var(--accent)',
              desc: 'Recommendations combine 60% collaborative filtering (co-review patterns) + 40% content similarity (category, title, price, features).' },
          ].map(h => (
            <div key={h.title} className="how-card card">
              <div className="how-icon" style={{ background: `${h.color}22`, color: h.color }}>{h.icon}</div>
              <h3 className="how-title">{h.title}</h3>
              <p className="how-desc">{h.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trust formula */}
      <section className="formula-section container">
        <div className="formula-card card">
          <div className="formula-label">Final Trust Formula</div>
          <div className="formula-eq">
            <span className="f-var" style={{color:'var(--green2)'}}>Final</span>
            <span className="f-op"> = </span>
            <span className="f-w">0.55 ×</span>
            <span className="f-var" style={{color:'var(--accent2)'}}>P<sub>trust</sub></span>
            <span className="f-op"> + </span>
            <span className="f-w">0.35 ×</span>
            <span className="f-var" style={{color:'var(--amber)'}}>U<sub>trust</sub></span>
            <span className="f-op"> + </span>
            <span className="f-w">0.10 ×</span>
            <span className="f-var" style={{color:'var(--purple)'}}>S<sub>trust</sub></span>
          </div>
          <div className="formula-legend">
            <span style={{color:'var(--accent2)'}}>P = Product Trust</span>
            <span style={{color:'var(--amber)'}}>U = User Trust</span>
            <span style={{color:'var(--purple)'}}>S = Seller Trust</span>
          </div>
        </div>
      </section>

      {/* Top trusted products */}
      <section className="products-section container">
        <div className="section-header">
          <div>
            <h2 className="section-title">Top Trusted Products</h2>
            <p className="section-sub">Ranked by final combined trust score</p>
          </div>
          <Link to="/products" className="btn btn-ghost">
            View all <ArrowRight size={14}/>
          </Link>
        </div>
        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : (
          <div className="grid-3">
            {topProducts.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        )}
      </section>
    </div>
  );
}