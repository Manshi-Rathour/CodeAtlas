
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  Network,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import useAuth from '../hooks/useAuth'
import './LoginPage.css'

function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }))

    if (error) setError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    const email = formData.email.trim().toLowerCase()
    const password = formData.password

    if (!email || !password) {
      setError('Please enter both your email and password.')
      return
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    try {
      setIsSubmitting(true)

      await login({ email, password })

      navigate('/dashboard', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail

      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to log in. Please check your details and try again.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-visual-panel">
        <Link to="/" className="auth-brand">
          <span className="auth-brand-icon">
            <Network size={23} />
          </span>
          <span>Code<span>Atlas</span></span>
        </Link>

        <div className="auth-visual-content">
          <div className="auth-eyebrow">
            <Sparkles size={15} />
            YOUR CODEBASE, UNDERSTOOD
          </div>

          <h1>
            Welcome back to
            <span> smarter code exploration.</span>
          </h1>

          <p>
            Pick up where you left off. Explore your projects,
            understand complex codebases, and uncover how everything connects.
          </p>

          <div className="auth-visual-card">
            <div className="auth-card-top">
              <span className="auth-card-dot" />
              <span className="auth-card-dot" />
              <span className="auth-card-dot" />
              <span className="auth-card-label">codebase_overview</span>
            </div>

            <div className="auth-code-lines">
              <div><span>01</span> <b>project</b> = <em>"CodeAtlas"</em></div>
              <div><span>02</span> <b>understanding</b> = <em>true</em></div>
              <div><span>03</span> <b>complexity</b> = <i>simplified</i></div>
            </div>

            <div className="auth-card-footer">
              <ShieldCheck size={16} />
              Understand your code with confidence
            </div>
          </div>
        </div>

        <div className="auth-visual-bottom">
          Built for developers who want to understand more.
        </div>
      </section>

      <section className="auth-form-panel">
        <Link to="/" className="auth-back-link">
          <ArrowLeft size={16} />
          Back to home
        </Link>

        <div className="auth-form-wrapper">
          <div className="auth-mobile-brand">
            <span className="auth-brand-icon">
              <Network size={22} />
            </span>
            <span>Code<span>Atlas</span></span>
          </div>

          <div className="auth-heading">
            <div className="auth-heading-icon">
              <LockKeyhole size={21} />
            </div>

            <h2>Welcome back</h2>
            <p>Enter your details to access your CodeAtlas workspace.</p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label htmlFor="email">Email address</label>

              <div className="auth-input-wrapper">
                <Mail size={18} />
                <input
                  id="email"
                  type="email"
                  name="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <div className="auth-label-row">
                <label htmlFor="password">Password</label>
              </div>

              <div className="auth-input-wrapper">
                <LockKeyhole size={18} />

                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((previous) => !previous)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="auth-error" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="auth-submit-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="auth-spinner" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in to CodeAtlas
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <p className="auth-switch-text">
            Don't have an account?{' '}
            <Link to="/signup">Create an account</Link>
          </p>

          <div className="auth-security-note">
            <ShieldCheck size={15} />
            Your workspace is protected with secure authentication.
          </div>
        </div>

        <div className="auth-copyright">
          © {new Date().getFullYear()} CodeAtlas. All rights reserved.
        </div>
      </section>
    </main>
  )
}

export default LoginPage
