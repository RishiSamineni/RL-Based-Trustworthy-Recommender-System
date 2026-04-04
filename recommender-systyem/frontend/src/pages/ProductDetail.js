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
  const [trustCheck, setTrustCheck] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const [pageLoading, setPageLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(true);

  const [showBreakdown, setShowBreakdown] = useState(false);

  // 1) Load product + trust first
  useEffect(() => {
    if (!asin) return;

    setPageLoading(true);
    setProduct(null);
    setTrustCheck(null);

    Promise.allSettled([
      productsAPI.get(asin),
      recsAPI.getTrust(asin),
    ])
      .then(([productRes, trustRes]) => {
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
      })
      .catch((err) => {
        console.error('Detail page load error:', err);
        setProduct(null);
        setTrustCheck(null);
      })
      .finally(() => {
        setPageLoading(false);
      });
  }, [asin]);

  // 2) Load recommendations separately so they do not block page render
  useEffect(() => {
    if (!asin) return;

    setRecsLoading(true);
    setRecommendations([]);

    recsAPI.getSimilar(asin, 6, 0.3)
      .then((res) => {
        const data = res.data;

        if (Array.isArray(data)) {
          setRecommendations(data);
        } else if (Array.isArray(data?.recommendations)) {
          setRecommendations(data.recommendations);
        } else {
          setRecommendations([]);
        }
      })
      .catch((err) => {
        console.error('Recommendations load error:', err);
        setRecommendations([]);
      })
      .finally(() => {
        setRecsLoading(false);
      });
  }, [asin]);

  const getImage = (item) => {
    const imgs = item?.images || item?.meta?.images;
    if (Array.isArray(imgs) && imgs.length > 0) {
      return imgs[0]?.large || imgs[0]?.thumb || '';
    }
    return '';
  };

  if (pageLoading) {
    return (
      <div className="loading-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!product || product.error) {
    return <div className="container">Product not found</div>;
  }

  const meta = trustCheck?.meta || {};
  const trustData = trustCheck?.trust_data || {};

  const finalTrustScore =
    trustData?.final_trust_score ??
    product?.final_trust_score ??
    null;

  const productTrust = trustData?.product_trust ?? null;
  const userTrust = trustData?.user_trust ?? null;
  const sellerTrust = trustData?.seller_trust ?? null;

  const riskLabel = trustCheck?.risk_label || 'unknown';
  const threshold = trustCheck?.threshold ?? 0.5;
  const decision = trustCheck?.decision;

  const badgeColor =
    riskLabel === 'trusted'
      ? '#16a34a'
      : riskLabel === 'moderate'
        ? '#f59e0b'
        : '#ef4444';

  return (
    <div className="product-detail page-enter">
      <div className="container">
        <Link to="/products" className="btn btn-ghost" style={{ marginBottom: '20px' }}>
          Back
        </Link>

        <div
          className="card"
          style={{
            padding: '24px',
            borderRadius: '18px',
            marginBottom: '24px',
            display: 'grid',
            gridTemplateColumns: 'minmax(280px, 420px) 1fr',
            gap: '24px',
            alignItems: 'start'
          }}
        >
          <div>
            {getImage(product) ? (
              <img
                src={getImage(product)}
                alt={product.title || 'Product'}
                style={{
                  width: '100%',
                  height: '360px',
                  objectFit: 'cover',
                  borderRadius: '16px'
                }}
              />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '360px',
                  borderRadius: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#111827'
                }}
              >
                No Image
              </div>
            )}
          </div>

          <div>
            <h1 className="detail-title" style={{ marginBottom: '12px' }}>
              {product.title || meta.title || 'Product'}
            </h1>

            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: '999px',
                background: badgeColor,
                color: 'white',
                fontWeight: 600,
                marginBottom: '18px'
              }}
            >
              {decision ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
              {riskLabel.toUpperCase()}
            </div>

            <div className="tcp-scores" style={{ lineHeight: 1.9 }}>
              <p><strong>ASIN:</strong> {product.asin || asin}</p>
              <p><strong>Rating:</strong> {product.rating ?? product.average_rating ?? meta.avg_rating ?? 'N/A'}</p>
              <p>
                <strong>Final Trust Score:</strong>{' '}
                {finalTrustScore == null ? 'N/A' : `${(finalTrustScore * 100).toFixed(1)}%`}
              </p>
              <p><strong>Decision Threshold:</strong> {(threshold * 100).toFixed(1)}%</p>
              <p><strong>Decision:</strong> {decision ? 'Trusted' : 'Not Trusted'}</p>
              <p><strong>Store:</strong> {product.store || meta.store || 'N/A'}</p>
              <p><strong>Category:</strong> {product.main_category || product.category || meta.category || 'N/A'}</p>
              <p><strong>Price:</strong> {product.price ?? meta.price ?? 'N/A'}</p>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: '24px', borderRadius: '18px', marginBottom: '24px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <h2 style={{ margin: 0 }}>Transparency / Trust Breakdown</h2>

            <button
              type="button"
              onClick={() => setShowBreakdown(!showBreakdown)}
              className="btn btn-ghost"
            >
              {showBreakdown ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              {showBreakdown ? 'Hide' : 'Show'}
            </button>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '16px',
              marginTop: '20px'
            }}
          >
            <div className="card" style={{ padding: '16px' }}>
              <h3 style={{ marginBottom: '8px' }}>Product Trust</h3>
              <p style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {productTrust == null ? 'N/A' : `${(productTrust * 100).toFixed(1)}%`}
              </p>
            </div>

            <div className="card" style={{ padding: '16px' }}>
              <h3 style={{ marginBottom: '8px' }}>User Trust</h3>
              <p style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {userTrust == null ? 'N/A' : `${(userTrust * 100).toFixed(1)}%`}
              </p>
            </div>

            <div className="card" style={{ padding: '16px' }}>
              <h3 style={{ marginBottom: '8px' }}>Seller Trust</h3>
              <p style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {sellerTrust == null ? 'N/A' : `${(sellerTrust * 100).toFixed(1)}%`}
              </p>
            </div>

            <div className="card" style={{ padding: '16px' }}>
              <h3 style={{ marginBottom: '8px' }}>Final Trust</h3>
              <p style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {finalTrustScore == null ? 'N/A' : `${(finalTrustScore * 100).toFixed(1)}%`}
              </p>
            </div>
          </div>

          {showBreakdown && (
            <pre
              style={{
                whiteSpace: 'pre-wrap',
                overflowX: 'auto',
                marginTop: '20px',
                background: '#0f172a',
                padding: '16px',
                borderRadius: '12px'
              }}
            >
              {JSON.stringify(trustCheck, null, 2)}
            </pre>
          )}
        </div>

        {Array.isArray(product.description) && product.description.length > 0 && (
          <div className="card" style={{ padding: '24px', borderRadius: '18px', marginBottom: '24px' }}>
            <h2>Description</h2>
            <p>{product.description.join(' ')}</p>
          </div>
        )}

        <div className="similar-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap /> Recommended Similar Products
          </h2>

          {recsLoading ? (
            <p>Loading recommendations...</p>
          ) : recommendations.length === 0 ? (
            <p>No recommendations found for this product.</p>
          ) : (
            <div
              className="grid-3"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '20px'
              }}
            >
              {recommendations.map((item, i) => {
                const recMeta = item.meta || {};
                const recTrust = item.trust_data || {};
                const recImage =
                  Array.isArray(recMeta.images) && recMeta.images.length > 0
                    ? recMeta.images[0]?.large || ''
                    : '';

                return (
                  <Link
                    key={item.asin || i}
                    to={`/products/${item.asin}`}
                    className="card product-card"
                    style={{
                      textDecoration: 'none',
                      color: 'inherit',
                      padding: '16px',
                      borderRadius: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      minHeight: '380px'
                    }}
                  >
                    <div
                      style={{
                        width: '100%',
                        height: '180px',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        background: '#111827',
                        marginBottom: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {recImage ? (
                        <img
                          src={recImage}
                          alt={recMeta.title || 'Product'}
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                          }}
                        />
                      ) : (
                        <span>No Image</span>
                      )}
                    </div>

                    <h3
                      style={{
                        marginBottom: '10px',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        minHeight: '3em'
                      }}
                    >
                      {recMeta.title || item.asin}
                    </h3>

                    <p><strong>ASIN:</strong> {item.asin}</p>
                    <p><strong>Rating:</strong> {recMeta.avg_rating ?? 'N/A'}</p>
                    <p>
                      <strong>Trust:</strong>{' '}
                      {recTrust.final_trust_score == null
                        ? 'N/A'
                        : `${(recTrust.final_trust_score * 100).toFixed(1)}%`}
                    </p>
                    <p><strong>Risk:</strong> {item.risk_label || 'N/A'}</p>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}