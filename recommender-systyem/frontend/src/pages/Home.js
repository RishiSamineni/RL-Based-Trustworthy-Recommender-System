import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { recsAPI } from '../utils/api';
import { Shield, Zap, ArrowRight, Star } from 'lucide-react';
import './Home.css';

export default function Home() {
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    recsAPI.forYou()
      .then((res) => {
        const data = res.data;

        if (Array.isArray(data)) {
          setTopProducts(data.slice(0, 6));
        } else {
          console.warn('Unexpected Home API response:', data);
          setTopProducts([]);
        }
      })
      .catch((err) => {
        console.error('Home fetch error:', err);
        setTopProducts([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="home page-enter">
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
            AI-powered recommendations using trust + RL.
          </p>

          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary">
              Browse Products <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      <section className="how-section container">
        <h2 className="section-title">How it Works</h2>

        <div className="grid-3 how-grid">
          <div className="how-card card">
            <Star size={22} />
            <h3>Product Trust</h3>
            <p>Based on ratings and consistency.</p>
          </div>

          <div className="how-card card">
            <Shield size={22} />
            <h3>User Trust</h3>
            <p>Measures reviewer credibility.</p>
          </div>

          <div className="how-card card">
            <Zap size={22} />
            <h3>RL Recommendations</h3>
            <p>Adaptive learning-based system.</p>
          </div>
        </div>
      </section>

      <section className="products-section container">
        <div className="section-header">
          <h2 className="section-title">Top Trusted Products</h2>
          <Link to="/products" className="btn btn-ghost">
            View all <ArrowRight size={14} />
          </Link>
        </div>

        {loading ? (
          <div className="loading-center">
            <div className="spinner" />
          </div>
        ) : topProducts.length === 0 ? (
          <div className="empty-state">
            <p>No products found.</p>
          </div>
        ) : (
          <div className="grid-3">
            {topProducts.map((p, i) => (
              <Link
                key={p.asin || i}
                to={`/products/${p.asin}`}
                className="card product-card"
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                <h3>{p.title || 'Untitled Product'}</h3>

                <p>
                  <strong>ASIN:</strong> {p.asin || 'N/A'}
                </p>

                <p>
                  <strong>Rating:</strong> {p.rating ?? 'N/A'}
                </p>

                <p>
                  <strong>Trust:</strong>{' '}
                  {((p.final_trust_score || 0) * 100).toFixed(1)}%
                </p>

                {p.category && (
                  <p>
                    <strong>Category:</strong> {p.category}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}