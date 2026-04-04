import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { productsAPI } from '../utils/api';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import './Products.css';

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const search = searchParams.get('search') || '';
  const page = parseInt(searchParams.get('page') || 1);

  const [searchInput, setSearchInput] = useState(search);

  const fetchProducts = useCallback(() => {
    setLoading(true);

    productsAPI.list()
      .then(r => {
        let data = r.data || [];

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

        <form onSubmit={handleSearch}>
          <input
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Search..."
          />
          <button type="submit">Search</button>
        </form>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="grid-4">
            {products.map((p, i) => (
              <Link key={i} to={`/products/${p.asin}`} className="card">

                {getImage(p) && (
                  <img src={getImage(p)} alt={p.title} />
                )}

                <h3>{p.title}</h3>

                <p><b>ASIN:</b> {p.asin}</p>

                <p>
                  <b>Trust:</b>{' '}
                  {p.final_trust_score == null
                    ? 'N/A'
                    : `${(p.final_trust_score * 100).toFixed(1)}%`}
                </p>

              </Link>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}