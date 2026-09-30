import type { ReactNode } from 'react'

interface ErrorStateProps {
  title: string
  message: string
  heading?: 'h1' | 'h2'
  action?: ReactNode
}

export function ErrorState({ title, message, heading = 'h1', action }: ErrorStateProps) {
  const Heading = heading
  return (
    <section className="error-state">
      <Heading>{title}</Heading>
      <p>{message}</p>
      {action}
    </section>
  )
}

export function LoadingState({ message }: { message: string }) {
  return <p className="loading">{message}</p>
}
