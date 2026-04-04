import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { productsAPI } from '../utils/api';
import { Search } from 'lucide-react';
import './Products.css';

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const search = searchParams.get('search') || '';
  const [searchInput, setSearchInput] = useState(search);

  const fetchProducts = useCallback(() => {
    setLoading(true);

    productsAPI.list()
      .then(r => {
        let data = r.data || [];

        if (!Array.isArray(data)) data = [];

        // SEARCH
        if (search) {
          data = data.filter(p =>
            p.title?.toLowerCase().includes(search.toLowerCase())
          );
        }

        setProducts(data);
      })
      .catch(err => {
        console.error(err);
        setProducts([]);
      })
      .finally(() => setLoading(false));

  }, [search]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchParams({ search: searchInput });
  };

  const getImage = (product) => {
    if (product.images?.length > 0) {
      return product.images[0]?.large;
    }
    return '';
  };

  return (
    <div className="products-page">
      <div className="container">

        <h1>Trusted Products</h1>

        <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
          <input
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search..."
            style={{ padding: '8px', marginRight: '10px' }}
          />
          <button type="submit">Search</button>
        </form>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <div
            className="grid-4"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: '20px'
            }}
          >
            {products.map((p, i) => (
              <Link
                key={i}
                to={`/products/${p.asin}`}
                className="card"
                style={{
                  textDecoration: 'none',
                  color: 'inherit',
                  display: 'flex',
                  flexDirection: 'column',
                  padding: '16px',
                  borderRadius: '16px',
                  minHeight: '420px',
                  maxHeight: '420px',
                  overflow: 'hidden'
                }}
              >
                {/* IMAGE BOX */}
                <div
                  style={{
                    width: '100%',
                    height: '180px',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    marginBottom: '12px',
                    background: '#111827',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  {getImage(p) ? (
                    <img
                      src={getImage(p)}
                      alt={p.title}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                      }}
                    />
                  ) : (
                    <span style={{ fontSize: '12px', opacity: 0.6 }}>
                      No Image
                    </span>
                  )}
                </div>

                {/* TITLE */}
                <h3
                  style={{
                    fontSize: '1.1rem',
                    marginBottom: '10px',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    minHeight: '3em'
                  }}
                >
                  {p.title}
                </h3>

                {/* INFO */}
                <p><b>ASIN:</b> {p.asin}</p>

                <p>
                  <b>Trust:</b>{' '}
                  {p.final_trust_score == null
                    ? 'N/A'
                    : `${(p.final_trust_score * 100).toFixed(1)}%`}
                </p>

                {/* PUSH BOTTOM */}
                <div style={{ marginTop: 'auto' }} />
              </Link>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}