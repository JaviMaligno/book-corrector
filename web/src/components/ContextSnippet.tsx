import React from 'react'

type Props = {
  text: string
  target: string
  replacement?: string
  mode?: 'before' | 'after' | 'inline'
}

// Simple highlighter: first exact occurrence of target
export function ContextSnippet({ text, target, replacement, mode = 'inline' }: Props) {
  const idx = target ? text.toLowerCase().indexOf(target.toLowerCase()) : -1
  if (idx === -1) {
    if (mode === 'after' && replacement) {
      return <span>{text.replace(target, replacement)}</span>
    }
    return <span>{text}</span>
  }

  const before = text.slice(0, idx)
  const match = text.slice(idx, idx + target.length)
  const after = text.slice(idx + target.length)

  if (mode === 'before') {
    return (
      <span>
        {before}
        <mark className="bg-[color:var(--red)]/20 text-[color:var(--red)] line-through decoration-[color:var(--red)]">{match}</mark>
        {after}
      </span>
    )
  }

  if (mode === 'after' && replacement) {
    return (
      <span>
        {before}
        <mark className="bg-[color:var(--teal)]/20 text-[color:var(--teal)] underline decoration-[color:var(--teal)]">{replacement}</mark>
        {after}
      </span>
    )
  }

  // inline: show both original->corrected
  return (
    <span>
      {before}
      <span className="inline-flex items-center gap-1">
        <span className="line-through text-[color:var(--red)]">{match}</span>
        <span className="text-gray-400">→</span>
        <span className="text-[color:var(--teal)] font-medium">{replacement ?? match}</span>
      </span>
      {after}
    </span>
  )
}

