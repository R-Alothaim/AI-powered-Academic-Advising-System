export default function AuthBackground() {
  return (
    <>
      <div className="bg" />
      <div className="orb orb1" />
      <div className="orb orb2" />
      <div className="orb orb3" />

      <svg
        className="network-svg"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <g stroke="#3A6AE8" strokeWidth="0.7" fill="none">
          <line x1="80" y1="120" x2="200" y2="220" />
          <line x1="200" y1="220" x2="150" y2="380" />
          <line x1="200" y1="220" x2="320" y2="160" />
          <line x1="150" y1="380" x2="90" y2="500" />
          <line x1="150" y1="380" x2="250" y2="480" />
          <line x1="90" y1="500" x2="60" y2="680" />
          <line x1="250" y1="480" x2="180" y2="700" />
          <line x1="320" y1="160" x2="420" y2="90" />
          <line x1="1100" y1="80" x2="1250" y2="180" />
          <line x1="1250" y1="180" x2="1360" y2="120" />
          <line x1="1250" y1="180" x2="1300" y2="340" />
          <line x1="1300" y1="340" x2="1400" y2="420" />
          <line x1="1300" y1="340" x2="1200" y2="440" />
          <line x1="1200" y1="440" x2="1350" y2="580" />
          <line x1="1200" y1="440" x2="1100" y2="620" />
          <line x1="1100" y1="620" x2="1280" y2="750" />
          <line x1="1100" y1="620" x2="1000" y2="780" />
          <line x1="700" y1="50" x2="780" y2="130" />
          <line x1="780" y1="130" x2="850" y2="60" />
          <line x1="700" y1="820" x2="760" y2="760" />
          <line x1="760" y1="760" x2="840" y2="840" />
        </g>
        <g fill="#1B3D9C" stroke="#4A7AFF" strokeWidth="1">
          <circle cx="80" cy="120" r="5" />
          <circle cx="200" cy="220" r="9" />
          <circle cx="150" cy="380" r="7" />
          <circle cx="320" cy="160" r="5" />
          <circle cx="420" cy="90" r="4" />
          <circle cx="90" cy="500" r="6" />
          <circle cx="250" cy="480" r="5" />
          <circle cx="60" cy="680" r="4" />
          <circle cx="180" cy="700" r="5" />
          <circle cx="1100" cy="80" r="5" />
          <circle cx="1250" cy="180" r="9" />
          <circle cx="1360" cy="120" r="4" />
          <circle cx="1300" cy="340" r="7" />
          <circle cx="1400" cy="420" r="4" />
          <circle cx="1200" cy="440" r="8" />
          <circle cx="1350" cy="580" r="5" />
          <circle cx="1100" cy="620" r="7" />
          <circle cx="1280" cy="750" r="4" />
          <circle cx="1000" cy="780" r="5" />
          <circle cx="700" cy="50" r="4" />
          <circle cx="780" cy="130" r="6" />
          <circle cx="850" cy="60" r="4" />
          <circle cx="700" cy="820" r="4" />
          <circle cx="760" cy="760" r="6" />
          <circle cx="840" cy="840" r="4" />
        </g>
        <circle cx="200" cy="220" r="16" fill="#1B3D9C" stroke="#5AAEFF" strokeWidth="1" opacity="0.4" />
        <circle cx="1250" cy="180" r="16" fill="#1B3D9C" stroke="#5AAEFF" strokeWidth="1" opacity="0.4" />
        <circle cx="1200" cy="440" r="14" fill="#1B3D9C" stroke="#5AAEFF" strokeWidth="1" opacity="0.4" />
      </svg>

      <div className="brand">
        <div className="brand-icon">
          <svg viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M11 2L13.5 8H20L14.5 12L16.5 18L11 14L5.5 18L7.5 12L2 8H8.5L11 2Z"
              stroke="#EAD27A"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="brand-text">
          <div className="brand-name">Academic Advisor</div>
          <div className="brand-sub">AI-Powered Academic System</div>
        </div>
      </div>

      <div className="hero-left">
        <div className="hero-eyebrow">Intelligent &middot; Personalized &middot; Academic</div>
        <div className="hero-title">
          Your <em>Academic</em>
          <br />
          Path, Guided
          <br />
          by AI
        </div>
        <div className="hero-desc">
          Get instant, personalized guidance on courses, degree plans, deadlines, and career
          paths &mdash; available 24/7 through our intelligent advisor.
        </div>
        <div className="hero-pills">
          <span className="pill">GPA Planning</span>
          <span className="pill">Course Search</span>
          <span className="pill">Career Paths</span>
          <span className="pill">Scheduling</span>
        </div>
      </div>
