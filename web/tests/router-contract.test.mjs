import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { createMemoryRouter } from 'react-router-dom';

test('actual project, run and login route patterns preserve navigation', async () => {
  const source = readFileSync(new URL('../src/main.tsx', import.meta.url), 'utf8');
  const routes = [...source.matchAll(/path: '([^']+)'/g)].map(match => ({ path: match[1] }));
  assert.equal(routes.length, 7);
  const router = createMemoryRouter(routes, { initialEntries: ['/projects/42'] });
  try {
    assert.equal(router.state.matches.at(-1).params.projectId, '42');
    await router.navigate('/runs/7/corrections');
    assert.equal(router.state.matches.at(-1).params.runId, '7');
    await router.navigate(-1);
    assert.equal(router.state.location.pathname, '/projects/42');
    await router.navigate('/login');
    assert.equal(router.state.matches.at(-1).route.path, '/login');
  } finally { router.dispose(); }
});
