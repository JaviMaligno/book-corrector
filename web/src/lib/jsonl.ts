import type { CorrectionRow } from './types'

export function parseJsonl(text: string): CorrectionRow[] {
  const out: CorrectionRow[] = []
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      const obj = JSON.parse(trimmed)
      out.push({
        token_id: obj.token_id,
        line: obj.line,
        original: obj.original ?? '',
        corrected: obj.corrected ?? '',
        reason: obj.reason ?? '',
        context: obj.context ?? '',
        sentence: obj.sentence ?? '',
        chunk_index: obj.chunk_index
      })
    } catch (e) {
      // skip bad lines
    }
  }
  return out
}

