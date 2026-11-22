import { Link } from 'react-router-dom'
import { Network, ArrowUpRight, Menu, X } from 'lucide-react'
import { useState } from 'react'

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="site-header">
      <nav className="navbar">
        <Link to="/" className="brand">
          <span className="brand-icon">
            <Network size={22} />
          </span>

          <span className="brand-copy">
            <span className="brand-name">
              Code<span>Atlas</span>
            </span>

            <span className="brand-subtitle">
              AI Code Intelligence
            </span>
          </span>
        </Link>

        <div className={`nav-links ${menuOpen ? 'nav-open' : ''}`}>
          <a href="#features" onClick={() => setMenuOpen(false)}>
            Features
          </a>

          <a href="#how-it-works" onClick={() => setMenuOpen(false)}>
            How it works
          </a>

          <a href="#languages" onClick={() => setMenuOpen(false)}>
            Language Support
          </a>

          <div className="mobile-nav-actions">
            <Link to="/login" onClick={() => setMenuOpen(false)}>
              Log in
            </Link>

            <Link
              to="/signup"
              className="primary-button"
              onClick={() => setMenuOpen(false)}
            >
              Get started <ArrowUpRight size={16} />
            </Link>
          </div>
        </div>

        <div className="nav-actions">
          <Link to="/login" className="nav-login">
            Log in
          </Link>

          <Link to="/signup" className="nav-cta">
            Get started <ArrowUpRight size={16} />
          </Link>
        </div>

        <button
          type="button"
          className="mobile-menu-button"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X size={23} /> : <Menu size={23} />}
        </button>
      </nav>
    </header>
  )
}

export default Navbar
