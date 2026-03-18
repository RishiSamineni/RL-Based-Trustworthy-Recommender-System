import React from 'react';
import { Link } from 'react-router-dom';
import { TrustBadge, StarRating, TrustBar } from './TrustComponents';
import { DollarSign } from 'lucide-react';
import './ProductCard.css';

export default function ProductCard({ product, showSimilarity = false, similarity, explanation }) {
  const trust = product.trust || {};
  const finalTrust = trust.final_trust_score ?? 0;

  return (
    <Link to={`/products/${product.id}`} className="product-card">
      <div className="product-card-img">
        <img src={product.image_url} alt={product.title} onError={e => { e.target.src = `https://picsum.photos/seed/${product.asin}/300/200`; }} />
        <div className="product-card-overlay">
          <TrustBadge score={finalTrust} />
        </div>
      </div>

      <div className="product-card-body">
        <div className="product-card-cat">{product.category}</div>
        <h3 className="product-card-title">{product.title}</h3>

        <div className="product-card-meta">
          <StarRating value={product.avg_rating} />
          <span className="meta-count">({product.rating_count})</span>
          <span className="meta-price">
            <DollarSign size={12} />{product.price?.toFixed(2)}
          </span>
        </div>

        <div className="product-card-trust">
          <TrustBar score={finalTrust} label="Trust" />
        </div>

        {showSimilarity && similarity != null && (
          <div className="product-card-sim">
            <span className="badge badge-blue">
              {Math.round(similarity * 100)}% similar
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}