# Reading Hermes sessions from state.db

Open read-only: `sqlite3 'file:/Users/<u>/.hermes/state.db?mode=ro'` (Python: `uri=True`).

Tables: `sessions(id, title, source, started_at, cwd, parent_session_id, archived, …)`,
`messages(session_id, role, content, tool_calls JSON, tool_name, timestamp, active, …)`.
Use `active=1` only (inactive rows are rewound/compacted). `tool_calls` is a JSON list of
`{function:{name, arguments}}`; tool results are `role='tool'` rows with `tool_name`.

## Sessions of a workstream / project dir
```sql
select id, title, datetime(started_at,'unixepoch') from sessions
where cwd like '<dir>%' and parent_session_id is null order by started_at;
```

## Candidate sessions for testing the method (short, retries, tool calls)
```sql
with s as (
 select s.id, s.title,
  (select count(*) from messages m where m.session_id=s.id and m.role='user') u,
  (select count(*) from messages m where m.session_id=s.id and m.role='tool') t,
  (select count(*) from messages m where m.session_id=s.id and m.role='tool' and
    (m.content like '%"error": "%' or m.content like '%"success": false%'
     or m.content like '%exit_code": 1%' or m.content like '%exit_code": 127%'
     or m.content like '%Traceback%')) e
 from sessions s where s.started_at > strftime('%s','now','-45 days')
  and s.parent_session_id is null)
select * from s where u between 1 and 4 and t between 12 and 40 and e>=3
order by e*1.0/t desc limit 30;
```

## Duration
```sql
select (max(timestamp)-min(timestamp))/60.0 from messages where session_id='<id>' and active=1;
```
