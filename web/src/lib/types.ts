export type CorrectionRow = {
  token_id?: number
  line?: number
  original: string
  corrected: string
  reason?: string
  context?: string
  sentence?: string
  chunk_index?: number
}

