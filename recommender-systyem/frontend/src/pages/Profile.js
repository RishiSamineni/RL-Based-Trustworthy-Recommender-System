import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ratingsAPI } from '../utils/api';
import { Link } from 'react-router-dom';
import { StarRating, TrustBar } from '../components/TrustComponents';
import { User, Star, Calendar } from 'lucide-react';
import './Profile.css';

export default function Profile() {
  const { user } = useAuth();
  const [ratings, setRatings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ratingsAPI.myRatings().then(r => setRatings(r.data)).finally(() => setLoading(false));
  }, []);

  if (!user) return <div className="container" style={{ paddingTop: 80 }}>Please log in.</div>;

  const avgRating = ratings.length ? ratings.reduce((s, r) => s + r.rating, 0) / ratings.length : 0;
  const verifiedCount = ratings.filter(r => r.verified_purchase).length;

  return (
    <div className="profile-page page-enter">
      <div className="container">
        <div className="profile-header card">
          <div className="profile-avatar-lg">{user.username[0].toUpperCase()}</div>
          <div className="profile-info">
            <h1 className="profile-name">{user.username}</h1>
            <p className="profile-email">{user.email}</p>
            <div className="profile-stats">
              <div className="pstat"><Star size={14}/> {ratings.length} ratings</div>
              <div className="pstat"><Star size={14}/> {avgRating.toFixed(1)} avg</div>
              <div className="pstat">✓ {verifiedCount} verified</div>
            </div>
          </div>
        </div>

        <h2 className="section-title" style={{ margin: '32px 0 16px', fontSize: 22 }}>My Ratings</h2>
        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : ratings.length === 0 ? (
          <div className="empty-state">
            <Star size={36} style={{ color: 'var(--text3)' }} />
            <p>You haven't rated any products yet.</p>
            <Link to="/products" className="btn btn-primary">Browse Products</Link>
          </div>
        ) : (
          <div className="ratings-list">
            {ratings.map(r => (
              <Link key={r.id} to={`/products/${r.product_id}`} className="rating-row card">
                <div className="rr-left">
                  <div className="rr-title">{r.product_title}</div>
                  <div className="rr-asin">{r.product_asin}</div>
                  {r.review_text && <p className="rr-review">{r.review_text.slice(0, 120)}{r.review_text.length > 120 ? '…' : ''}</p>}
                </div>
                <div className="rr-right">
                  <StarRating value={r.rating} />
                  <div className="rr-date">
                    <Calendar size={11} />
                    {new Date(r.timestamp).toLocaleDateString()}
                  </div>
                  {r.verified_purchase && <span className="badge badge-green" style={{ fontSize: 10 }}>✓ Verified</span>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}