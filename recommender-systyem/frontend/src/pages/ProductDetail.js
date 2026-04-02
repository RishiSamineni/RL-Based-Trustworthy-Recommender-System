import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { productsAPI, recsAPI } from '../utils/api';
import {
  ShieldCheck,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Zap
} from 'lucide-react';
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
    if (!asin) return;

    setLoading(true);

    Promise.allSettled([
      productsAPI.get(asin),
      recsAPI.getTrust(asin),
      recsAPI.getSimilar(asin, 6, 0.3),
    ])
      .then((results) => {
        const productRes = results[0];
        const trustRes = results[1];
        const similarRes = results[2];

        if (productRes.status === 'fulfilled') {
          setProduct(productRes.value.data);
        } else {
          setProduct(null);
        }

        if (trustRes.status === 'fulfilled') {
          setTrustCheck(trustRes.value.data);
        } else {
          setTrustCheck(null);
        }

        if (
          similarRes.status === 'fulfilled' &&
          Array.isArray(similarRes.value.data)
        ) {
          setSimilar(similarRes.value.data);
        } else {
          setSimilar([]);
        }
      })
      .catch((err) => {
        console.error('Product detail error:', err);
        setProduct(null);
        setTrustCheck(null);
        setSimilar([]);
      })
      .finally(() => setLoading(false));
  }, [asin]);

  const getImage = (item) => {
    if (Array.isArray(item?.images) && item.images.length > 0) {
      return item.images[0]?.large || item.images[0]?.thumb || '';
    }
    return '';
  };

  if (loading) {
    return (
      <div className="loading-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!product || product.error) {
    return <div className="container">Product not found</div>;
  }

  const finalTrustScore =
    trustCheck?.trust?.final_trust_score ??
    trustCheck?.final_trust_score ??
    product?.final_trust_score ??
    0;

  const isTrusty =
    trustCheck?.rl_decision?.is_trustworthy ??
    (finalTrustScore >= threshold);

  return (
    <div className="product-detail page-enter">
      <div className="container">
        <h1 className="detail-title">{product.title || 'Product'}</h1>

        {getImage(product) ? (
          <img
            src={getImage(product)}
            alt={product.title || 'Product'}
            style={{
              width: '100%',
              maxWidth: '500px',
              height: 'auto',
              borderRadius: '16px',
              marginBottom: '20px'
            }}
          />
        ) : null}

        <div className="trust-check-panel card">
          <div className="tcp-header">
            {isTrusty ? <ShieldCheck color="green" /> : <ShieldAlert color="red" />}
            <h3>Trust Verdict</h3>
          </div>

          <div className="tcp-scores">
            <p><strong>ASIN:</strong> {product.asin || asin}</p>
            <p><strong>Rating:</strong> {product.rating ?? product.average_rating ?? 'N/A'}</p>
            <p><strong>Trust:</strong> {(finalTrustScore * 100).toFixed(1)}%</p>
            <p><strong>Store:</strong> {product.store || 'N/A'}</p>
            <p><strong>Category:</strong> {product.main_category || product.category || 'N/A'}</p>
            <p><strong>Price:</strong> {product.price ?? 'N/A'}</p>
          </div>

          <div>
            <label>Threshold: {(threshold * 100).toFixed(0)}%</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
            />
          </div>

          <button
            type="button"
            onClick={() => setShowBreakdown(!showBreakdown)}
            className="btn btn-ghost"
          >
            {showBreakdown ? <ChevronUp /> : <ChevronDown />}
            Transparency / Breakdown
          </button>

          {showBreakdown && (
            <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto' }}>
              {JSON.stringify(trustCheck || product, null, 2)}
            </pre>
          )}
        </div>

        {Array.isArray(product.description) && product.description.length > 0 && (
          <div className="card" style={{ marginTop: '20px', padding: '20px' }}>
            <h3>Description</h3>
            <p>{product.description.join(' ')}</p>
          </div>
        )}

        <div className="similar-section">
          <h2>
            <Zap /> Recommendations
          </h2>

          {similar.length === 0 ? (
            <p>No similar products found</p>
          ) : (
            <div className="grid-3">
              {similar.map((p, i) => (
                <Link
                  key={p.asin || i}
                  to={`/products/${p.asin}`}
                  className="card product-card"
                  style={{ textDecoration: 'none', color: 'inherit' }}
                >
                  {getImage(p) ? (
                    <img
                      src={getImage(p)}
                      alt={p.title || 'Product'}
                      style={{
                        width: '100%',
                        height: '160px',
                        objectFit: 'cover',
                        borderRadius: '12px',
                        marginBottom: '12px'
                      }}
                    />
                  ) : null}

                  <h3>{p.title || 'Untitled Product'}</h3>
                  <p><strong>ASIN:</strong> {p.asin || 'N/A'}</p>
                  <p><strong>Rating:</strong> {p.rating ?? 'N/A'}</p>
                  <p>
                    <strong>Trust:</strong>{' '}
                    {((p.final_trust_score || 0) * 100).toFixed(1)}%
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>

        <Link to="/products" className="btn btn-ghost">
          Back
        </Link>
      </div>
    </div>
  );
}