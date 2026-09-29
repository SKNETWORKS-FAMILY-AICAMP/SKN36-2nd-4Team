export type IconName =
  | 'home'
  | 'risk-user'
  | 'user-detail'
  | 'analytics'
  | 'document'
  | 'users'
  | 'verified-user'
  | 'churn-user'
  | 'pie-chart'
  | 'gamepad'

interface IconProps {
  name: IconName
  className?: string
}

function IconDrawing({ name }: { name: IconName }) {
  switch (name) {
    case 'home':
      return (
        <>
          <path className="icon-fill" d="m4 10 8-6 8 6v10H4Z" />
          <path d="m3 10 9-7 9 7M5 9.5V20h14V9.5M9.5 20v-6h5v6" />
          <path d="M16.5 5.5V3.8h2v3.3" />
        </>
      )
    case 'risk-user':
      return (
        <>
          <circle className="icon-fill" cx="9" cy="7" r="3" />
          <circle cx="9" cy="7" r="3" />
          <path d="M3.8 18.8c.4-3.4 2.2-5.5 5.2-5.5 2.1 0 3.6 1 4.5 2.6" />
          <path className="icon-fill" d="m17.5 12 4 7H13.5Z" />
          <path d="m17.5 12 4 7H13.5Zm0 2.6v1.9m0 1.2v.1" />
        </>
      )
    case 'user-detail':
      return (
        <>
          <circle className="icon-fill" cx="9" cy="7" r="3" />
          <circle cx="9" cy="7" r="3" />
          <path d="M3.5 19c.5-3.6 2.3-5.7 5.5-5.7 1.8 0 3.2.7 4.2 2" />
          <circle cx="17" cy="16.5" r="3.2" />
          <path d="m19.4 18.9 2.2 2.2" />
        </>
      )
    case 'analytics':
      return (
        <>
          <path className="icon-fill" d="M4 13h3v7H4zm6-5h3v12h-3zm6-4h3v16h-3z" />
          <path d="M4 13h3v7H4zm6-5h3v12h-3zm6-4h3v16h-3zM3 20.5h18" />
          <path d="m4.5 9 5-4 3 1.5L18.5 2" />
        </>
      )
    case 'document':
      return (
        <>
          <path className="icon-fill" d="M5 2.8h9l5 5V21H5Z" />
          <path d="M5 2.8h9l5 5V21H5Zm9 0V8h5M8 12h8M8 15.5h8M8 19h5" />
          <circle cx="8" cy="8" r="1.2" />
        </>
      )
    case 'users':
      return (
        <>
          <circle className="icon-fill" cx="12" cy="7" r="3" />
          <circle cx="12" cy="7" r="3" />
          <path d="M6.5 20c.4-4.2 2.2-6.5 5.5-6.5s5.1 2.3 5.5 6.5" />
          <circle cx="4.8" cy="9" r="2" />
          <circle cx="19.2" cy="9" r="2" />
          <path d="M1.8 19c.3-3 1.3-4.7 3.2-4.7 1 0 1.8.4 2.4 1.2M22.2 19c-.3-3-1.3-4.7-3.2-4.7-1 0-1.8.4-2.4 1.2" />
        </>
      )
    case 'verified-user':
      return (
        <>
          <circle className="icon-fill" cx="9" cy="7" r="3" />
          <circle cx="9" cy="7" r="3" />
          <path d="M3.5 19c.4-3.7 2.3-5.8 5.5-5.8 1.8 0 3.2.7 4.2 2" />
          <circle className="icon-fill" cx="17.5" cy="17" r="4.2" />
          <circle cx="17.5" cy="17" r="4.2" />
          <path d="m15.5 17 1.4 1.4 2.7-3" />
        </>
      )
    case 'churn-user':
      return (
        <>
          <circle className="icon-fill" cx="8.5" cy="7" r="3" />
          <circle cx="8.5" cy="7" r="3" />
          <path d="M3.2 19c.4-3.8 2.2-5.8 5.3-5.8 1.7 0 3 .6 4 1.8" />
          <path className="icon-fill" d="m17.2 11.8 4.3 7.5h-8.6Z" />
          <path d="m17.2 11.8 4.3 7.5h-8.6Zm0 2.6v2.1m0 1.3v.1" />
        </>
      )
    case 'pie-chart':
      return (
        <>
          <path className="icon-fill" d="M11 3a9 9 0 1 0 9 9h-9Z" />
          <path d="M11 3a9 9 0 1 0 9 9h-9Zm3-1v7h7A7 7 0 0 0 14 2Z" />
          <path d="M11 12 6.5 18" />
        </>
      )
    case 'gamepad':
      return (
        <>
          <path className="icon-fill" d="M7.5 8h9c2 0 3.1 1.4 3.8 3.7l1 3.6c.6 2.3-.2 4-1.8 4-1.2 0-2-1.1-3-2.5h-9c-1 1.4-1.8 2.5-3 2.5-1.6 0-2.4-1.7-1.8-4l1-3.6C4.4 9.4 5.5 8 7.5 8Z" />
          <path d="M7.5 8h9c2 0 3.1 1.4 3.8 3.7l1 3.6c.6 2.3-.2 4-1.8 4-1.2 0-2-1.1-3-2.5h-9c-1 1.4-1.8 2.5-3 2.5-1.6 0-2.4-1.7-1.8-4l1-3.6C4.4 9.4 5.5 8 7.5 8Z" />
          <path d="M7.5 11v4M5.5 13h4" />
          <circle cx="16" cy="12" r=".8" fill="currentColor" stroke="none" />
          <circle cx="18.3" cy="14.2" r=".8" fill="currentColor" stroke="none" />
          <path d="M10 8 9 5h6l-1 3" />
        </>
      )
  }
}

export function Icon({ name, className = '' }: IconProps) {
  return (
    <svg
      className={`ui-icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <IconDrawing name={name} />
    </svg>
  )
}
