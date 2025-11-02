import { api } from './api'
import type { Suggestion, SuggestionsListResponse } from './types'

/**
 * List suggestions for a run, optionally filtered by status
 */
export async function listSuggestions(
  runId: string,
  status?: 'pending' | 'accepted' | 'rejected'
): Promise<SuggestionsListResponse> {
  const params = status ? { status } : {}
  const response = await api.get<SuggestionsListResponse>(
    `/suggestions/runs/${runId}/suggestions`,
    { params }
  )
  return response.data
}

/**
 * Update status of a single suggestion (accept/reject)
 */
export async function updateSuggestionStatus(
  suggestionId: string,
  status: 'accepted' | 'rejected'
): Promise<Suggestion> {
  const response = await api.patch<Suggestion>(
    `/suggestions/suggestions/${suggestionId}`,
    { status }
  )
  return response.data
}

/**
 * Bulk update status of multiple suggestions
 */
export async function bulkUpdateSuggestions(
  runId: string,
  suggestionIds: string[],
  status: 'accepted' | 'rejected'
): Promise<{ updated: number; total_requested: number }> {
  const response = await api.post(
    `/suggestions/runs/${runId}/suggestions/bulk-update`,
    { suggestion_ids: suggestionIds, status }
  )
  return response.data
}

/**
 * Accept all pending suggestions for a run
 */
export async function acceptAllSuggestions(
  runId: string
): Promise<{ accepted: number }> {
  const response = await api.post(
    `/suggestions/runs/${runId}/suggestions/accept-all`
  )
  return response.data
}

/**
 * Reject all pending suggestions for a run
 */
export async function rejectAllSuggestions(
  runId: string
): Promise<{ rejected: number }> {
  const response = await api.post(
    `/suggestions/runs/${runId}/suggestions/reject-all`
  )
  return response.data
}

/**
 * Export document with only accepted corrections applied
 * Returns a blob URL for downloading the DOCX file
 */
export async function exportWithAccepted(runId: string): Promise<Blob> {
  const response = await api.post(
    `/suggestions/runs/${runId}/export-with-accepted`,
    {},
    { responseType: 'blob' }
  )
  return response.data
}

/**
 * Trigger download of exported document with accepted corrections
 */
export function downloadExportedDocument(runId: string, blob: Blob, filename?: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || `run_${runId.slice(0, 8)}_accepted.docx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

