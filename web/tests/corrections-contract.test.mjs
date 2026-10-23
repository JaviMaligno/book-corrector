import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { test } from 'node:test';
import { Socket } from 'node:net';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient } from '@tanstack/react-query';

Socket.prototype.connect = () => { throw new Error('No network in correction contracts'); };
globalThis.fetch = () => { throw new Error('No fetch in correction contracts'); };
const sourceRoot = fileURLToPath(new URL('../src/', import.meta.url));
registerHooks({
  resolve(specifier, context, next) {
    if (specifier.startsWith('.') && context.parentURL?.startsWith('file:')) {
      const file = fileURLToPath(new URL(specifier, context.parentURL));
      if (file.startsWith(sourceRoot)) {
        for (const ext of ['.ts', '.tsx']) {
          if (existsSync(file + ext)) return { url: pathToFileURL(file + ext).href, shortCircuit: true };
        }
      }
    }
    return next(specifier, context);
  },
  load(url, context, next) {
    if (url.startsWith('file:')) {
      const file = fileURLToPath(url);
      if (file.startsWith(sourceRoot) && /\.tsx?$/.test(file)) {
        return { format: 'module', source: ts.transpileModule(readFileSync(file, 'utf8'), {
          compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
        }).outputText, shortCircuit: true };
      }
    }
    return next(url, context);
  },
});

const { invalidateSuggestionsForRun, parseJsonl } = await import('../src/lib/corrections.ts');
const { CorrectionsTable } = await import('../src/components/CorrectionsTable.tsx');
const { updateSuggestionStatus } = await import('../src/lib/suggestions.ts');
const { api } = await import('../src/lib/api.ts');

test('a review refreshes every filter of its run while preserving other runs and projects', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  const own = [['suggestions', 'run-a', 'all'], ['suggestions', 'run-a', 'pending']];
  const unrelated = [['suggestions', 'run-b', 'all'], ['projects', 'project-a']];
  try {
    for (const key of [...own, ...unrelated]) client.setQueryData(key, { synthetic: true });
    await invalidateSuggestionsForRun(client, 'run-a');
    for (const key of own) assert.equal(client.getQueryState(key).isInvalidated, true);
    for (const key of unrelated) assert.equal(client.getQueryState(key).isInvalidated, false);
  } finally { client.clear(); }
});

test('legacy JSONL preserves valid rows, document names and malformed-line tolerance', () => {
  const rows = parseJsonl('{"original":"vello","corrected":"bello"}\ninvalid json\n\n{"original":"hola","corrected":"Hola"}', 'synthetic.docx');
  assert.equal(rows.length, 2);
  assert.equal(rows[0].original, 'vello');
  assert.equal(rows[1].corrected, 'Hola');
  assert.ok(rows.every(row => row.document === 'synthetic.docx'));
  assert.deepEqual(parseJsonl(' \n', 'empty.docx'), []);
  const html = renderToStaticMarkup(React.createElement(CorrectionsTable, { rows, mode: 'legacy', showDocumentColumn: true }));
  assert.match(html, /synthetic\.docx/);
  assert.match(html, /vello/);
  assert.match(html, /bello/);
});

test('persistent suggestions render before/after and revert accepted corrections to pending', async () => {
  const suggestion = { id: 's-a', run_id: 'run-a', document_id: 'd-a', token_id: 1, line: 1,
    suggestion_type: 'ortografia', severity: 'error', before: 'vello', after: 'bello', reason: 'synthetic',
    source: 'rule', confidence: null, context: null, sentence: 'vello', status: 'accepted' };
  const html = renderToStaticMarkup(React.createElement(CorrectionsTable, { rows: [suggestion], mode: 'server' }));
  assert.match(html, /vello/);
  assert.match(html, /bello/);
  assert.match(html, /Aceptada/);
  assert.match(html, /Revertir a pendiente/);
  const original = api.defaults.adapter;
  api.defaults.adapter = async config => {
    assert.equal(config.method, 'patch');
    assert.equal(config.url, '/suggestions/suggestions/s-a');
    assert.deepEqual(JSON.parse(config.data), { status: 'pending' });
    return { data: { ...suggestion, status: 'pending' }, status: 200, statusText: 'OK', headers: {}, config };
  };
  try { assert.equal((await updateSuggestionStatus('s-a', 'pending')).status, 'pending'); }
  finally { api.defaults.adapter = original; }
});
