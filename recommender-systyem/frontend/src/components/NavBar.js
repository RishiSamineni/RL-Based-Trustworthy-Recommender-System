import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Shield, User, LogOut, BarChart3, Home, Package, Heart } from 'lucide-react';
import './NavBar.css';

export default function NavBar() {
  const { user, logout } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    addToast('Logged out successfully', 'success');
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <Shield size={24} />
          <span>TrustRec</span>
        </Link>

        <div className="nav-links">
          <Link to="/" className="nav-link">
            <Home size={16} />
            <span>Home</span>
          </Link>
          <Link to="/products" className="nav-link">
            <Package size={16} />
            <span>Products</span>
          </Link>
          {user && (
            <Link to="/for-you" className="nav-link">
              <Heart size={16} />
              <span>For You</span>
            </Link>
          )}
          {user && (
            <Link to="/analytics" className="nav-link">
              <BarChart3 size={16} />
              <span>Analytics</span>
            </Link>
          )}
        </div>

        <div className="nav-auth">
          {user ? (
            <div className="user-menu">
              <Link to="/profile" className="nav-link">
                <User size={16} />
                <span>{user.username}</span>
              </Link>
              <button onClick={handleLogout} className="btn btn-ghost nav-logout">
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="auth-links">
              <Link to="/login" className="btn btn-ghost">Login</Link>
              <Link to="/register" className="btn btn-primary">Sign Up</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}