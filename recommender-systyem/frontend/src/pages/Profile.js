import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { User } from 'lucide-react';
import './Profile.css';

export default function Profile() {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="container" style={{ paddingTop: 80 }}>
        Please log in.
      </div>
    );
  }

  return (
    <div className="profile-page page-enter">
      <div className="container">

        {/* Profile Header */}
        <div className="profile-header card">
          <div className="profile-avatar-lg">
            {user.username ? user.username[0].toUpperCase() : 'U'}
          </div>

          <div className="profile-info">
            <h1 className="profile-name">
              {user.username || 'User'}
            </h1>

            <p className="profile-email">
              {user.email}
            </p>

            <div className="profile-stats">
              <div className="pstat">
                <User size={14} /> Recommender User
              </div>
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="empty-state" style={{ marginTop: 40 }}>
          <p>This is a demo profile.</p>
          <p>Ratings and history are not enabled in this system.</p>

          <Link to="/" className="btn btn-primary">
            Go to Home
          </Link>
        </div>

      </div>
    </div>
  );
}