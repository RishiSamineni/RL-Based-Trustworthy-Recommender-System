import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Navbar from './components/NavBar';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Analytics from './pages/Analytics';
import ForYou from './pages/ForYou';
import Profile from './pages/Profile';
import { Login, Register } from './pages/Auth';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Navbar />
          <main>
            <Routes>
              <Route path="/"            element={<Home />} />
              <Route path="/products"    element={<Products />} />
              <Route path="/products/:id" element={<ProductDetail />} />
              <Route path="/analytics"   element={<Analytics />} />
              <Route path="/for-you"     element={<ForYou />} />
              <Route path="/profile"     element={<Profile />} />
              <Route path="/login"       element={<Login />} />
              <Route path="/register"    element={<Register />} />
            </Routes>
          </main>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}