import type { QueryClient } from '@tanstack/react-query'
import type { CorrectionRow } from './types'

export function invalidateSuggestionsForRun(queryClient: QueryClient, runId: string) {
  return queryClient.invalidateQueries({ queryKey: ['suggestions', runId] })
}

export function parseJsonl(text: string, documentName: string): CorrectionRow[] {
  return text
    .trim()
    .split('\n')
    .filter(line => line.trim())
    .map((line): CorrectionRow | null => {
      try {
        const row = JSON.parse(line) as CorrectionRow
        return { ...row, document: documentName }
      } catch {
        return null
      }
    })
    .filter((row): row is CorrectionRow => row !== null)
}
