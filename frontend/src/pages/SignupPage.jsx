
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
  UserRound,
} from 'lucide-react'

import useAuth from '../hooks/useAuth'
import './SignupPage.css'

function SignupPage() {
  const navigate = useNavigate()
  const { signup } = useAuth()

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
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

    const full_name = formData.full_name.trim()
    const email = formData.email.trim().toLowerCase()
    const password = formData.password

    if (full_name.length < 2) {
      setError('Full name must contain at least 2 characters.')
      return
    }

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    if (password !== formData.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    try {
      setIsSubmitting(true)

      await signup({
        full_name,
        email,
        password,
      })

      navigate('/dashboard', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail

      setError(
        typeof detail === 'string'
          ? detail
          : 'Unable to create your account. Please try again.'
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
            START YOUR DEVELOPER JOURNEY
          </div>

          <h1>
            Understand your code.
            <span> Build with confidence.</span>
          </h1>

          <p>
            Bring your projects together and discover a smarter way
            to explore, analyze, and understand your codebase.
          </p>

          <div className="auth-visual-card">
            <div className="auth-card-top">
              <span className="auth-card-dot" />
              <span className="auth-card-dot" />
              <span className="auth-card-dot" />
              <span className="auth-card-label">your_next_project</span>
            </div>

            <div className="auth-code-lines">
              <div><span>01</span> <b>explore</b> = <em>"Any language"</em></div>
              <div><span>02</span> <b>analyze</b> = <em>true</em></div>
              <div><span>03</span> <b>understand</b> = <i>"Everything"</i></div>
            </div>

            <div className="auth-card-footer">
              <ShieldCheck size={16} />
              One workspace for your codebase
            </div>
          </div>
        </div>

        <div className="auth-visual-bottom">
          A smarter way to navigate complex code.
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
              <UserRound size={21} />
            </div>

            <h2>Create your account</h2>
            <p>Get started with your CodeAtlas workspace today.</p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label htmlFor="full_name">Full name</label>

              <div className="auth-input-wrapper">
                <UserRound size={18} />
                <input
                  id="full_name"
                  type="text"
                  name="full_name"
                  placeholder="Enter your full name"
                  value={formData.full_name}
                  onChange={handleChange}
                  autoComplete="name"
                  minLength={2}
                  maxLength={100}
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="signup-email">Email address</label>

              <div className="auth-input-wrapper">
                <Mail size={18} />
                <input
                  id="signup-email"
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
              <label htmlFor="signup-password">Password</label>

              <div className="auth-input-wrapper">
                <LockKeyhole size={18} />

                <input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={128}
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

            <div className="auth-field">
              <label htmlFor="confirm-password">Confirm password</label>

              <div className="auth-input-wrapper">
                <LockKeyhole size={18} />

                <input
                  id="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  required
                />

                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowConfirmPassword((previous) => !previous)}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
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
                  Creating account...
                </>
              ) : (
                <>
                  Create account
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <p className="auth-switch-text">
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>

          <div className="auth-security-note">
            <ShieldCheck size={15} />
            Your account is protected with secure authentication.
          </div>
        </div>

        <div className="auth-copyright">
          © {new Date().getFullYear()} CodeAtlas. All rights reserved.
        </div>
      </section>
    </main>
  )
}

export default SignupPage
