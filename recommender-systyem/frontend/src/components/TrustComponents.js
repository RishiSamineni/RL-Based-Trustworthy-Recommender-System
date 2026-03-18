import React from 'react';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

/* ── Trust Score Badge ──────────────────────────────── */
export function TrustBadge({ score, size = 'md' }) {
  const pct = Math.round(score * 100);
  let cls, Icon, label;
  if (score >= 0.7) { cls = 'badge-green';  Icon = ShieldCheck; label = 'Trusted'; }
  else if (score >= 0.5) { cls = 'badge-amber'; Icon = Shield; label = 'Moderate'; }
  else                  { cls = 'badge-red';   Icon = ShieldAlert; label = 'Risky'; }

  const fontSize = size === 'lg' ? 14 : 12;
  return (
    <span className={`badge ${cls}`} style={{ fontSize }}>
      <Icon size={size === 'lg' ? 14 : 11} />
      {label} · {pct}%
    </span>
  );
}

/* ── Trust Score Bar ────────────────────────────────── */
export function TrustBar({ score, label, showPct = true }) {
  const pct = Math.round(score * 100);
  let color;
  if (score >= 0.7)      color = 'var(--green)';
  else if (score >= 0.5) color = 'var(--amber)';
  else                   color = 'var(--red)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {(label || showPct) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text2)' }}>
          {label && <span>{label}</span>}
          {showPct && <span style={{ color, fontWeight: 600 }}>{pct}%</span>}
        </div>
      )}
      <div className="trust-bar-wrap">
        <div className="trust-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

/* ── Star Rating Display ────────────────────────────── */
export function StarRating({ value, max = 5, size = 14, interactive = false, onChange }) {
  const [hover, setHover] = React.useState(0);
  const stars = Array.from({ length: max }, (_, i) => i + 1);
  return (
    <div className="stars" style={{ gap: 2 }}>
      {stars.map(s => (
        <span
          key={s}
          className={`star ${s <= (hover || value) ? 'star-full' : 'star-empty'}`}
          style={{ fontSize: size, cursor: interactive ? 'pointer' : 'default' }}
          onMouseEnter={() => interactive && setHover(s)}
          onMouseLeave={() => interactive && setHover(0)}
          onClick={() => interactive && onChange && onChange(s)}
        >★</span>
      ))}
    </div>
  );
}

/* ── Trust Breakdown Panel ──────────────────────────── */
export function TrustBreakdown({ trust }) {
  if (!trust) return null;
  const { product_trust, user_trust, seller_trust, final_trust_score, details } = trust;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <TrustBar score={final_trust_score}  label="Final Trust Score" />
      <TrustBar score={product_trust}      label="Product Trust" />
      {user_trust    != null && <TrustBar score={user_trust}    label="User Trust" />}
      {seller_trust  != null && <TrustBar score={seller_trust}  label="Seller Trust" />}
      {details && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Detail breakdown</div>
          {Object.entries(details).map(([k, v]) => (
            <TrustBar key={k} score={v} label={k.replace(/_/g, ' ')} />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Method Breakdown Pills ─────────────────────────── */
export function MethodBadges({ breakdown }) {
  if (!breakdown) return null;
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
      <span className="badge badge-blue">
        CF {Math.round(breakdown.collaborative * 100)}%
      </span>
      <span className="badge badge-purple">
        CB {Math.round(breakdown.content * 100)}%
      </span>
    </div>
  );
}