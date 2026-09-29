interface PlaceholderPageProps {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section className="placeholder">
      <div className="placeholder-card">
        <p className="eyebrow">준비 중인 화면</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </section>
  )
}

