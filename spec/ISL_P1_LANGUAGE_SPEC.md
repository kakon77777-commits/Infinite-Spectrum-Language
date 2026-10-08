# ISL P1 — Minimal Language Specification (v0.1)

Status: **public experimental grammar**, reference implementation in Python 3.10+.  
Authoring source: UTF-8 Markdown.  
Conceptual ancestry: the 2026-03-10 five-layer infinite-spectrum language proposal.

## 1. Position

ISL P1 implements explicit numerical spectrum operations, not natural-language semantic encoding or reasoning. A spectrum is a record with a finite set of manually declared named axes. The logical namespace can be extended across versions; any individual program is finite.

A declared axis is not assumed to be a discovered semantic atom. Its empirical interpretation must be justified independently of ISL. Values in `[0,1]` are bounded numerical annotations, not inherently probabilities, model confidences, linguistic ambiguities, or logical truth degrees.

## 2. Lexical grammar

- UTF-8 source; double-quoted JSON-compatible string literals (Unicode permitted).
- ASCII case-sensitive identifiers: `[A-Za-z_][A-Za-z0-9_]*`.
- Nonnegative decimal literals in the range `[0,1]` for operations and intervals. No exponent notation in v0.1.
- `#` line comments, terminated by newline or end of file.
- Whitespace has no semantic effect outside strings.
- Reserved statement words: `isl`, `axis`, `record`, `let`, `print`.
- Built-in expression names: `intersect`, `union`, `blend`, `cosine`, `filter`.

## 3. Concrete grammar

The following is descriptive EBNF. Terminals appear in quotes; `ID`, `STRING`, `NUMBER` are lexical categories.

```ebnf
program         = "isl", "0.1", ";", { statement } ;
statement       = axis_decl | record_decl | binding | print_stmt ;
axis_decl       = "axis", ID, ";" ;
record_decl     = "record", ID, "{", { record_field }, "}" ;
record_field    = ("text" | "context" | "provenance"), STRING, ";"
                | ID, "=", "[", NUMBER, ",", NUMBER, "]", ";" ;
binding         = "let", ID, "=", expression, ";" ;
print_stmt      = "print", ID, ";" ;
axis_ref        = ID, ".", ID ;
expression      = "intersect", "(", axis_ref, ",", axis_ref, ")"
                | "union", "(", axis_ref, ",", axis_ref, ")"
                | "blend", "(", axis_ref, ",", axis_ref, ",", NUMBER, ")"
                | "cosine", "(", ID, ",", ID, ")"
                | "filter", "(", ID, ",", "lower", ">=", NUMBER, ")" ;
```

## 4. Types and static/dynamic checks

- All `axis` declarations must appear before any `record`, `let` or `print`.
- Each record supplies exactly all declared axes, one value per axis. At least one axis is required.
- `record` metadata `text`, `context`, `provenance` is mandatory and nonblank.
- Duplicate declared axes, record names, binding names, metadata fields or record axes are rejected.
- Record and `let` names cannot collide; declared axis names cannot shadow metadata field names. Referenced records and variables must already exist.
- Each interval has finite bounds satisfying $$0\le l\le u\le1$$. Invalid intervals are errors.
- `intersect`, `union`, `blend` accept two axis references using the **same named axis**; no implicit cross-axis arithmetic.
- `cosine` accepts two complete records with the same axes; zero midpoint norm is rejected. Scores are heuristic numerical rankings.
- `filter` accepts a declared axis and a lower bound, and returns matching record names in declaration order.
- `print` accepts a prior `let` binding. There is no general expression nesting, mutation or looping.

## 5. Numerical semantics

For intervals $$I=[l_I,u_I],\ J=[l_J,u_J]$$, intersection is

$$
I\cap J=\begin{cases}
[\max(l_I,l_J),\min(u_I,u_J)] & \max(l_I,l_J)\le\min(u_I,u_J)\\
\varnothing & \text{otherwise}.
\end{cases}
$$

Union is the **exact set union** (a list of one merged interval if overlapping/touching, or two disjoint intervals). No convex hull is implied.

Numeric blend at $$0\le\alpha\le1$$ is

$$
B_\alpha(I,J)=[\alpha l_I+(1-\alpha)l_J,\ \alpha u_I+(1-\alpha)u_J].
$$

The P1 reference evaluates with ordinary finite binary floating-point numbers; the JSON representation is not a machine-independent exact-decimal numerical contract. Cross-platform bitwise determinism remains outside the P1 guarantee.

Cosine similarity uses midpoint vectors over matching alphabetically ordered axis names. It is solely a candidate-ranking heuristic. A high similarity score is neither logical entailment nor semantic equivalence.

## 6. Output and errors

A successful `run` returns a JSON object with exact top-level keys `profile`, `axes`, `records`, `outputs`. Output events preserve explicit `print` order. The profile is `isl-language/0.1`.

Output value types:

- `interval-or-empty`: `{"lower": number, "upper": number}` or `null`.
- `interval-set`: one or two interval objects in ascending order.
- `interval`: one interval object.
- `heuristic-similarity`: a JSON number.
- `record-selection`: an ordered array of record IDs.

The CLI prints a diagnostic and returns nonzero for malformed or unsupported syntax, duplicate identifiers, undeclared or incompatible axes, invalid bounds, and undefined objects; it does not run arbitrary code from ISL input. Future versions may introduce additional value and error kinds behind explicit version boundaries.

## 7. Security, privacy and interoperability

The interpreter does not import scripts from ISL source, evaluate arbitrary code, call model providers, or access a network. No hidden data or model state is used to generate examples. External text, labels and numeric annotations are user-authored input, not evidence of semantic truth.

The compatibility boundary is **ISL P1 only**; no relation to a non-public system is assumed, and the P1 grammar is not claimed to be a finalized cross-implementation standard. A second independent implementation with normative cross-platform vectors is a future acceptance gate.
