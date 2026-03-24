import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Shield, User, LogOut, BarChart3, Home, Package, Heart, Search, Menu, X } from 'lucide-react';
import './NavBar.css';

export default function NavBar() {
  const { user, logout } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState('');

  const isActive = (path) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);

  const handleLogout = () => {
    logout();
    addToast('Logged out successfully', 'success');
    navigate('/');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/products?q=${encodeURIComponent(query.trim())}`);
      setQuery('');
      setMobileOpen(false);
    }
  };

  const navLinks = [
    { to: '/', icon: <Home size={15} />, label: 'Home' },
    { to: '/products', icon: <Package size={15} />, label: 'Products' },
    ...(user ? [
      { to: '/for-you',   icon: <Heart size={15} />,    label: 'For You'   },
      { to: '/analytics', icon: <BarChart3 size={15} />, label: 'Analytics' },
    ] : []),
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">

        {/* Logo */}
        <Link to="/" className="nav-logo">
          <span className="logo-icon"><Shield size={22} /></span>
          <span className="logo-text">TrustRec</span>
        </Link>

        {/* Desktop links */}
        <div className="nav-links">
          {navLinks.map(({ to, icon, label }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link${isActive(to) ? ' active' : ''}`}
            >
              {icon}
              <span>{label}</span>
            </Link>
          ))}
        </div>

        {/* Search */}
        <form className="nav-search" onSubmit={handleSearch}>
          <span className="search-icon"><Search size={14} /></span>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search products…"
            aria-label="Search products"
          />
        </form>

        {/* Desktop auth */}
        <div className="nav-auth">
          {user ? (
            <div className="user-menu">
              <Link to="/profile" className="user-chip">
                <span className="user-avatar">
                  {user.username?.[0]?.toUpperCase() ?? 'U'}
                </span>
                <span className="user-name">{user.username}</span>
              </Link>
              <button onClick={handleLogout} className="nav-logout" title="Log out">
                <LogOut size={15} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="auth-links">
              <Link to="/login"    className="btn btn-ghost btn-sm">Login</Link>
              <Link to="/register" className="btn btn-primary btn-sm">Sign Up</Link>
            </div>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="mobile-toggle"
          onClick={() => setMobileOpen(o => !o)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="mobile-menu">
          {navLinks.map(({ to, icon, label }) => (
            <Link
              key={to}
              to={to}
              className={`mobile-link${isActive(to) ? ' active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              {icon}
              <span>{label}</span>
            </Link>
          ))}

          <div className="mobile-divider" />

          {user ? (
            <>
              <Link to="/profile" className="mobile-link" onClick={() => setMobileOpen(false)}>
                <User size={15} /><span>{user.username}</span>
              </Link>
              <button className="mobile-link mobile-logout" onClick={() => { handleLogout(); setMobileOpen(false); }}>
                <LogOut size={15} /><span>Logout</span>
              </button>
            </>
          ) : (
            <div className="mobile-auth">
              <Link to="/login"    className="btn btn-ghost"    onClick={() => setMobileOpen(false)}>Login</Link>
              <Link to="/register" className="btn btn-primary"  onClick={() => setMobileOpen(false)}>Sign Up</Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}