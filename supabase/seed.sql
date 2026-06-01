-- Seed workspaces, projects, beliefs, profiles, sample memory & decisions
-- Run after migrations. IDs match frontend MSW fixtures.

INSERT INTO workspaces (id, name, description) VALUES
  ('clawback-labs', 'Clawback Labs', 'Payroll clawback recovery for mid-market employers'),
  ('nexops', 'NexOps', 'Operations intelligence and workflow automation')
ON CONFLICT (id) DO NOTHING;

INSERT INTO projects (id, workspace_id, name, status) VALUES
  ('proj-claw-q3', 'clawback-labs', 'Q3 Outreach Campaign', 'active'),
  ('proj-claw-icp', 'clawback-labs', 'ICP Refinement', 'active'),
  ('proj-nex-pilot', 'nexops', 'Pilot Onboarding', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO strategic_beliefs (workspace_id, content, sort_order) VALUES
  ('clawback-labs', 'ICP = 200–1,500 employees', 1),
  ('clawback-labs', 'Avoid enterprise first — no 5,000+ employee targets until 3 mid-market wins', 2),
  ('clawback-labs', 'Revenue before perfection — ship outreach before full product polish', 3),
  ('clawback-labs', 'Credibility over growth hacks — no fake case studies or inflated metrics', 4),
  ('nexops', 'NexOps remains open source — core workflow engine stays MIT licensed', 1),
  ('nexops', 'Guided onboarding beats self-serve for first 20 customers', 2),
  ('nexops', 'BCH ecosystem is a distribution channel, not the product', 3)
ON CONFLICT DO NOTHING;

INSERT INTO workspace_profiles (workspace_id, metrics, context_lines) VALUES
  (
    'clawback-labs',
    '[{"label": "Open decisions", "value": "4"}, {"label": "ICP band", "value": "200–1,500"}, {"label": "Q3 pipeline", "value": "12 targets"}]'::jsonb,
    '["Mid-market payroll clawback recovery", "Series B–D employers with compliance teams", "Avoid enterprise motion until 3 wins"]'::jsonb
  ),
  (
    'nexops',
    '[{"label": "Open decisions", "value": "2"}, {"label": "Pilot stage", "value": "3 accounts"}, {"label": "Mentor feedback", "value": "Pending"}]'::jsonb,
    '["Open-source ops intelligence", "BCH ecosystem partnerships", "Self-serve blocked on support playbook"]'::jsonb
  )
ON CONFLICT (workspace_id) DO UPDATE SET
  metrics = EXCLUDED.metrics,
  context_lines = EXCLUDED.context_lines,
  updated_at = NOW();

INSERT INTO entities (id, workspace_id, name, entity_type, confidence, summary, linked_decision_ids) VALUES
  (
    'a0000001-0000-4000-8000-000000000001',
    'clawback-labs',
    'Acme Corp',
    'company',
    0.62,
    'Series B HR expansion; conditional board fit. ~2,400 employees.',
    '["dec-acme-001"]'::jsonb
  ),
  (
    'a0000001-0000-4000-8000-000000000002',
    'clawback-labs',
    'BrightPay Inc',
    'company',
    0.78,
    'ICP band match; compliance team hiring signals.',
    '[]'::jsonb
  ),
  (
    'a0000001-0000-4000-8000-000000000003',
    'nexops',
    'BCH Alliance',
    'partner',
    0.55,
    'Ecosystem partnership window; mentor intro pending.',
    '[]'::jsonb
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO memory_chunks (workspace_id, chunk_type, content, summary, entity_name) VALUES
  ('clawback-labs', 'strategy_note', 'Target companies with dedicated compliance teams and recent Series B funding.', 'ICP strategy note', NULL),
  ('clawback-labs', 'entity_profile', 'Acme Corp uses legacy payroll stack. Compliance team exists per LinkedIn.', 'Acme profile', 'Acme Corp'),
  ('clawback-labs', 'research_summary', 'Acme Corp: Series B 2022, HR expansion, no public clawback litigation.', 'Acme research', 'Acme Corp'),
  ('nexops', 'strategy_note', 'Pilot customers need guided onboarding; self-serve blocked on support playbook.', 'Onboarding strategy', NULL)
ON CONFLICT DO NOTHING;
