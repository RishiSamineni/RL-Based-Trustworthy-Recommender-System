import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { productsAPI } from '../utils/api';
import ProductCard from '../components/ProductCard';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import './Products.css';

const SORT_OPTIONS = [
  { value: 'trust',       label: 'Highest Trust' },
  { value: 'rating',      label: 'Best Rated' },
  { value: 'price_asc',   label: 'Price: Low → High' },
  { value: 'price_desc',  label: 'Price: High → Low' },
];

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);

  const search   = searchParams.get('search') || '';
  const category = searchParams.get('category') || '';
  const sort     = searchParams.get('sort') || 'trust';
  const minTrust = parseFloat(searchParams.get('min_trust') || 0);
  const page     = parseInt(searchParams.get('page') || 1);

  const [searchInput, setSearchInput] = useState(search);

  const fetchProducts = useCallback(() => {
    setLoading(true);
    productsAPI.list({ search, category, sort, min_trust: minTrust, page, per_page: 12 })
      .then(r => {
        setProducts(r.data.products);
        setTotal(r.data.total);
        setPages(r.data.pages);
        if (r.data.categories.length) setCategories(r.data.categories);
      })
      .finally(() => setLoading(false));
  }, [search, category, sort, minTrust, page]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  const setParam = (key, val) => {
    const p = new URLSearchParams(searchParams);
    if (val) p.set(key, val); else p.delete(key);
    p.delete('page');
    setSearchParams(p);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setParam('search', searchInput);
  };

  const clearFilters = () => {
    setSearchInput('');
    setSearchParams({});
  };

  const hasFilters = search || category || sort !== 'trust' || minTrust > 0;

  return (
    <div className="products-page page-enter">
      <div className="container">
        <div className="products-header">
          <div>
            <h1 className="page-title">Software Products</h1>
            <p className="page-sub">{total} products · sorted by {sort}</p>
          </div>
        </div>

        {/* Filter bar */}
        <div className="filter-bar card">
          <form className="filter-search" onSubmit={handleSearch}>
            <Search size={14} />
            <input
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              placeholder="Search by title…"
            />
            <button type="submit" className="btn btn-primary btn-sm">Search</button>
          </form>

          <div className="filter-controls">
            <SlidersHorizontal size={14} style={{ color: 'var(--text3)' }} />

            <select value={category} onChange={e => setParam('category', e.target.value)} className="filter-select">
              <option value="">All Categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>

            <select value={sort} onChange={e => setParam('sort', e.target.value)} className="filter-select">
              {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>

            <div className="trust-filter">
              <label>Min Trust: <strong>{Math.round(minTrust * 100)}%</strong></label>
              <input type="range" min="0" max="1" step="0.1" value={minTrust}
                onChange={e => setParam('min_trust', e.target.value)} />
            </div>

            {hasFilters && (
              <button className="btn btn-ghost btn-sm" onClick={clearFilters}>
                <X size={13}/> Clear
              </button>
            )}
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <Search size={40} style={{ color: 'var(--text3)' }} />
            <p>No products match your filters.</p>
            <button className="btn btn-ghost" onClick={clearFilters}>Clear filters</button>
          </div>
        ) : (
          <div className="grid-4">
            {products.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            {Array.from({ length: pages }, (_, i) => i + 1).map(pg => (
              <button key={pg}
                className={`page-btn ${pg === page ? 'active' : ''}`}
                onClick={() => { const p = new URLSearchParams(searchParams); p.set('page', pg); setSearchParams(p); }}>
                {pg}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}