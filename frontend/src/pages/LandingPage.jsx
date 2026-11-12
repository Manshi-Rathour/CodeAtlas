
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  ArrowUpRight,
  Upload,
  Sparkles,
  Search,
  GitBranch,
  FileCode2,
  ShieldCheck,
  Network,
  MessageSquareText,
  Boxes,
  Zap,
  CheckCircle2,
  Code2,
  Terminal,
} from 'lucide-react'

import Navbar from '../components/common/Navbar'

function LandingPage() {
  const features = [
    {
      icon: Search,
      title: 'Understand any codebase',
      description:
        'Explore unfamiliar projects with structured analysis, file discovery, and intelligent code understanding.',
    },
    {
      icon: Network,
      title: 'Visualize dependencies',
      description:
        'Discover how files, modules, and components connect through interactive dependency graphs.',
    },
    {
      icon: MessageSquareText,
      title: 'Chat with your code',
      description:
        'Ask questions in natural language and get contextual answers grounded in your source code.',
    },
    {
      icon: FileCode2,
      title: 'Automatic documentation',
      description:
        'Generate clear project documentation and understand important parts of your application.',
    },
    {
      icon: Boxes,
      title: 'Multi-language support',
      description:
        'Explore projects across different programming languages and technology stacks.',
    },
    {
      icon: ShieldCheck,
      title: 'Built with security in mind',
      description:
        'Projects are analyzed as source files. Uploaded code is never executed by the platform.',
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

  return (
    <div className="landing-page">
      <Navbar />

      <main>
        {/* Hero Section */}
        <section className="landing-hero">
          <div className="hero-glow hero-glow-one"></div>
          <div className="hero-glow hero-glow-two"></div>

          <div className="hero-content">
            <div className="hero-announcement">
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
                href="https://github.com"
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
                        <strong>1,284</strong>
                        <small>Across your project</small>
                      </div>
                      <div className="preview-stat">
                        <span>Languages</span>
                        <strong>08</strong>
                        <small>Detected languages</small>
                      </div>
                      <div className="preview-stat">
                        <span>Dependencies</span>
                        <strong>246</strong>
                        <small>Relationships found</small>
                      </div>
                    </div>

                    <div className="preview-analysis">
                      <div className="preview-analysis-heading">
                        <span>
                          <Zap size={15} />
                          Codebase insights
                        </span>
                        <span className="preview-live">DEMO PREVIEW</span>
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
          <div className="import-card">
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

          <div className="import-card">
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
          <div className="section-heading">
            <span className="section-eyebrow">POWERFUL CAPABILITIES</span>
            <h2>
              Everything you need to
              <br />
              <span>navigate complex code.</span>
            </h2>
            <p>
              From understanding project structure to asking AI questions,
              get a clearer picture of how your software works.
            </p>
          </div>

          <div className="features-grid">
            {features.map((feature, index) => {
              const Icon = feature.icon

              return (
                <article className="feature-card" key={feature.title}>
                  <div className="feature-icon">
                    <Icon size={22} />
                  </div>

                  <span className="feature-number">
                    0{index + 1}
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
          <div className="section-heading">
            <span className="section-eyebrow">SIMPLE WORKFLOW</span>
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
            <div className="workflow-step">
              <span className="workflow-number">01</span>
              <div className="workflow-icon">
                <Upload size={23} />
              </div>
              <h3>Import your project</h3>
              <p>
                Upload a ZIP file or connect a public GitHub repository.
              </p>
            </div>

            <div className="workflow-step">
              <span className="workflow-number">02</span>
              <div className="workflow-icon">
                <Search size={23} />
              </div>
              <h3>Analyze your code</h3>
              <p>
                Discover files, languages, architecture, and dependencies.
              </p>
            </div>

            <div className="workflow-step">
              <span className="workflow-number">03</span>
              <div className="workflow-icon">
                <Sparkles size={23} />
              </div>
              <h3>Explore with AI</h3>
              <p>
                Ask questions, understand modules, and generate documentation.
              </p>
            </div>
          </div>
        </section>

        {/* Languages Section */}
        <section className="languages-section" id="languages">
          <div className="section-heading">
            <span className="section-eyebrow">UNIVERSAL CODE SUPPORT</span>
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

          <div className="language-list">
            {languages.map((language) => (
              <span className="language-badge" key={language}>
                <Code2 size={15} />
                {language}
              </span>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="final-cta">
          <div className="cta-glow"></div>

          <span className="section-eyebrow">YOUR NEXT PROJECT STARTS HERE</span>

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
        <Link to="/" className="brand">
          <span className="brand-icon">
            <Network size={20} />
          </span>
          <span className="brand-name">
            Code<span>Atlas</span>
          </span>
        </Link>

        <p>
          Understand your code. Navigate with confidence.
        </p>

        <span className="footer-copyright">
          © {new Date().getFullYear()} CodeAtlas. All rights reserved.
        </span>
      </footer>
    </div>
  )
}

export default LandingPage
