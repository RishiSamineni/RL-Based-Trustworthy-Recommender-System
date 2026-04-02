import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { recsAPI } from '../utils/api';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import './Products.css';

const SORT_OPTIONS = [
  { value: 'trust', label: 'Highest Trust' },
  { value: 'rating', label: 'Best Rated' },
];

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);

  const search = searchParams.get('search') || '';
  const sort = searchParams.get('sort') || 'trust';
  const minTrust = parseFloat(searchParams.get('min_trust') || 0);
  const page = parseInt(searchParams.get('page') || 1);

  const [searchInput, setSearchInput] = useState(search);

  const fetchProducts = useCallback(() => {
    setLoading(true);

    recsAPI.forYou()
      .then(r => {
        let data = r.data || [];

        if (!Array.isArray(data)) data = [];

        if (search) {
          data = data.filter(p =>
            p.title?.toLowerCase().includes(search.toLowerCase())
          );
        }

        if (minTrust > 0) {
          data = data.filter(p =>
            (p.final_trust_score || 0) >= minTrust
          );
        }

        if (sort === 'trust') {
          data.sort((a, b) =>
            (b.final_trust_score || 0) -
            (a.final_trust_score || 0)
          );
        }

        const start = (page - 1) * 12;
        const paginated = data.slice(start, start + 12);

        setProducts(paginated);
        setTotal(data.length);
        setPages(Math.ceil(data.length / 12));
      })
      .catch(err => {
        console.error("API ERROR:", err);
        setProducts([]);
      })
      .finally(() => setLoading(false));

  }, [search, sort, minTrust, page]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const setParam = (key, val) => {
    const p = new URLSearchParams(searchParams);
    if (val) p.set(key, val);
    else p.delete(key);
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

  const hasFilters = search || sort !== 'trust' || minTrust > 0;

  return (
    <div className="products-page page-enter">
      <div className="container">

        <div className="products-header">
          <div>
            <h1 className="page-title">Products</h1>
            <p className="page-sub">{total} products · sorted by {sort}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="filter-bar card">
          <form className="filter-search" onSubmit={handleSearch}>
            <Search size={14} />
            <input
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              placeholder="Search products..."
            />
            <button type="submit" className="btn btn-primary btn-sm">
              Search
            </button>
          </form>

          <div className="filter-controls">
            <SlidersHorizontal size={14} />

            <select
              value={sort}
              onChange={e => setParam('sort', e.target.value)}
              className="filter-select"
            >
              {SORT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>

            <div className="trust-filter">
              <label>Min Trust: {Math.round(minTrust * 100)}%</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={minTrust}
                onChange={e => setParam('min_trust', e.target.value)}
              />
            </div>

            {hasFilters && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={clearFilters}
              >
                <X size={13} /> Clear
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="loading-center">
            <div className="spinner" />
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <Search size={40} />
            <p>No products found.</p>
          </div>
        ) : (
          <div className="grid-4">
            {products.map((p, i) => (
              <Link key={i} to={`/product/${p.asin}`} className="card product-card">
                <h3>{p.title}</h3>
                <p>⭐ {p.rating || "N/A"}</p>
                <p>Trust: {((p.final_trust_score || 0) * 100).toFixed(1)}%</p>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="pagination">
            <button
              onClick={() => setParam('page', page - 1)}
              disabled={page === 1}
            >
              ←
            </button>

            <span>{page} / {pages}</span>

            <button
              onClick={() => setParam('page', page + 1)}
              disabled={page === pages}
            >
              →
            </button>
          </div>
        )}

      </div>
    </div>
  );
}