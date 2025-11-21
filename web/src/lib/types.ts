export type CorrectionRow = {
  token_id?: number
  line?: number
  original: string
  corrected: string
  reason?: string
  context?: string
  sentence?: string
  chunk_index?: number
  document?: string  // Nombre del documento de origen
}

// Backend suggestion model (persistent)
export type Suggestion = {
  id: string                    // UUID de la sugerencia
  run_id: string
  document_id: string
  token_id: number
  line: number
  suggestion_type: string       // ortografia, puntuacion, estilo, etc.
  severity: string              // error, warning, info
  before: string                // texto original
  after: string                 // texto sugerido
  reason: string
  source: string                // rule | llm
  confidence: number | null     // 0.0-1.0
  context: string | null
  sentence: string | null       // frase completa
  status: 'pending' | 'accepted' | 'rejected'
}

export type SuggestionsListResponse = {
  run_id: string
  total: number
  suggestions: Suggestion[]
}

export type Project = {
  id: string
  owner_id: string
  name: string
  lang_variant: string | null
  style_profile_id: string | null
  config_json: string | null
  created_at: string
}

