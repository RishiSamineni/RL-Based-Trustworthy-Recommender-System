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
  const page = parseInt(searchParams.get('page') || 1, 10);

  const [searchInput, setSearchInput] = useState(search);

  const fetchProducts = useCallback(() => {
    setLoading(true);

    recsAPI.forYou()
      .then((r) => {
        let data = r.data || [];
        if (!Array.isArray(data)) data = [];

        if (search) {
          data = data.filter((p) =>
            (p.title || '').toLowerCase().includes(search.toLowerCase())
          );
        }

        if (minTrust > 0) {
          data = data.filter((p) => (p.final_trust_score || 0) >= minTrust);
        }

        if (sort === 'trust') {
          data.sort(
            (a, b) => (b.final_trust_score || 0) - (a.final_trust_score || 0)
          );
        } else if (sort === 'rating') {
          data.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        }

        const perPage = 12;
        const totalItems = data.length;
        const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
        const safePage = Math.min(Math.max(page, 1), totalPages);
        const start = (safePage - 1) * perPage;
        const paginated = data.slice(start, start + perPage);

        setProducts(paginated);
        setTotal(totalItems);
        setPages(totalPages);
      })
      .catch((err) => {
        console.error('API ERROR:', err);
        setProducts([]);
        setTotal(0);
        setPages(1);
      })
      .finally(() => setLoading(false));
  }, [search, sort, minTrust, page]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const setParam = (key, val) => {
    const p = new URLSearchParams(searchParams);

    if (val !== '' && val !== null && val !== undefined) {
      p.set(key, val);
    } else {
      p.delete(key);
    }

    if (key !== 'page') {
      p.delete('page');
    }

    setSearchParams(p);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setParam('search', searchInput.trim());
  };

  const clearFilters = () => {
    setSearchInput('');
    setSearchParams({});
  };

  const hasFilters = search || sort !== 'trust' || minTrust > 0;

  const getImage = (product) => {
    if (Array.isArray(product.images) && product.images.length > 0) {
      return product.images[0]?.large || product.images[0]?.thumb || '';
    }
    return '';
  };

  return (
    <div className="products-page page-enter">
      <div className="container">
        <div className="products-header">
          <div>
            <h1 className="page-title">Products</h1>
            <p className="page-sub">{total} products · sorted by {sort}</p>
          </div>
        </div>

        <div className="filter-bar card">
          <form className="filter-search" onSubmit={handleSearch}>
            <Search size={14} />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
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
              onChange={(e) => setParam('sort', e.target.value)}
              className="filter-select"
            >
              {SORT_OPTIONS.map((o) => (
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
                onChange={(e) => setParam('min_trust', e.target.value)}
              />
            </div>

            {hasFilters && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={clearFilters}
              >
                <X size={13} /> Clear
              </button>
            )}
          </div>
        </div>

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
              <Link
                key={p.asin || i}
                to={`/products/${p.asin}`}
                className="card product-card"
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                {getImage(p) ? (
                  <img
                    src={getImage(p)}
                    alt={p.title || 'Product'}
                    style={{
                      width: '100%',
                      height: '180px',
                      objectFit: 'cover',
                      borderRadius: '12px',
                      marginBottom: '12px'
                    }}
                  />
                ) : null}

                <h3>{p.title || 'Untitled Product'}</h3>

                <p><strong>ASIN:</strong> {p.asin || 'N/A'}</p>
                <p><strong>Rating:</strong> {p.rating ?? 'N/A'}</p>
                <p>
                  <strong>Trust:</strong>{' '}
                  {((p.final_trust_score || 0) * 100).toFixed(1)}%
                </p>

                {p.category && (
                  <p><strong>Category:</strong> {p.category}</p>
                )}
              </Link>
            ))}
          </div>
        )}

        {pages > 1 && (
          <div className="pagination">
            <button
              type="button"
              onClick={() => setParam('page', page - 1)}
              disabled={page === 1}
            >
              ←
            </button>

            <span>{page} / {pages}</span>

            <button
              type="button"
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