import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  Upload,
  Sparkles,
  Search,
  GitBranch,
  FileCode2,
  FileText,
  FolderTree,
  ShieldCheck,
  Network,
  Layers,
  MessageSquareText,
  Zap,
  CheckCircle2,
  Code2,
  Terminal,
  Activity,
  ArrowUp,
} from 'lucide-react'

import Navbar from '../components/common/Navbar'

const SCAN_FEED = [
  'Scanning 1,284 files across 42 directories',
  'Detecting languages · Python · TypeScript · Go',
  'Parsing symbols with tree-sitter grammars',
  'Mapping 246 static file dependencies',
  'Indexing code chunks for AI retrieval',
  'Analysis complete — ready to chat',
]

const GALAXY_STARS = Array.from({ length: 46 }, (_, index) => ({
  left: `${(Math.random() * 99).toFixed(2)}%`,
  top: `${(Math.random() * 94 + 2).toFixed(2)}%`,
  size: `${[1, 1, 1, 2, 2, 3][index % 6]}px`,
  delay: `${(Math.random() * 7).toFixed(2)}s`,
  duration: `${(3.2 + Math.random() * 4.2).toFixed(2)}s`,
}))

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handleChange = (event) => setReduced(event.matches)
    query.addEventListener('change', handleChange)

    return () => query.removeEventListener('change', handleChange)
  }, [])

  return reduced
}

function AnimatedNumber({ value, pad = 0, duration = 1500 }) {
  const [display, setDisplay] = useState(0)
  const nodeRef = useRef(null)
  const startedRef = useRef(false)
  const reducedMotion = usePrefersReducedMotion()

  useEffect(() => {
    if (reducedMotion) return

    const node = nodeRef.current
    if (!node) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting || startedRef.current) return

          startedRef.current = true
          const startTime = performance.now()

          const tick = (now) => {
            const progress = Math.min((now - startTime) / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)

            setDisplay(Math.round(value * eased))

            if (progress < 1) {
              requestAnimationFrame(tick)
            }
          }

          requestAnimationFrame(tick)
        })
      },
      { threshold: 0.35 },
    )

    observer.observe(node)

    return () => observer.disconnect()
  }, [value, duration, reducedMotion])

  const shownValue = reducedMotion ? value : display
  const text = pad
    ? String(shownValue).padStart(pad, '0')
    : shownValue.toLocaleString('en-US')

  return <strong ref={nodeRef}>{text}</strong>
}

function LiveFeed() {
  const [lineIndex, setLineIndex] = useState(0)
  const [text, setText] = useState('')
  const reducedMotion = usePrefersReducedMotion()

  useEffect(() => {
    if (reducedMotion) return

    const fullLine = SCAN_FEED[lineIndex % SCAN_FEED.length]

    let charIndex = 0
    let holdTimer = null

    const typeTimer = setInterval(() => {
      charIndex += 1
      setText(fullLine.slice(0, charIndex))

      if (charIndex >= fullLine.length) {
        clearInterval(typeTimer)
        holdTimer = setTimeout(() => {
          setLineIndex((current) => current + 1)
        }, 1700)
      }
    }, 26)

    return () => {
      clearInterval(typeTimer)
      if (holdTimer) clearTimeout(holdTimer)
    }
  }, [lineIndex, reducedMotion])

  return (
    <div className="preview-live-feed">
      <span className="feed-prompt">
        <Activity size={12} />
      </span>

      <span className="feed-text">
        {reducedMotion ? SCAN_FEED[0] : text}
      </span>

      <span className="feed-caret" aria-hidden="true" />
    </div>
  )
}

function LandingPage() {
  const heroRef = useRef(null)
  const [scrollProgress, setScrollProgress] = useState(0)
  const reducedMotion = usePrefersReducedMotion()

  const features = [
    {
      icon: FolderTree,
      title: 'Explore and understand code',
      description:
        'Browse a searchable file tree with a Monaco viewer, then inspect functions, methods, classes, and code chunks extracted.',
    },
        {
      icon: GitBranch,
      title: 'Import from GitHub or ZIP',
      description:
        'Bring in a public repository with branch selection or upload a ZIP archive, with a complete file inventory.',
    },
    {
      icon: Code2,
      title: 'Multi-language support',
      description:
        'Analyze Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, PHP, Ruby, HTML, CSS, SQL, Swift, Kotlin, and more.',
    },
    {
      icon: Network,
      title: 'Visualize dependencies',
      description:
        'See how files and modules connect through an interactive graph built from resolved internal imports.',
    },
    {
      icon: Layers,
      title: 'Map architecture and APIs',
      description:
        'Explore modules, language distribution, frameworks, libraries, databases, HTTP endpoints, and AI architecture explanations.',
    },
    {
      icon: MessageSquareText,
      title: 'Chat with your code',
      description:
        'Ask questions in natural language and get answers grounded in retrieved source code, with file and line citations.',
    },
    {
      icon: FileText,
      title: 'Generate documentation',
      description:
        'Create practical project documentation from real manifests, symbols, routes, and code context.',
    },
    {
      icon: Activity,
      title: 'Track project metrics',
      description:
        'Measure files, languages, functions, classes, chunks, dependencies, API routes, conversations, and documentation.',
    },
    {
      icon: ShieldCheck,
      title: 'Secure and private',
      description:
        'Source is never executed, with safe imports, sensitive-file filtering, JWT auth, per-user isolation.',
    },
  ]

  const languages = [
    'Python',
    'JavaScript',
    'TypeScript',
    'Java',
    'C++',
    'C',
    'Go',
    'Rust',
    'PHP',
    'Ruby',
    'HTML',
    'CSS',
    'SQL',
    'Swift',
    'Kotlin',
    'And more',
  ]

  const languageRows = [languages.slice(0, 8), languages.slice(8)]

  /* Scroll progress bar */
  useEffect(() => {
    let frame = null

    const updateProgress = () => {
      frame = null
      const scrollable =
        document.documentElement.scrollHeight - window.innerHeight

      if (scrollable <= 0) {
        setScrollProgress(0)
        return
      }

      setScrollProgress(
        Math.min(Math.max(window.scrollY / scrollable, 0), 1),
      )
    }

    const handleScroll = () => {
      if (frame !== null) return
      frame = requestAnimationFrame(updateProgress)
    }

    updateProgress()
    window.addEventListener('scroll', handleScroll, { passive: true })
    window.addEventListener('resize', handleScroll)

    return () => {
      if (frame !== null) cancelAnimationFrame(frame)
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('resize', handleScroll)
    }
  }, [])

  /* Scroll reveal */
  useEffect(() => {
    const elements = Array.from(
      document.querySelectorAll('.landing-page [data-reveal]'),
    )

    if (reducedMotion || !('IntersectionObserver' in window)) {
      elements.forEach((element) => element.classList.add('is-visible'))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        })
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px' },
    )

    elements.forEach((element) => observer.observe(element))

    return () => observer.disconnect()
  }, [reducedMotion])

  /* Hero pointer parallax */
  const handleHeroMove = useCallback(
    (event) => {
      if (reducedMotion) return

      const node = heroRef.current
      if (!node) return

      const rect = node.getBoundingClientRect()
      const x = (event.clientX - rect.left) / rect.width - 0.5
      const y = (event.clientY - rect.top) / rect.height - 0.5

      node.style.setProperty('--hero-x', x.toFixed(3))
      node.style.setProperty('--hero-y', y.toFixed(3))
    },
    [reducedMotion],
  )

  const handleHeroLeave = useCallback(() => {
    const node = heroRef.current
    if (!node) return

    node.style.setProperty('--hero-x', '0')
    node.style.setProperty('--hero-y', '0')
  }, [])

  /* Feature card spotlight */
  const handleCardMove = (event) => {
    if (reducedMotion) return

    const card = event.currentTarget
    const rect = card.getBoundingClientRect()

    card.style.setProperty(
      '--mx',
      `${((event.clientX - rect.left) / rect.width) * 100}%`,
    )
    card.style.setProperty(
      '--my',
      `${((event.clientY - rect.top) / rect.height) * 100}%`,
    )
  }

  return (
    <div className="landing-page">
      <div
        className="scroll-progress"
        style={{ transform: `scaleX(${scrollProgress})` }}
        aria-hidden="true"
      />

      <Navbar />

      <main>
        {/* Hero Section */}
        <section
          className="landing-hero"
          ref={heroRef}
          onMouseMove={handleHeroMove}
          onMouseLeave={handleHeroLeave}
        >
          <div className="hero-background" aria-hidden="true">
            <div className="galaxy-band"></div>
            <div className="galaxy-swirl"></div>
            <div className="hero-glow hero-glow-one"></div>
            <div className="hero-glow hero-glow-two"></div>

            <div className="galaxy-stars">
              {GALAXY_STARS.map((star, index) => (
                <span
                  className="galaxy-star"
                  key={index}
                  style={{
                    left: star.left,
                    top: star.top,
                    '--star-size': star.size,
                    '--star-delay': star.delay,
                    '--star-duration': star.duration,
                  }}
                />
              ))}
            </div>
          </div>

          <div className="hero-content">
            <div className="hero-announcement">
              <span className="announcement-pulse" aria-hidden="true"></span>
              <Sparkles size={15} />
              <span>Your codebase, understood.</span>
              <ArrowUpRight size={14} />
            </div>

            <h1>
              Explore your codebase.
              <br />
              <span>Understand everything.</span>
            </h1>

            <p className="hero-description">
              Stop wasting hours navigating unfamiliar projects.
              CodeAtlas helps you explore code, discover architecture,
              visualize dependencies, and understand your software
              with AI-powered insights.
            </p>

            <div className="hero-actions">
              <Link to="/signup" className="primary-button hero-primary">
                Get started for free
                <ArrowRight size={18} />
              </Link>

              <a
                href="https://github.com/Manshi-Rathour/CodeAtlas"
                target="_blank"
                rel="noreferrer"
                className="secondary-button hero-secondary"
              >
                <GitBranch size={18} />
                Explore GitHub
              </a>
            </div>

            <div className="hero-trust">
              <span>
                <CheckCircle2 size={15} />
                No paid API required
              </span>
              <span>
                <CheckCircle2 size={15} />
                Multiple languages
              </span>
              <span>
                <CheckCircle2 size={15} />
                Developer-focused
              </span>
            </div>
          </div>

          {/* Product Preview */}
          <div className="hero-preview-wrapper">
            <div className="preview-top-glow"></div>

            <div className="product-preview">
              <div className="preview-titlebar">
                <div className="window-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>

                <div className="preview-project-name">
                  <Code2 size={14} />
                  codeatlas / sample-project
                </div>

                <span className="preview-status">
                  <span></span>
                  Analysis complete
                </span>
              </div>

              <div className="preview-body">
                <aside className="preview-sidebar">
                  <div className="preview-sidebar-heading">
                    PROJECT EXPLORER
                  </div>

                  <div className="preview-file active">
                    <FileCode2 size={15} />
                    src
                  </div>
                  <div className="preview-file nested">
                    <FileCode2 size={14} />
                    main.py
                  </div>
                  <div className="preview-file nested">
                    <FileCode2 size={14} />
                    config.py
                  </div>
                  <div className="preview-file nested">
                    <FileCode2 size={14} />
                    routes.py
                  </div>
                  <div className="preview-file">
                    <FileCode2 size={15} />
                    tests
                  </div>
                  <div className="preview-file">
                    <FileCode2 size={15} />
                    requirements.txt
                  </div>
                  <div className="preview-file">
                    <FileCode2 size={15} />
                    README.md
                  </div>
                </aside>

                <div className="preview-main">
                  <div className="preview-tabs">
                    <span className="selected-tab">Overview</span>
                    <span>Architecture</span>
                    <span>Dependencies</span>
                  </div>

                  <div className="preview-overview">
                    <div className="preview-welcome">
                      <div>
                        <span className="preview-eyebrow">
                          PROJECT OVERVIEW
                        </span>
                        <h3>Welcome to your codebase</h3>
                        <p>
                          Here's what we discovered in your project.
                        </p>
                      </div>
                      <div className="preview-ai-icon">
                        <Sparkles size={22} />
                      </div>
                    </div>

                    <div className="preview-stats">
                      <div className="preview-stat">
                        <span>Files analyzed</span>
                        <AnimatedNumber value={1284} />
                        <small>Across your project</small>
                      </div>
                      <div className="preview-stat">
                        <span>Languages</span>
                        <AnimatedNumber value={8} pad={2} />
                        <small>Detected languages</small>
                      </div>
                      <div className="preview-stat">
                        <span>Dependencies</span>
                        <AnimatedNumber value={246} />
                        <small>Relationships found</small>
                      </div>
                    </div>

                    <div className="preview-analysis">
                      <div className="preview-analysis-heading">
                        <span>
                          <Zap size={15} />
                          Codebase insights
                        </span>
                        <span className="preview-live">
                          <span className="live-dot"></span>
                          DEMO PREVIEW
                        </span>
                      </div>

                      <div className="insight-row">
                        <span className="insight-icon">
                          <GitBranch size={15} />
                        </span>
                        <div>
                          <strong>Project architecture discovered</strong>
                          <small>Application modules and connections</small>
                        </div>
                        <CheckCircle2 size={17} />
                      </div>

                      <div className="insight-row">
                        <span className="insight-icon">
                          <Search size={15} />
                        </span>
                        <div>
                          <strong>Code structure indexed</strong>
                          <small>Files and source code inventory</small>
                        </div>
                        <CheckCircle2 size={17} />
                      </div>

                      <div className="insight-row">
                        <span className="insight-icon">
                          <MessageSquareText size={15} />
                        </span>
                        <div>
                          <strong>Ready for codebase questions</strong>
                          <small>Ask questions about your project</small>
                        </div>
                        <CheckCircle2 size={17} />
                      </div>

                      <LiveFeed />
                    </div>
                  </div>
                </div>
              </div>

              <div className="preview-bottom">
                <span>
                  <Terminal size={13} />
                  CodeAtlas workspace
                </span>
                <span>Universal codebase explorer</span>
              </div>
            </div>
          </div>
        </section>

        {/* Import Section */}
        <section className="import-section">
          <div className="import-card" data-reveal>
            <div className="import-icon">
              <GitBranch size={23} />
            </div>

            <div className="import-content">
              <h3>Start with your GitHub repository</h3>
              <p>
                Bring a public repository into CodeAtlas and explore
                its structure.
              </p>
            </div>

            <Link to="/signup" className="secondary-button">
              Import repository <ArrowUpRight size={16} />
            </Link>
          </div>

          <div
            className="import-card"
            data-reveal
            style={{ '--reveal-delay': '0.12s' }}
          >
            <div className="import-icon">
              <Upload size={23} />
            </div>

            <div className="import-content">
              <h3>Have a project on your computer?</h3>
              <p>
                Upload a ZIP archive and start exploring your codebase.
              </p>
            </div>

            <Link to="/signup" className="secondary-button">
              Upload ZIP <ArrowUpRight size={16} />
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section" id="features">
          <div className="section-heading" data-reveal>
            <span className="section-eyebrow">
              <span className="eyebrow-dot"></span>
              POWERFUL CAPABILITIES
            </span>
            <h2>
              Everything you need to
              <br />
              <span>navigate complex code.</span>
            </h2>
            <p>
              From file-level symbols and dependency graphs to APIs, metrics,
              and AI answers, get a complete picture of how your software works.
            </p>
          </div>

          <div className="features-grid">
            {features.map((feature, index) => {
              const Icon = feature.icon

              return (
                <article
                  className="feature-card"
                  key={feature.title}
                  data-reveal
                  style={{ '--reveal-delay': `${index * 0.07}s` }}
                  onMouseMove={handleCardMove}
                >
                  <div className="feature-icon">
                    <Icon size={22} />
                  </div>

                  <span className="feature-number">
                    {String(index + 1).padStart(2, '0')}
                  </span>

                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </article>
              )
            })}
          </div>
        </section>

        {/* How It Works */}
        <section className="workflow-section" id="how-it-works">
          <div className="section-heading" data-reveal>
            <span className="section-eyebrow">
              <span className="eyebrow-dot"></span>
              SIMPLE WORKFLOW
            </span>
            <h2>
              From source code to
              <br />
              <span>complete understanding.</span>
            </h2>
            <p>
              Get started in three simple steps.
            </p>
          </div>

          <div className="workflow-grid">
            <div
              className="workflow-step"
              data-reveal
              style={{ '--reveal-delay': '0s' }}
            >
              <span className="workflow-number">01</span>
              <div className="workflow-icon">
                <Upload size={23} />
              </div>
              <h3>Import your project</h3>
              <p>
                Upload a ZIP archive or import a public GitHub repository
                with an optional branch, then build a complete file inventory.
              </p>
            </div>

            <div
              className="workflow-step"
              data-reveal
              style={{ '--reveal-delay': '0.12s' }}
            >
              <span className="workflow-number">02</span>
              <div className="workflow-icon">
                <Search size={23} />
              </div>
              <h3>Analyze your code</h3>
              <p>
                Parse functions, classes, and imports, resolve dependencies,
                and detect frameworks, APIs, architecture, and metrics.
              </p>
            </div>

            <div
              className="workflow-step"
              data-reveal
              style={{ '--reveal-delay': '0.24s' }}
            >
              <span className="workflow-number">03</span>
              <div className="workflow-icon">
                <Sparkles size={23} />
              </div>
              <h3>Explore with AI</h3>
              <p>
                Browse source and dependency graphs, ask cited questions,
                and generate grounded documentation with a local model.
              </p>
            </div>
          </div>
        </section>

        {/* Languages Section */}
        <section className="languages-section" id="languages">
          <div className="section-heading" data-reveal>
            <span className="section-eyebrow">
              <span className="eyebrow-dot"></span>
              UNIVERSAL CODE SUPPORT
            </span>
            <h2>
              One workspace.
              <br />
              <span>Multiple languages.</span>
            </h2>
            <p>
              Explore projects written in different programming languages.
              Structural analysis depends on language parser support.
            </p>
          </div>

          <div className="language-marquee">
            {languageRows.map((row, rowIndex) => (
              <div
                className={`marquee-row ${rowIndex === 1 ? 'reverse' : ''}`}
                key={rowIndex}
              >
                <div className="marquee-track">
                  {[...row, ...row].map((language, index) => (
                    <span
                      className="language-badge"
                      key={`${language}-${index}`}
                    >
                      <Code2 size={15} />
                      {language}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="final-cta" data-reveal>
          <div className="cta-glow"></div>
          <div className="cta-glow cta-glow-two"></div>

          <span className="section-eyebrow">
            <span className="eyebrow-dot"></span>
            YOUR NEXT PROJECT STARTS HERE
          </span>

          <h2>
            Make every codebase
            <br />
            <span>easier to understand.</span>
          </h2>

          <p>
            Spend less time searching through files and more time building
            great software.
          </p>

          <Link to="/signup" className="primary-button hero-primary">
            Start exploring for free
            <ArrowRight size={18} />
          </Link>
        </section>
      </main>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-top">
            <div className="footer-brand-block">
              <Link to="/" className="brand">
                <span className="brand-icon">
                  <Network size={20} />
                </span>
                <span className="brand-name">
                  Code<span>Atlas</span>
                </span>
              </Link>

              <p className="footer-tagline">
                Explore your codebase.
                <br />
                Understand your code.
              </p>
            </div>

            <nav className="footer-nav" aria-label="Footer">
              <div className="footer-col">
                <h4>Product</h4>
                <a href="#features">Features</a>
                <a href="#how-it-works">How it works</a>
                <a href="#languages">Language Support</a>
              </div>

              <div className="footer-col">
                <h4>Workspace</h4>
                <span>File explorer</span>
                <span>Dependency graph</span>
                <span>AI codebase chat</span>
                <span>Documentation generator</span>
              </div>

              <div className="footer-col">
                <h4>Get started</h4>
                <Link to="/signup">Create an account</Link>
                <Link to="/login">Log in</Link>
              </div>
            </nav>
          </div>

          <div className="footer-wordmark">
            <span>CodeAtlas</span>
          </div>

          <div className="footer-bottom">
            <span>
              © {new Date().getFullYear()} CodeAtlas. All rights reserved.
            </span>

            <button
              type="button"
              className="footer-top-button"
              onClick={() =>
                window.scrollTo({
                  top: 0,
                  behavior: reducedMotion ? 'auto' : 'smooth',
                })
              }
            >
              Back to top <ArrowUp size={14} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
