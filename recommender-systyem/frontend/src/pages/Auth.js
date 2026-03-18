import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Shield, Eye, EyeOff } from 'lucide-react';
import './Auth.css';

export function Login() {
  const { login } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.email, form.password);
      addToast('Welcome back!', 'success');
      navigate('/');
    } catch (err) {
      addToast(err.response?.data?.error || 'Login failed', 'error');
    } finally { setLoading(false); }
  };

  // Demo login helper
  const demoLogin = async () => {
    setLoading(true);
    try {
      await login('alice@example.com', 'password123');
      addToast('Logged in as alice_dev (demo)', 'success');
      navigate('/');
    } catch { addToast('Demo login failed', 'error'); }
    finally { setLoading(false); }
  };

  return (
    <div className="auth-page page-enter">
      <div className="auth-card card">
        <div className="auth-logo"><Shield size={28} style={{ color: 'var(--accent2)' }} /></div>
        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-sub">Log in to your TrustRec account</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
              placeholder="you@example.com" required />
          </div>
          <div className="field">
            <label>Password</label>
            <div className="pw-wrap">
              <input type={showPw ? 'text' : 'password'} value={form.password}
                onChange={e => setForm({...form, password: e.target.value})}
                placeholder="••••••••" required />
              <button type="button" className="pw-toggle" onClick={() => setShowPw(!showPw)}>
                {showPw ? <EyeOff size={14}/> : <Eye size={14}/>}
              </button>
            </div>
          </div>
          <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
            {loading ? 'Logging in…' : 'Log in'}
          </button>
        </form>

        <button className="btn btn-ghost demo-btn" onClick={demoLogin} disabled={loading}>
          Try Demo Account
        </button>

        <p className="auth-switch">Don't have an account? <Link to="/register">Sign up</Link></p>
      </div>
    </div>
  );
}

export function Register() {
  const { register } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 6) { addToast('Password must be at least 6 characters', 'error'); return; }
    setLoading(true);
    try {
      await register(form.username, form.email, form.password);
      addToast('Account created!', 'success');
      navigate('/');
    } catch (err) {
      addToast(err.response?.data?.error || 'Registration failed', 'error');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page page-enter">
      <div className="auth-card card">
        <div className="auth-logo"><Shield size={28} style={{ color: 'var(--accent2)' }} /></div>
        <h2 className="auth-title">Create account</h2>
        <p className="auth-sub">Join TrustRec to get personalised recommendations</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label>Username</label>
            <input value={form.username} onChange={e => setForm({...form, username: e.target.value})}
              placeholder="your_username" required minLength={3} />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
              placeholder="you@example.com" required />
          </div>
          <div className="field">
            <label>Password</label>
            <div className="pw-wrap">
              <input type={showPw ? 'text' : 'password'} value={form.password}
                onChange={e => setForm({...form, password: e.target.value})}
                placeholder="Min 6 characters" required minLength={6} />
              <button type="button" className="pw-toggle" onClick={() => setShowPw(!showPw)}>
                {showPw ? <EyeOff size={14}/> : <Eye size={14}/>}
              </button>
            </div>
          </div>
          <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-switch">Already have an account? <Link to="/login">Log in</Link></p>
      </div>
    </div>
  );
}