import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../app/AuthContext';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'var(--color-bg)' }}>
      <div className="card" style={{ width: 380, maxWidth: '90vw' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, textAlign: 'center', marginBottom: '1.5rem' }}>登录 MailPilot</h1>
        {error && (
          <div style={{ padding: '0.5rem 0.75rem', marginBottom: '1rem', borderRadius: 'var(--radius)', background: '#fef2f2', color: '#991b1b', fontSize: '0.875rem' }}>{error}</div>
        )}
        <form onSubmit={handleSubmit}>
          <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--color-text-muted)' }}>邮箱</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
            style={{ width: '100%', marginTop: '0.25rem', marginBottom: '0.75rem' }} placeholder="you@example.com" />
          <label style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--color-text-muted)' }}>密码</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6}
            style={{ width: '100%', marginTop: '0.25rem', marginBottom: '1rem' }} placeholder="至少 6 位" />
          <button className="btn-primary" type="submit" disabled={loading} style={{ width: '100%' }}>
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          还没有账号？<Link to="/register">注册</Link>
        </p>
      </div>
    </div>
  );
}
