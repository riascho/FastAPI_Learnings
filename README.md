# FastAPI Project

I wanted to learn a bit more about building a server using FastAPI and refresh my Python skills, so I've used AI as my tutor and guide me through building this project. All code is written by myself and below are the steps taken for building this app and my learnings.

## Concepts learnt (AI summary)

The concept introduction from each lesson, in the order they were taught.

**Contents**

1. [Virtual environments](#1-virtual-environments)
2. [Dependency manifests](#1½-dependency-manifests)
3. [Your first endpoint](#2-your-first-endpoint)
4. [Side quest: PEP 8 and auto-formatting](#side-quest-pep-8-and-auto-formatting)
5. [Path parameters and type hints](#3-path-parameters-and-type-hints)
6. [Pydantic models and request bodies](#4-pydantic-models-and-request-bodies)
7. [Status codes and HTTPException](#5-status-codes-and-httpexception)
8. [PUT and DELETE](#6-put-and-delete)
9. [Query parameters](#7-query-parameters)
10. [Project structure](#8-project-structure)
11. [Depends and dependency injection](#9-depends-and-dependency-injection)
12. [The database layer](#10-the-database-layer)
13. [Swapping the routes over](#11-swapping-the-routes-over)
14. [Automated tests](#12-automated-tests)
15. [Test isolation](#13-test-isolation)
16. [Appendix: follow-up questions](#appendix-follow-up-questions)

---

### 1. Virtual environments

If you `pip install` packages globally, every Python project on your machine shares one pile
of libraries. Project A needs `fastapi==0.100`, project B needs `0.115` — they can't coexist,
and upgrading one silently breaks the other.

A **virtual environment** is a self-contained folder holding its own copy of Python plus its
own `site-packages` directory. "Activating" it just puts that folder's `bin/` at the front of
your shell's `PATH`, so `python` and `pip` resolve to the project-local ones. Deactivate (or
delete the folder) and your system Python is untouched.

Two packages to install:

- **`fastapi`** — the framework. It gives you the decorators, validation, and auto-generated docs.
- **`uvicorn`** — the _server_. FastAPI only defines how to respond to requests; it doesn't
  listen on a port. Uvicorn is an **ASGI** server (Asynchronous Server Gateway Interface) — the
  standard contract between a Python web app and the thing holding the network socket. Think
  "FastAPI writes the replies, uvicorn runs the mailroom."

This app is built as an **ASGI application**. In practical terms, ASGI is designed for modern,
async Python web apps: it handles HTTP requests and can also support WebSockets, lifespan hooks,
and multiple concurrent connections without blocking the whole process. **WSGI** (the older
standard used by frameworks like Flask and Django's traditional server setup) is a synchronous
request/response interface: each request is handled one at a time, and it's less suited to async
work or long-lived connection patterns. FastAPI sits on top of ASGI, which is why it can use
`async def` endpoints and efficient concurrency.

Activation is a convenience, not a requirement: the venv's `bin/` contains real executables
you can call by path (`.venv/bin/pip`), which works regardless of `PATH`. Activation lasts only
for the shell that ran it.

---

### 1½. Dependency manifests

Your `.venv` folder is **disposable and local**. It's hundreds of files, it's platform-specific
(compiled binaries inside won't work on Linux), and it never gets committed to git. So if you
delete it, hand the project to a colleague, or deploy it to a server, how does anyone know what
to install?

A `requirements.txt` is the answer: a plain text file, one package per line, declaring what
your project needs. It's the _source of truth_; the venv is a build artifact you regenerate
from it.

#### Two ways to write one

**Option A — generate it from the environment:** `pip freeze > requirements.txt` prints every
installed package as `name==exact.version`. Perfect reproducibility — but it captures
**transitive dependencies** too (things your dependencies depend on), so the file no longer
tells you what the project actually _wants_.

**Option B — hand-write your direct dependencies.** Short, readable, self-documenting; pip
resolves the transitive ones at install time. The cost: those get whatever version is current
on install day.

Option B for learning projects and libraries. Option A (or a proper lockfile) for production
where byte-identical builds matter. Real teams often do both.

#### Version specifiers

| Written as         | Means                                             |
| ------------------ | ------------------------------------------------- |
| `fastapi`          | any version — newest available                    |
| `fastapi==0.142.2` | exactly this version                              |
| `fastapi>=0.142.2` | this or newer                                     |
| `fastapi~=0.142.2` | "compatible release" — `>=0.142.2` but `<0.143.0` |

#### Dependency tiers

A formatter is needed to _develop_ the project, not to _run_ it — a server deploying your API
shouldn't install one. Hence a second file, `requirements-dev.txt`, conventionally starting with
`-r requirements.txt` ("also include everything from that file") so one command installs both
tiers while production installs only the first.

**Habit worth keeping:** every time you `pip install` something new, add it to the manifest in
the same breath. Drift between the two is one of the most common sources of "works on my machine."

---

### 2. Your first endpoint

**1. The app object.** You import the `FastAPI` class and create one instance, conventionally
named `app`. That object _is_ your application — a registry of routes that also happens to be a
callable conforming to the ASGI interface. Uvicorn takes this object and feeds HTTP requests
into it.

**2. Path operation decorators.** A route is a function with a decorator above it, binding two
things together:

```
@app.get("/tasks")
  │    │     │
  │    │     └── the path (the URL after the domain)
  │    └──────── the HTTP method, lowercased
  └───────────── your app object
```

FastAPI calls these **path operations** — "path" being the URL, "operation" the HTTP method.
There's `@app.get`, `.post`, `.put`, `.delete`, and so on. The function underneath is the **path
operation function**: it runs when a request matches, and whatever it returns becomes the
response body.

**3. Return values become JSON automatically.** Return a Python dict (or list, or Pydantic
model) and FastAPI serialises it to JSON and sets `Content-Type: application/json`. No manual
`json.dumps`, no response object to build.

#### `async def` vs `def`

Write plain `def` unless your function body actually `await`s something. FastAPI runs sync
functions in a thread pool so they never block the event loop — both are correct and fast.

#### What you get for free

`/docs` is an interactive Swagger UI generated entirely from your type hints and route
definitions, where you can execute requests from the browser. `/openapi.json` is the
machine-readable schema it's built from. You write zero lines of documentation to get either.

---

### Side quest: PEP 8 and auto-formatting

Three tools that get confused:

| Tool type        | Job                                                                 | Changes your code?             |
| ---------------- | ------------------------------------------------------------------- | ------------------------------ |
| **Formatter**    | layout only — whitespace, line breaks, quote style, trailing commas | yes, but never the meaning     |
| **Linter**       | finds problems — unused imports, undefined names, shadowed builtins | only if you ask it to auto-fix |
| **Type checker** | verifies your annotations are consistent                            | no                             |

#### What PEP 8 is

A **PEP** is a Python Enhancement Proposal — the numbered design documents defining the
language's evolution. PEP 8, from 2001, is the official style guide: 4-space indentation,
`snake_case` for functions and variables, `PascalCase` for classes, spacing around operators,
import ordering. It's why Python code from different authors looks remarkably uniform.

It's a _document_, not a program. You need a tool to apply it.

#### Ruff

A formatter _and_ linter in one Rust binary, typically 10–100× faster than the Python tools it
replaces. It consolidates `black` (formatting), `flake8` (linting), `isort` (import sorting),
and `pyupgrade` (modernising syntax) into one tool with one config.

**Honest caveat on line length:** PEP 8 says 79 characters. Ruff and Black default to **88** — a
deliberate deviation, because Black's authors found it produced fewer awkward line breaks. So
"PEP 8 formatting" in practice means "PEP 8 as interpreted by Black."

#### Import ordering

PEP 8 wants three groups, blank-line separated, alphabetised within each:

```
1. standard library    (typing, os, json)
2. third-party         (fastapi, pydantic)
3. first-party/local   (models, storage)
```

**An important distinction:** format-on-save runs the _formatter_, which deliberately won't
reorder imports (reordering can change behaviour when imports have side effects). Import
sorting is a _lint fix_, requiring `editor.codeActionsOnSave`. And "lint passed" is only as
strong as the rules you enabled — most rule sets are off by default.

---

### 3. Path parameters and type hints

Real APIs need paths with variables in them — `/tasks/1`, `/tasks/2`, `/tasks/837` all hitting
one piece of code. That's a **path parameter**. Declare it with braces in the path, then accept
it as a function argument **with the same name**:

```
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
              │        │
              │        └── the type hint — this is where the magic is
              └─────────── name must match the brace in the path exactly
```

#### Why the type hint is the important part

A URL is just text. `/tasks/1` carries the characters `"1"`, not the number `1` — HTTP has no
concept of types. Most frameworks hand you the string and leave conversion to you. FastAPI reads
your annotation and does three things:

1. **Parses** — converts `"1"` into the integer `1`
2. **Validates** — if the value can't become an `int`, the request never reaches your function;
   FastAPI returns **422 Unprocessable Entity** with a JSON body naming the failing parameter
3. **Documents** — `/docs` shows the parameter typed as an integer

One annotation, three jobs. This is the central idea of FastAPI: **your type hints are the
specification**, not just hints.

#### Type hints refresher

Annotations arrived in Python 3.5, written `name: type`. The crucial thing: **Python itself
ignores them completely at runtime.** They're metadata stored in `f.__annotations__`. Tools
choose to read them — type checkers before you run, editors for autocomplete, and FastAPI _at
runtime_ to generate validators.

#### Reading a 422

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "task_id"],
      "msg": "Input should be a valid integer...",
      "input": "abc"
    }
  ]
}
```

- **`type`** — machine-readable error code, stable enough for a client to branch on
- **`loc`** — the **location** as a path: `["path","task_id"]`, or `["body","title"]` for bodies.
  This is how a client knows _which input_ to highlight
- **`msg`** — human-readable explanation
- **`input`** — the offending value echoed back

`detail` is an **array** because Pydantic reports _every_ validation failure at once, not just
the first. One round trip tells the client everything wrong.

#### Route order matters

FastAPI checks routes **top to bottom** and uses the first match. A fixed path that could also
match a parameterised pattern — `/tasks/stats` alongside `/tasks/{task_id}` — must come **first
in the file**, or it gets swallowed by the parameter route.

---

### 4. Pydantic models and request bodies

Reading is done; now the client has to _send_ you data — a JSON object in the **request body**.
Bodies are what `POST`, `PUT`, and `PATCH` use; `GET` conventionally doesn't have one.

A body is untrusted input from the outside world. So you need a **schema**: a declaration of
what a valid task looks like. In FastAPI that's a **Pydantic model** — a class inheriting from
`BaseModel` whose body is just annotated field names:

```python
class Thing(BaseModel):
    name: str              # required — no default
    count: int = 0         # optional — has a default
```

No `__init__`, no boilerplate. Pydantic reads the annotations and generates a constructor, a
validator, a JSON serialiser, and a JSON Schema. Same principle as type hints, scaled to whole
objects.

**Required vs optional is determined by the default value.** No default → the client must supply
it. Has a default → the client may omit it and Pydantic fills it in.

#### How FastAPI knows a parameter is the body

The rule worth memorising. For each function parameter, FastAPI looks at the annotation:

| The annotation is…                                                         | FastAPI reads it from…               |
| -------------------------------------------------------------------------- | ------------------------------------ |
| a Pydantic model                                                           | the **request body**, parsed as JSON |
| a scalar (`int`, `str`, `bool`) whose name matches a `{brace}` in the path | the **path**                         |
| a scalar whose name is _not_ in the path                                   | the **query string**                 |

No decorators or markers needed — the type decides.

#### Models use dot access, dicts use brackets

```python
tasks[0]["title"]      # dict → brackets
new_task.title         # Pydantic model → dot
```

Mixing these up is the single most likely error in this lesson.

#### Two models, or one?

What the client _sends_ and what your API _stores_ are different shapes: the client sends a
`title` but must not choose the `id` — the server assigns that. So the model describing the
request body should have **no `id` field**. This is why real APIs commonly have a `TaskCreate`
model (input) separate from a `Task` model (stored/returned).

---

### 5. Status codes and HTTPException

Every HTTP response carries a three-digit status code, and it's the **primary** signal of what
happened — the body is secondary. Clients branch on it, HTTP caches respect it, load balancers
and monitoring count it, and `fetch()` exposes it as `response.ok`.

| Range | Meaning                                               | Who's at fault |
| ----- | ----------------------------------------------------- | -------------- |
| `2xx` | success                                               | —              |
| `3xx` | redirection                                           | —              |
| `4xx` | **client** error — bad request, don't retry unchanged | the caller     |
| `5xx` | **server** error — your code broke, retrying may work | you            |

| Code  | Name                 | Use for                                      |
| ----- | -------------------- | -------------------------------------------- |
| `200` | OK                   | successful `GET`, `PUT`                      |
| `201` | Created              | successful `POST` that made a new resource   |
| `204` | No Content           | successful `DELETE` — body **must** be empty |
| `404` | Not Found            | the requested resource doesn't exist         |
| `422` | Unprocessable Entity | body/params failed validation (automatic)    |

#### Why returning 200 with an error body is a real bug

```
HTTP 200 OK
{"error": "no task for id 99 found!"}
```

A `200` is a promise that the request succeeded. A client doing `if (response.ok)` proceeds
happily, then crashes reading `task.title` on an object that has no title. Your monitoring shows
a 100% success rate while users see broken pages. The error is _invisible_ to every layer that
only reads status codes. Sometimes called "200 OK lying."

#### `HTTPException`

```python
raise HTTPException(status_code=404, detail="Task not found")
```

**You `raise` it, you don't `return` it.** `raise` aborts the function immediately and unwinds
the call stack; FastAPI has a handler that catches `HTTPException` and converts it into a proper
response. This is why it works from anywhere — including from a helper or dependency three calls
deep, which `return` could never do.

**`detail` becomes the response body**, wrapped as `{"detail": "..."}` — matching the key in
FastAPI's own 422s, so your errors are shaped consistently with the framework's.

#### Setting the success status code

For non-200 successes, declare it **on the decorator**: `@app.post("/tasks", status_code=201)`.
It belongs there because it's part of the route's _contract_, which means `/docs` documents it.
A value returned at runtime couldn't be documented. FastAPI also ships constants —
`status.HTTP_201_CREATED` — identical in behaviour, more readable, autocompletable.

#### Guard clauses

Because `raise` terminates the function, an `else` after it adds indentation without meaning.
The idiomatic Python form handles the bad case and exits, leaving the happy path at the base
indentation level:

```
if <bad condition>:
    raise ...
<normal path, un-indented>
```

The payoff compounds: with three validations, nested `else` blocks bury the happy path four
levels deep, while guard clauses read as "reject, reject, reject, then do the work."

#### Don't Repeat Yourself

Three copies of one lookup loop is three places to fix a bug. Extract it into a **plain function
with no decorator** — not a route, just a helper your routes call.

---

### 6. PUT and DELETE

#### PUT vs PATCH

Two update verbs; the distinction is about **what the body means**:

|                     | `PUT`                                     | `PATCH`                       |
| ------------------- | ----------------------------------------- | ----------------------------- |
| Body contains       | the **complete** new state                | only the fields to change     |
| Missing fields mean | "set to default / absent"                 | "leave unchanged"             |
| `{"done": true}`    | replaces the whole task, wiping the title | flips `done`, title untouched |

`PUT` is a **replacement**, `PATCH` is a **merge**. `PATCH` needs a model where _every_ field is
optional — a different model and a fiddlier endpoint.

#### Idempotency

An operation is **idempotent** if doing it five times leaves the system in the same state as
doing it once.

| Verb     | Idempotent? | Why                                             |
| -------- | ----------- | ----------------------------------------------- |
| `GET`    | ✅          | reading changes nothing                         |
| `PUT`    | ✅          | setting the same state repeatedly = same result |
| `DELETE` | ✅          | already gone stays gone                         |
| `POST`   | ❌          | **five calls create five tasks**                |

This isn't academic. When a request times out, the client doesn't know whether the server
processed it. If the verb is idempotent, retrying is safe. If it's `POST`, retrying might
duplicate the resource — which is why payment APIs make you send an "idempotency key."

It's also why `PUT` returns `200`, not `201`: `201 Created` claims something new came into
existence, but a `PUT` to an existing resource just overwrites it.

#### 204 No Content

For `DELETE` there's nothing meaningful to send back — the resource is gone. The spec says a 204
response **must not** have a body, so your function returns nothing at all. Python makes that
natural: a function with no `return` returns `None`, and FastAPI sends an empty body.

#### Mutation vs rebinding — the trap

Dicts are **mutable**, and your lookup helper returns a _reference_ to the dict inside the list,
not a copy. So `found_task["title"] = x` modifies the one in the list. No reinsertion needed.

But deleting by filtering looks tempting and breaks:

```python
tasks = [t for t in tasks if t["id"] != task_id]     # BROKEN inside a function
```

Python decides a variable's scope at _compile_ time: because the function body assigns to
`tasks`, Python treats it as a **local variable throughout the entire function** — so reading it
on the right-hand side raises `UnboundLocalError`. Even if it worked, you'd create a new local
list and leave the module-level one untouched.

| Operation                                            | Effect on the module-level list   |
| ---------------------------------------------------- | --------------------------------- |
| `tasks.append(x)`, `tasks.remove(x)`, `tasks[0] = y` | ✅ mutates the real object        |
| `tasks = anything`                                   | ❌ creates/assigns a _local_ name |

**Mutate, don't rebind.** Rebinding a module-level variable from inside a function needs
`global`, which is a smell in application code and entirely avoidable here.

---

### 7. Query parameters

`GET /tasks` returning everything is fine with 2 tasks and catastrophic with 50,000. Clients
need options, and those go in the **query string**:

```
/tasks?done=false&limit=20
      │     │          │
      │     │          └── second pair
      │     └── first key=value pair
      └── ? begins the query string, & separates pairs
```

No new syntax to learn — you already know the rule from Lesson 4. A scalar parameter whose name
is **not** in the path becomes a query parameter. Same parsing, same validation, same 422s, same
auto-documentation.

#### Required vs optional, again by default value

```python
def get_all_tasks(limit: int):          # no default → REQUIRED
def get_all_tasks(limit: int = 10):     # default → optional
```

A required query parameter means `/tasks` with no query string returns 422. Occasionally
correct, usually annoying. Filters should almost always be optional.

#### The three-state problem

The obvious thing is wrong:

```python
def get_all_tasks(done: bool = False):      # BROKEN
```

`/tasks` with no query string sets `done` to `False`, so you filter to unfinished tasks only.
**You've made it impossible to list all tasks.** The default didn't mean "no filter," it meant
"filter to false."

A boolean has two states, but you need **three**: `true`, `false`, and _not specified_:

```python
done: bool | None = None
```

`bool | None` is a **union type** — "either a `bool` or `None`" (Python 3.10+; older code writes
`Optional[bool]`, which means the same). Then branch on `if done is not None:` — "the caller
actually asked for a filter." `None` as a sentinel for "absent" is a pervasive Python pattern.

#### How FastAPI parses a boolean from a URL

The query string carries text, so `?done=false` arrives as characters. FastAPI accepts these,
case-insensitively:

| Parsed as `True`         | Parsed as `False`         |
| ------------------------ | ------------------------- |
| `true`, `1`, `yes`, `on` | `false`, `0`, `no`, `off` |

Anything else → 422.

#### Constraints with `Query`

A plain `limit: int = 10` accepts `?limit=-5` or `?limit=999999999`. To constrain it, attach
metadata to the annotation:

```python
limit: Annotated[int, Query(ge=1, le=100)] = 10
```

- `Annotated[X, ...]` — standard-library syntax for "this is type `X`, plus extra metadata."
  Type checkers see `int`; FastAPI reads the extra part
- `Query(...)` — declares query-parameter rules: `ge`, `le`, `gt`, `lt`, `min_length`,
  `max_length`, `pattern`, `description`

Violations become 422s automatically and `/docs` renders the constraints. This `Annotated` form
is current FastAPI's recommended style.

#### Filters must compose

Filter progressively from the _previous result_, not from the original collection each time.
Rebuilding from the source in the second filter silently discards the first.

#### Unknown query parameters are ignored

FastAPI extracts the parameters you declared and ignores the rest; it does not reject unexpected
ones. So a typo like `?donee=true` silently returns unfiltered results rather than telling you.

---

### 8. Project structure

A 99-line `main.py` holding four unrelated jobs — app creation, data storage, the data schema,
and seven route handlers — is fine at that size. At 500 lines you can't find anything, two
people can't edit it without conflicts, and you can't test the routes without importing the
whole world.

So split by **responsibility** — and critically, **without changing any behaviour**. That's what
makes it a _refactor_: the external API must respond identically afterward.

#### Modules and packages

- A **module** is a single `.py` file. Import from it with `from models import Task`
- A **package** is a _directory_ of modules containing a file named `__init__.py`

`__init__.py` is usually **empty**. Its presence marks the directory as an importable package.
(Python 3.3+ can import directories without it via "namespace packages," but the behaviour
differs subtly and nearly every real project includes the file.)

#### `APIRouter`

You can't use `@app.get` in another file — `app` lives in `main.py`, and if a router module
imported it while `main.py` imported the router, you'd have a **circular import**. FastAPI's
answer:

```python
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("")          # note: empty string, not "/"
def get_all_tasks(...): ...
```

An `APIRouter` has the same decorator methods as `app` but it's a **collection of routes, not an
application**. It registers nothing until `main.py` calls `app.include_router(tasks.router)`, at
which point FastAPI copies every route in, applying the prefix. Dependencies flow one direction
only — `main` imports `routers`, never the reverse — so no cycle.

- **`prefix="/tasks"`** — prepended to every path inside. **Must not end in a slash**
- **`tags=["tasks"]`** — groups these endpoints under a collapsible heading in `/docs`

⚠️ **The prefix gotcha:** with `prefix="/tasks"`, the collection route's path is the **empty
string** `""`, giving exactly `/tasks`. Writing `"/"` gives `/tasks/` — a _different_ URL that
only works via a 307 redirect.

#### The shared-state subtlety

Does each importer of a module-level list get its own copy? No. **Python caches modules in
`sys.modules`** — the first import executes the file; every subsequent import returns the cached
object. So there is exactly one list.

But `from storage import tasks` binds a **local name** in your module pointing at that one
object:

| In another module                     | Effect on the real list            |
| ------------------------------------- | ---------------------------------- |
| `tasks.append(x)` / `tasks.remove(x)` | ✅ mutates the shared object       |
| `tasks = [...]`                       | ❌ rebinds only this module's name |

Same mutate-don't-rebind rule, now across module boundaries. (The alternative, `import storage`
then `storage.tasks`, goes through the module object every time and so always sees rebindings —
more robust, slightly noisier.)

---

### 9. `Depends` and dependency injection

#### What dependency injection means

Instead of your function _fetching_ what it needs, it **declares** what it needs and the
framework supplies it. You've been using this all along without the label:

```python
def get_task(task_id: int)          # "I need an int from the path" — FastAPI provides it
def create_task(payload: Task)      # "I need a validated body" — FastAPI provides it
```

`Depends` extends that to arbitrary values: "I need the result of calling _this function_."

```python
def get_task(task: dict = Depends(get_existing_task)):
    return task
```

#### The part that makes it powerful

**A dependency can declare its own parameters, and FastAPI resolves them the same way it
resolves a route's.** So if the dependency is written `def get_existing_task(task_id: int)`,
FastAPI reads _its_ signature, matches `task_id` to the `{task_id}` in the route's path, parses
and validates it, and passes it in. Which means:

- your route function **doesn't need `task_id` in its signature at all**
- `/docs` still documents the path parameter, because FastAPI walks the whole dependency tree
  when building the schema
- if the dependency raises, the route function never runs

#### Why not just a plain helper function?

A helper would also remove duplication. `Depends` buys four more things:

1. **Parameter resolution** — the dependency gets `task_id` injected rather than handed to it
2. **Documentation** — parameters and errors it declares appear in the OpenAPI schema
3. **Per-request caching** — if two dependencies in one request share a sub-dependency, it
   executes **once** and the result is reused. Critical when that sub-dependency opens a
   database connection, since the route and its dependency then share the same transaction
4. **Override for tests** — `app.dependency_overrides` lets you swap any dependency for a fake
   without touching the route. The single biggest practical reason the pattern exists

#### Where dependencies live

A dependency that raises `HTTPException` is an HTTP concern. Keeping `storage`/`database`
modules free of FastAPI imports is a property worth protecting: storage knows about _data_, not
about _the web_, so it stays reusable in a CLI or a scheduled job. A separate `dependencies.py`
becomes the bridge layer that translates between them.

#### A Python rule you'll hit immediately

```python
def update_task(payload: Task, task: dict = Depends(get_existing_task)):   # ✅
def update_task(task: dict = Depends(get_existing_task), payload: Task):   # ❌ SyntaxError
```

**Parameters without defaults must come before parameters with defaults.** `Depends(...)` is
used _as_ a default value, so it has to come last.

This constraint is precisely why modern FastAPI prefers `Annotated`:

```python
task: Annotated[dict, Depends(get_existing_task)]      # no default → order is free
```

#### Ruff `B008` and mutable default arguments

`Depends()` in a default triggers Ruff rule `B008`. The rule exists for a real reason:

**Default values are evaluated once, when the `def` statement runs — not on each call.**

```python
def add_item(item, items=[]):       # the [] is created ONCE, at definition time
    items.append(item)
    return items

add_item(1)      # [1]
add_item(2)      # [1, 2]   ← the SAME list
```

Every call without an explicit `items` shares one list that accumulates forever. Likewise
`def f(t=datetime.now())` freezes the timestamp at import time. The convention is
`def f(items=None)` plus `if items is None: items = []` — the same `None`-as-sentinel pattern as
the `done` query parameter.

But it's a **false positive** for FastAPI. `Depends(fn)` returns a small **marker object** that
records "resolve this parameter by calling that function." FastAPI reads the signature at
startup, finds the marker, and **never uses the default as a value**. Being evaluated once is
exactly what's wanted. Same for `Query()`, `Path()`, `Body()`, `Header()`.

Three fixes: switch to `Annotated` (removes the default entirely, so the warning becomes
inapplicable rather than suppressed), allowlist the calls via `extend-immutable-calls` in
`ruff.toml`, or `# noqa: B008` at the point of use.

---

### 10. The database layer

Data in a Python list dies with the process. Three problems a database solves:

1. **Persistence** — data outlives the process
2. **Concurrency** — two workers can't safely share a Python list; a database handles
   simultaneous access with locking and transactions
3. **Querying at scale** — filtering 500,000 rows in Python means loading all 500,000 into
   memory first. A database does it with an index and returns 20

### Why SQLite

It's in Python's **standard library** — no install, no server, no credentials. The entire
database is a single file, and the library runs _inside_ your process rather than over a
network socket. Ideal for learning, and production-viable for low-write single-server apps. Its
limitation is writes: one writer at a time, process-wide. Standard SQL means most of what you
learn transfers to PostgreSQL.

#### SQL in one table

| Statement      | Purpose        | Shape                                     |
| -------------- | -------------- | ----------------------------------------- |
| `CREATE TABLE` | define a table | `CREATE TABLE name (col TYPE, ...)`       |
| `INSERT`       | add rows       | `INSERT INTO name (cols) VALUES (?, ?)`   |
| `SELECT`       | read rows      | `SELECT cols FROM name WHERE ... LIMIT n` |
| `UPDATE`       | modify rows    | `UPDATE name SET col = ? WHERE ...`       |
| `DELETE`       | remove rows    | `DELETE FROM name WHERE ...`              |

SQL keywords are case-insensitive; uppercasing them is convention so they stand out from your
own names.

#### SQLite's types — and the missing boolean

Only five storage classes: `NULL`, `INTEGER`, `REAL`, `TEXT`, `BLOB`.

**There is no boolean type.** `done` is stored as `0`/`1`. Python's `sqlite3` accepts `True` on
the way in (because `bool` is a subclass of `int`), but on the way out you get the integer `1`.
JSON distinguishes `true` from `1`, so without an explicit `bool()` conversion your API contract
silently changes. This is the kind of detail an ORM hides from you.

SQLite is also **dynamically typed** — the column type is a hint ("type affinity"), not a hard
constraint, so it will store text in an `INTEGER` column. Postgres would reject it. Don't rely
on the database to enforce types; that's what Pydantic is for.

#### The `sqlite3` module

```python
conn = sqlite3.connect("tasks.db")     # opens (and creates if absent) the file
cursor = conn.execute(sql, params)      # runs one statement, returns a cursor
rows = cursor.fetchall()                # all result rows as a list
row = cursor.fetchone()                 # one row, or None if there are none
conn.commit()                           # make writes permanent
conn.close()                            # release the file
```

- **`connect()`** creates the file if absent — so there's no separate setup step, and a typo in
  the filename silently hands you a pristine empty database rather than failing
- **`execute()`** on the connection is a shortcut that makes a cursor and returns it, so you can
  chain `.fetchone()`. (A **cursor** is the handle to a result set.) A cursor is also
  _iterable_, which streams rows instead of materialising them all like `fetchall()`
- **`commit()`** is required for `INSERT`/`UPDATE`/`DELETE`/`CREATE`. The driver opens a
  transaction implicitly, so **without it your writes are discarded when the connection closes**
- **`fetchone()` returns `None`** when there's no row — which plugs into an `is None` 404 check.
  It always returns a _row_, even for `SELECT COUNT(*)`: a result set is always a table, so the
  number arrives inside a one-row, one-column container

#### ⚠️ Parameterised queries — the most important thing

Never build SQL with f-strings. **Ever.**

```python
conn.execute(f"SELECT * FROM tasks WHERE title = '{search}'")     # ❌ NEVER
conn.execute("SELECT * FROM tasks WHERE title = ?", (search,))    # ✅ ALWAYS
```

If a caller sends `?search=' OR 1=1 --`, the f-string version becomes:

```sql
SELECT * FROM tasks WHERE title = '' OR 1=1 --'
```

`1=1` is always true, `--` comments out the rest, and the filter is gone — every row returned.
Substitute `'; DROP TABLE tasks; --` and the table is gone. This is **SQL injection**, and it
remains one of the most exploited vulnerabilities in the world despite the fix being this simple.

The `?` placeholder fixes it structurally: the driver sends the statement and the values
**separately**, so the value is never parsed as SQL and cannot become code no matter what
characters it contains.

Two syntax notes: parameters go in a **sequence** (tuple or list), and a single parameter needs a
trailing comma — `(search,)`. Placeholders substitute **values only**, never table or column
names.

#### `row_factory`

By default rows come back as plain tuples — `row[1]` for the title is unreadable and breaks when
you reorder columns. Setting `conn.row_factory = sqlite3.Row` enables **access by column name**
(`row["title"]`) and `dict(row)` conversion. Set it right after connecting.

#### Idempotent initialisation

`CREATE TABLE IF NOT EXISTS` plus a "seed only if the table is empty" count check makes startup
initialisation safe to run on every boot. Without the count check, every startup would
re-insert the seed rows.

#### Relative paths

`DB_PATH = "tasks.db"` resolves against the **current working directory**, not the module's
location — so starting the app from a different folder silently creates a _second_, empty
database. `Path(__file__).parent / "tasks.db"` anchors it to the source file instead. (`__file__`
is a module-level variable holding the current source file's path; `pathlib` overloads `/` to
join path segments.)

---

### 11. Swapping the routes over

#### The `yield` dependency — managing a resource's lifetime

A connection must be **opened before** the request and **closed after** it. A regular dependency
can only do the "before" half. So FastAPI supports dependencies that `yield`:

```python
def get_db():
    conn = get_connection()
    try:
        yield conn          # ← request is handled right here
    finally:
        conn.close()        # ← runs after the response is sent
```

**What `yield` does.** A function containing `yield` is a **generator function** — calling it
doesn't run the body, it returns a generator object. The body runs only as values are pulled
from it, and it **pauses** at each `yield`, keeping all its local state alive.

FastAPI exploits that precisely: it advances the generator to the `yield`, takes the connection,
injects it into your route, waits for the response, then resumes the generator so the lines
after `yield` execute. One function, split across the request lifecycle.

**Why `try`/`finally`.** `finally` runs **whether or not an exception was raised**. Essential
here: a 404 raised by a dependency would otherwise skip the close and leak a file handle on every
missing-task request. A few thousand of those and your process runs out of file descriptors.

This is _the_ standard pattern for database sessions in FastAPI.

#### Sub-dependencies and the per-request cache

A dependency can depend on another dependency, and FastAPI resolves the whole tree before your
route runs. The caching from Lesson 9 now pays off concretely: a `PUT` route needs both the task
(from the lookup dependency) and a connection for the `UPDATE`. Both paths lead to `get_db`, but
it's called **once per request** and reused — so the dependency and the route body share the
_same_ connection and therefore the same transaction. Two connections could deadlock against
each other, since SQLite permits only one writer.

#### Filtering moves into SQL

Python-side filtering loads every row and discards most of them. Pushing the work down to where
the data and indexes are:

```sql
SELECT * FROM tasks WHERE done = ? AND title LIKE ? LIMIT ?
```

- **`LIKE`** with `%` wildcards does substring matching. The `%` characters belong to the
  **value**, not the SQL — pass `f"%{search}%"` as a parameter. Still fully safe
- **`LIKE` is case-insensitive for ASCII in SQLite by default** — so case-insensitivity comes
  free and the `.lower()` calls disappear. (Only for ASCII; accented characters still compare
  case-sensitively)

#### Building dynamic SQL safely

The filters are optional, so the `WHERE` clause varies. Build it from two parallel lists:

```python
conditions = []      # SQL fragments — written by YOU, never from input
params = []          # the values — always passed via ?
```

**The safety rule: the SQL _structure_ comes only from string literals in your source; every
user-supplied _value_ goes through a `?`.** Follow that and dynamic SQL is perfectly safe.

Placeholders are filled **positionally, left to right**, so the params list order must match the
SQL. A mismatch doesn't error — it filters on the wrong things.

#### `lastrowid`

After an `INSERT`, `cursor.lastrowid` reports the id SQLite auto-assigned. This replaces
computing `max(id) + 1`, and it's _correct_ in a way that computation never was: the database
assigns it atomically, so two simultaneous inserts can't collide.

Re-`SELECT`ing the row after a write costs one cheap query and guarantees your response reflects
what's actually stored rather than what you _think_ you stored.

---

### 12. Automated tests

The argument for this lesson, lived earlier in the project: a test of
`?done=false&search=groceries` returned the right answer and the code was broken — the second
filter was silently discarding the first. It took a _different_ input to expose it.

Hand-crafted curl commands have two problems: you only re-run the cases you remember, and
nothing stops a change in one lesson from breaking something from five lessons ago.
**Automated tests are how you make "everything still works" a fact rather than a hope.**

#### `TestClient`

FastAPI ships a test client that talks to your app **without a server and without a network**:

```python
client = TestClient(app)
response = client.get("/tasks")
```

It imports your `app` object and calls into the ASGI interface directly, in-process. So: no
uvicorn, no port, nothing to start or stop; milliseconds per request; and it works even if your
dev server isn't running. The API mirrors `requests`/`httpx` — `.get`, `.post(json=...)`,
`.put`, `.delete` — and responses give you `.status_code`, `.json()`, `.text`.

Built on **httpx2** in Starlette 1.7+ (plain `httpx` will not work).

#### pytest

- test **files** are named `test_*.py`
- test **functions** are named `test_*`
- a test passes if it finishes, and fails if an `assert` is false or an exception escapes

No classes, no `self`, no `assertEqual`. **`assert` is a plain Python statement** that raises
`AssertionError` if the condition is falsy; pytest rewrites assertions to show the actual values
on failure, so you get `assert 404 == 200` rather than a bare error.

#### The isolation problem

Tests that write to your real database give you two bad outcomes: development data fills with
junk, and — worse — tests become **order-dependent and non-repeatable**. A test asserting "there
are 3 tasks" passes once, then fails forever after a create test runs.

Good tests are **isolated**: each starts from a known state and leaves nothing behind.

#### A test that cannot fail provides no information

Two early tests were vacuous:

```
all([])  -> True      # "every returned task is done" passes on an EMPTY list
[] == [] -> True      # two empty responses compare equal
```

`all()` over an empty iterable is _vacuous truth_. So a broken filter returning nothing makes
the test pass. Concretely: change the SQL to `WHERE done = 99`, get `[]` back, and a test named
"filter by done" still reports PASSED.

The fix is an **emptiness guard** before asserting a property of the contents — better still,
assert something specific, since you control the seed data.

**A test that cannot fail is worse than no test**, because the green checkmark reads as a
guarantee that isn't there. The standard way to check a test is honest: **temporarily break the
code it covers and confirm the test goes red.**

---

### 13. Test isolation

#### Two separate injection systems that look alike

|                     | pytest fixtures                               | FastAPI `Depends`                |
| ------------------- | --------------------------------------------- | -------------------------------- |
| Comes from          | **pytest**                                    | **FastAPI**                      |
| Injects into        | test functions                                | route functions and dependencies |
| How it matches      | the parameter **name** matches a fixture name | the parameter has `Depends(...)` |
| Where you define it | `conftest.py` or a test file                  | anywhere                         |
| Setup/teardown      | `yield` inside the fixture                    | `yield` inside the dependency    |

They are **unrelated implementations of the same idea**, built by different people. pytest knew
nothing about FastAPI when fixtures were designed.

#### `app.dependency_overrides`

Your routes never mention a database file; they declare `Depends(get_db)`. So you can replace
what that resolves to:

```python
app.dependency_overrides[get_db] = some_other_function
```

A plain dict on your app, keyed by **the original dependency function object**. When FastAPI
resolves a dependency it checks this dict first — so every route and every sub-dependency
transparently receives the test connection instead.

Nothing in your application code changes. No `if TESTING:` branches, no environment variables.
That's the whole argument for injecting dependencies rather than importing them.

⚠️ **The dict is global and persists between tests.** Clear it in teardown, or an override from
one test leaks into every test that follows — pointing at a connection that's already closed.

#### An in-memory database

SQLite accepts the special filename `":memory:"`, creating the database in RAM: fast, no files,
no cleanup, and it vanishes when the connection closes.

That last property has a consequence to design around: **each connection to `":memory:"` gets
its own separate database.** Since `get_db` opens a fresh connection per request, the override
must yield **one connection, held open for the whole test** — and therefore must _not_ close it.
The fixture owns that lifetime.

Why that matters concretely: the override is called once per HTTP request. If it closed the
connection, request 1 would destroy the database and request 2 would see an empty new one — so a
test that creates a task and reads it back would fail.

#### Fixtures

A fixture is **a named recipe for something a test needs**, requested by naming it as a
parameter:

```python
@pytest.fixture
def numbers():
    return [1, 2, 3]

def test_sum(numbers):       # pytest sees the name, calls the fixture
    assert sum(numbers) == 6
```

Matching is **purely by name** — misspell the parameter and you get `fixture not found`.
Fixtures run **fresh for every test** by default (exactly the isolation you want), support
setup/teardown via `yield`, and can **request other fixtures** by the same mechanism, so they
layer. Teardown runs in **reverse order** of setup.

#### `conftest.py`

- **`test_*.py` = the tests.** pytest finds these files and runs every `test_*` function
- **`conftest.py` = the shared toolbox.** pytest loads it but runs nothing in it

Two rules: **you never import `conftest.py`** (pytest loads it automatically, purely because of
the filename), and **its fixtures are available to every test file in that folder and below**.
Fixtures defined inside a `test_*.py` are available only in that file. So the only reason to use
`conftest.py` is _sharing_.

#### Don't duplicate your schema

Tests need the table. Pasting the `CREATE TABLE` into `conftest.py` gives you **two definitions
that can silently drift apart** — add a column to the app and your tests keep building the old
shape, passing against a schema that no longer exists. Extract the DDL into a function taking a
connection, and have both the app and the tests call it.

**Seed data is different** — tests should control their own, so they can assert exact counts and
ids.

#### The import path

`from database import ...` only works if the project root is on **`sys.path`**, the list of
directories Python searches for modules.

| Command            | What gets prepended to `sys.path`                      |
| ------------------ | ------------------------------------------------------ |
| `pytest`           | the directory pytest decides is the test's import root |
| `python -m pytest` | **the current working directory** — always             |

That `-m` behaviour is a general Python rule, not a pytest one. Plain `pytest` walks **up** from
the test file looking for `__init__.py` files to determine the package root — so a `tests/`
folder without one makes pytest insert `tests/` itself, and the project root is never added.

Fixes: `pythonpath = ["."]` under `[tool.pytest.ini_options]` in `pyproject.toml` (recommended —
bare `pytest` then works everywhere), `python -m pytest`, a `tests/__init__.py`, or keeping tests
at the project root.

---

### Appendix: follow-up questions

#### Why split `create_schema` out of `init_db`?

The tests need **one part** of that function's job. `init_db` opens a connection to the real
`DB_PATH`, creates the table, seeds the app's rows, commits and closes — only the table creation
is wanted. The alternative is duplicating the `CREATE TABLE` in the test setup, and duplication
is the real hazard: add a column next month and your tests keep building the _old_ table, passing
confidently against a schema that no longer exists.

The split also describes reality better — "what shape is this table" and "bootstrap the
application's database" are two different responsibilities.

#### Why does `create_schema` take a connection instead of fetching one?

Same principle as `Depends`, applied to a plain function. If it called `get_connection()`
itself, it would be **hardwired to `DB_PATH`** — no way to apply the schema to an in-memory
database. Taking the connection as a parameter inverts that: the function knows _how to build
the table_ and nothing about _where_.

There's a second reason: **transaction ownership**. The connection carries the open transaction,
so passing one in means schema creation and seeding commit together as one unit. A function that
opened and closed its own connection would commit independently — and for `":memory:"` would
_destroy_ the database on close.

The general rule: **a function that acquires its own resources can only ever be used one way. A
function that accepts them can be used every way.**

#### Could `init_db` have used `yield` to share its connection?

The answer turns on **direction**:

```
parameter   → data flows IN   → the caller chooses the database
yield       → data flows OUT  → the caller borrows the database init_db already chose
```

The test's problem isn't "I need access to a connection," it's "I need a _different database_."
A `yield` hands out a connection to `DB_PATH` — exactly the database the test was avoiding.

Three further problems. It would **silently break the app**: a function containing `yield` is a
generator function, so `init_db()` would construct a generator, execute nothing, and the table
would never be created — failing later with `no such table`. `yield` is for **lifecycles**, not
operations; schema creation has no "after" to express. And it would still **conflate two jobs**
in one function.

#### Why not `app.dependency_overrides[get_db] = test_db()`?

Three separate reasons:

1. **pytest forbids calling a fixture directly.** `@pytest.fixture` wraps the function; calling
   it bypasses ordering, teardown and per-test freshness, so pytest blocks it
2. **The dict's values must be callables.** FastAPI _calls_ the replacement on every request.
   Assigning the result means FastAPI tries to call a `sqlite3.Connection`, which isn't callable.
   It wants the recipe, because it bakes one per request
3. **Generators are single-use.** `test_db` contains `yield`, so calling it returns a _generator
   object_ consumable exactly once: request 1 works, request 2 hits `StopIteration`. `get_db`
   works as a dependency precisely _because_ it's a function FastAPI invokes per request,
   producing a fresh generator each time

The wrapper is a **callable that closes over an already-created connection** — a function
FastAPI can call per request, each call making a fresh generator, all yielding the _same_
connection because the closure captured it.

A **closure** is a function defined inside another function, able to read the enclosing
function's variables — which is how the override reaches the fixture's connection without taking
it as a parameter.

(`app.dependency_overrides[get_db] = lambda: test_db` also works, since FastAPI accepts
non-generator dependencies. A named nested function is easier to read, mirrors the real
`get_db`, and leaves a body to extend.)

## My Steps & Learnings (Human Notes)

1. Create virtual environment

```bash
python3 -m venv .venv
# python run module venv <virtual environment name>
```

2. Activate that environment

```bash
source .venv/bin/activate
```

-> prefixes the prompt with `(venv)`

3. Install dependencies (in active `venv`)

```bash
pip install fastapi uvicorn
# verify
pip list
```

4. create `requirements.txt`

```bash
pip freeze > requirements.txt
# includes 3rd party requirements!
```

-> better to handwrite for the direct dependencies

Next time, requirements can be installed via

```bash
pip install -r requirements.txt
```

4. 1. create dev-dependencies `requirements-dev.txt`

**Ruff** is a Python Formatter and Linter tool. Install as dev-dependency and VSCode extension. Then make sure it's referenced in `.vscode/settings.json`.

```bash
ruff check --fix .
#runs the linter on current directory
```

5. run the server

```bash
uvicorn main:app --reload
# run ASGI server
        # where to find the app - module:variable
                # restart automatically on file changes
```

6. Test the server

- http://127.0.0.1:8000/ → the greeting as JSON
- http://127.0.0.1:8000/health → the status object
- http://127.0.0.1:8000/docs → this is the payoff. An interactive Swagger UI, generated entirely from the type hints and route definitions
- http://127.0.0.1:8000/openapi.json → the machine-readable OpenAPI schema the docs page is built from

> FastAPI sets the HTTP header `content-type: application/json` automatically from the returned Python dictionary.

7. defining URL params

> FastAPI uses type hints to parse and validate url parameters. If a value can't be validated it will return a HTTP `422` (unprocessable entity) error.

> type hints `name: type` are completely ignored by Python at runtime. They're metadata and are more meant for type checkers and editors, and in this case FastAPI

8. using Pydantic models

- body validation for `POST` requests using a schema (declaration of what a valid task looks like)
- create a Pydantic model for each request route that expects a body input
- FastAPI will know to parse and validate the body because of the use of Pydantic Model at that path
- using the `/docs` endpoint to test the `POST` requests from the browser!
- dot notation works on pydantic models (objects) but not on Python dictionaries (string notation)

9. `HTTPExceptions`

- FastAPI will convert any raised `HTTPException` to a proper response
- `raise` instead of `return` in order to abort the function early and unwind the call stack (equivalent to `throw` in JS)
- status codes are declared in the decorator (will be picked up by `/docs`)

10. Update and Delete Routes

- `PUT` is a replacement (body requires all fields), `PATCH` is a merge (body fields are optional)
- idempotency means doing something multiple times but leaving the system in the same state as doing it once
- `PUT` should return `200` as it simple changes the state, idempotently
- side note: `POST` is not idempotent, hence some sensible APIs (like payment APIs) will require an "idempotency key" with the request for verification in case of server time outs etc.
- `204 No Content` response mustn't have a body

11. Query parameters (filters)

- query parameters are set in the route function as arguments
- FastAPI will infer that they're query parameters because they're not in the path
- setting default to None so the filter is off when not specified
- FastAPI parses `true`, `1`, `yes`, `on` as `True` and `false`, `0`, `no`, `off` as `False`
- unknown query params are ignored, not errored

12. Project Structure

- split files by responsibility
- modules (`.py` files) and packages (`folders/` with `__init__.py` files) -> a folder becomes a package with an empty `__init__.py` file
- using `tags` in the `APIRouter` of FastAPI groups routes into these categories in `/docs`

13. `Depends`

> FastAPI feature: declare a parameter by the return result of a function

- using FastAPI's dependencies in parameters, makes them appear in the OpenAPI schema (`/docs`)
- order in params is important -> declare defaults after non-defaults!

14. SQL database

> SQL has no type constraints! -> use pydantic models to validate types before anything goes into the database

- boolean values will be 0/1 in SQL and need conversion in the app (that's what an ORM is for)

15. Wiring up the database

We can write a `yield` function that creates the db connection, yields the connection to where ever the function was called (in the API routes) and after the route is done, the yield function continues to close the connection. Otherwise every API route would have to create a connection, use it, and close it again, which may cause write blocks on the db. This way, we have one connection handler (like a middleware) that does the clean up as well. `yield` functions only pause and return where as `return` functions finish the function entirely.
We can then use this `yield` function as a FastAPI dependency when declaring the database in the route.

- sql connection `.execute` returns a sqlite cursor object! (need to use a method to return row/rows)
- don't forget `.commit()` after every WRITE operation!

16. Automated Tests

- FastAPI comes with a test client that mirrors the `httpx` library

```bash
# run tests
pytest --verbose # will pick up every test_*.py file
pytest -k <name> # run only specified test
pytest -s # enable print() statements in stdout
```

- think about splitting up functions in `database.py` to have them run in isolation, so that tests can use them for their own databases than production

- `conftest.py` is the shared toolbox for pytest tests, doesn't need importing. Whatever is defined inside becomes available to all tests nearby.

- a `Fixture` is a named recipe for something a test needs. Can be called by any test as a parameter.

## Recap (AI summary)

A persistent REST API for managing tasks, built in 13 steps. This file summarises the key
concepts, the mistakes worth remembering, and the commands used along the way.

### What was built

```
main.py           app creation and router wiring
models.py         Pydantic schema (Task)
database.py       connection, schema, seed, the get_db dependency, row_to_task
dependencies.py   the HTTP <-> storage bridge (check_task_exists / 404 handling)
routers/
  __init__.py     empty - marks the directory as a package
  tasks.py        five CRUD routes, backed by SQL
  health.py       / and /health
conftest.py       pytest fixtures (in-memory test DB + client with dependency override)
test_api.py       8 isolated tests
tasks.db          SQLite database (gitignored)
```

Endpoints:

| Method   | Path          | Purpose                                            |
| -------- | ------------- | -------------------------------------------------- |
| `GET`    | `/tasks`      | list, with `?done=`, `?search=`, `?limit=` filters |
| `GET`    | `/tasks/{id}` | one task, 404 if absent                            |
| `POST`   | `/tasks`      | create, returns 201                                |
| `PUT`    | `/tasks/{id}` | full replacement, returns 200                      |
| `DELETE` | `/tasks/{id}` | remove, returns 204 with an empty body             |

---

### Core FastAPI concepts

**Type hints are the specification.** A single annotation makes FastAPI parse the value,
validate it, reject bad input with a 422 before your function runs, and document it in
`/docs`. Nothing else in the framework matters as much as this.

**How FastAPI decides where a parameter comes from** — purely from its annotation:

| Annotation                                          | Source                   |
| --------------------------------------------------- | ------------------------ |
| a Pydantic model                                    | request body (JSON)      |
| a scalar whose name matches a `{brace}` in the path | the path                 |
| a scalar whose name is not in the path              | the query string         |
| `Depends(fn)`                                       | the return value of `fn` |

**Pydantic models** declare a schema as annotated class fields. Required vs. optional is
decided by whether a field has a default value. Validation errors return a `detail` array
reporting _every_ problem at once, each with a `loc` path like `["body", "title"]`.

**Status codes are the primary signal**, not the body. Returning `200` with an error body
is a real bug: clients checking `response.ok` proceed happily and monitoring shows 100%
success. Use `raise HTTPException(...)` — `raise` works from anywhere in the call stack,
including a dependency, which `return` could never do.

| Code | Use                                        |
| ---- | ------------------------------------------ |
| 200  | successful GET / PUT                       |
| 201  | successful POST that created a resource    |
| 204  | successful DELETE — body **must** be empty |
| 404  | resource not found                         |
| 422  | validation failure (automatic)             |

**Idempotency** — repeating the call leaves the same state. `GET`, `PUT`, `DELETE` are
idempotent; `POST` is not (five calls create five tasks). This determines whether a client
can safely retry after a timeout.

**`APIRouter`** collects routes in another file; `app.include_router()` attaches them.
`prefix="/tasks"` is prepended to every path inside, so the collection route's path is the
empty string `""` — using `"/"` would produce `/tasks/`, a different URL. `tags=[...]`
groups endpoints in `/docs`.

**Dependency injection** — don't fetch what you need, declare it and let the framework
supply it. The payoff is substitution: routes ask for "a database" and get the real one in
production, an in-memory one in tests, with no change to the route. Dependencies can have
their own parameters and their own sub-dependencies, and FastAPI calls each one **once per
request** and reuses the result — which is why a route and its dependency share the same
connection and therefore the same transaction.

**`yield` dependencies** manage resource lifetimes. The function pauses at `yield`, the
request is handled, then it resumes to clean up. Wrap in `try`/`finally` so the connection
closes even when the endpoint raises — otherwise every 404 leaks a file handle.

---

### Database concepts

**SQLite** is in the standard library: one file, no server, no credentials. Writes are
limited to one at a time, which is when you move to PostgreSQL.

**No boolean type.** SQLite stores `0`/`1`, so rows must be converted back with `bool()` on
the way out, or your JSON contract silently changes from `false` to `0`. That is the entire
job of `row_to_task`.

**Parameterised queries — the most important rule here.**

```python
conn.execute(f"SELECT * FROM tasks WHERE title = '{search}'")     # NEVER
conn.execute("SELECT * FROM tasks WHERE title = ?", (search,))    # ALWAYS
```

The driver sends the statement and the values separately, so a value can never be parsed as
SQL. With an f-string, `?search=' OR 1=1 --` returns every row and `'; DROP TABLE tasks; --`
deletes the table. For dynamic `WHERE` clauses the rule is: the SQL _structure_ comes only
from string literals in your source; every user-supplied _value_ goes through a `?`.

**Other details:** `row_factory = sqlite3.Row` enables `row["title"]` access and `dict(row)`.
`commit()` is mandatory after INSERT/UPDATE/DELETE or the write is discarded on close.
`fetchone()` returns `None` when there is no row, which plugs into an `is None` 404 check.
`INTEGER PRIMARY KEY` auto-assigns ids, and `cursor.lastrowid` reports the one assigned —
atomically, unlike computing `max(id) + 1` yourself.

---

### Testing concepts

**Two separate injection systems that look alike:**

|              | pytest fixtures        | FastAPI `Depends`         |
| ------------ | ---------------------- | ------------------------- |
| From         | pytest                 | FastAPI                   |
| Injects into | test functions         | routes and dependencies   |
| Matched by   | the parameter **name** | the `Depends(...)` marker |

`app.dependency_overrides` is the bridge between them — a dict keyed by the original
dependency function. It is global and must be cleared in teardown, or an override leaks
into later tests.

**`TestClient`** calls the ASGI app in-process: no server, no network, milliseconds per
request. Built on `httpx2` in Starlette 1.7+ (plain `httpx` will not work).

**`conftest.py`** is pytest's auto-loaded toolbox — never imported, discovered by filename,
and its fixtures are available to every test file in that directory and below. `test_*.py`
files hold the tests themselves.

**Fixtures** are named recipes requested by writing the name as a parameter. They run fresh
per test by default, can request other fixtures, and support setup/teardown via `yield`
(teardown runs in reverse order of setup).

**The override must be a callable, not a value.** `dependency_overrides[get_db] = test_db()`
fails three times over: pytest forbids calling fixtures directly; the dict's values are
called per request; and a generator _object_ is single-use, so it would work for exactly one
HTTP call. A small wrapper function that closes over the connection satisfies all three.

**Isolation** means every test starts from a known state. An in-memory database gives that
for free — but each connection to `":memory:"` is a _separate_ database, so the fixture must
hold one connection open for the whole test and the override must not close it.

**A test that cannot fail provides no information.** Two of the first eight were vacuous:

```python
all([])  -> True      # "every task is done" passes on an empty list
[] == [] -> True      # two empty responses compare equal
```

The fix is an emptiness guard before asserting a property of the contents. The general check:
**break the code deliberately and confirm the test goes red.**

---

### Python gotchas hit along the way

| Gotcha                        | Rule                                                                                          |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `import X from y`             | Python is `from y import X` — source first                                                    |
| `new FastAPI()`               | no `new` keyword; a class is simply callable                                                  |
| `{message: "hi"}`             | dict keys are **evaluated** — bare words are variable lookups, strings need quotes            |
| `def root:`                   | parentheses are always required, even when empty                                              |
| `true` / `null`               | Python uses `True` / `False` / `None`, capitalised                                            |
| `task.id` on a dict           | brackets for data containers, dots for objects (Pydantic models)                              |
| `search.lower()` alone        | strings are **immutable** — every string method returns a new value that must be assigned     |
| `tasks = [...]` in a function | assignment creates a _local_ name; mutate with `.append()`/`.remove()` instead                |
| `x is True` vs `== True`      | `is` only for singletons (`None`, `True`, `False`); `==` for values                           |
| `cursor.fetchone()`           | always returns a _row_, even for `COUNT(*)` — index it or name the column with `AS`           |
| `def f(items=[])`             | defaults are evaluated **once** at definition time; use `None` as a sentinel                  |
| `Depends()` in a default      | triggers Ruff `B008`, a false positive — fix with `Annotated[...]`, an allowlist, or `# noqa` |
| `result[:-1]`                 | negative slicing means "all but the last" — why `?limit=-1` silently dropped a task           |
| loop variables                | leak out of the loop in Python, unlike `let` in a JS block                                    |

Plus: `if conditions:` for emptiness (empty collections are falsy), `" AND ".join(...)` called
on the separator, `all(...)` with a generator expression, and generator expressions needing
their own parentheses when they are not the sole argument.

---

### Tooling

**Virtual environments** isolate per-project dependencies. Activation only edits `PATH`, so
calling `.venv/bin/pip` by path works regardless — useful when each shell is fresh.

**Dependency tiers:** `requirements.txt` for runtime, `requirements-dev.txt` for tooling
(starting with `-r requirements.txt` to include both in one install). Pin with `==` while
learning so nothing shifts underneath you.

**Ruff** is formatter and linter in one. Important distinction: format-on-save runs the
_formatter_ (whitespace, quotes, wrapping) while import sorting is a _lint fix_ requiring
`editor.codeActionsOnSave`. "Lint passed" is only as strong as the rules enabled — `B018`
would have caught the discarded `search.lower()`, and it is off by default.

**Import path.** `from database import ...` only works if the project root is on `sys.path`.
Moving tests into a subfolder broke it, because pytest inserts the test's own directory when
there is no `__init__.py`. Fixes: `pythonpath = ["."]` in `pyproject.toml`, `python -m pytest`
(which always adds the CWD), an `__init__.py`, or keeping tests at the root.

### Commands

```bash
python3 -m venv .venv                      # create the virtual environment
source .venv/bin/activate                  # activate it (per shell)
pip install -r requirements-dev.txt        # install runtime + dev dependencies

uvicorn main:app --reload                  # run the dev server on :8000
                                           # main:app = module:variable

ruff format .                              # apply formatting
ruff check . --fix                         # lint and auto-fix (incl. import sorting)
pytest -v                                  # run the suite, one line per test

sqlite3 tasks.db -header "SELECT * FROM tasks;"   # inspect the database
sqlite3 tasks.db ".schema"                        # show CREATE statements
```

Useful URLs while the server runs: `/docs` (interactive Swagger UI), `/redoc`,
`/openapi.json` (the generated schema).
